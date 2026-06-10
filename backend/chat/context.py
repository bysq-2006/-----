"""Backend-managed chat context and summary persistence."""

from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AIConversationMessage, AIUserMemory, User


RECENT_MESSAGE_LIMIT = 10
SUMMARY_TRIGGER_COUNT = 40
SUMMARY_BATCH_COUNT = 30
SUMMARY_SYSTEM_PROMPT = (
    "你负责把用户和景区数字人 AI 的历史对话压缩成长期可用的上下文摘要。"
    "请保留用户明确表达的需求、偏好、已确认信息、未完成事项和 AI 已给出的关键建议。"
    "不要加入新事实，输出一段简洁中文摘要。"
)


async def get_user_memory(
    session: AsyncSession,
    user_id: Any,
) -> AIUserMemory | None:
    result = await session.execute(
        select(AIUserMemory).where(AIUserMemory.user_id == user_id)
    )
    return result.scalar_one_or_none()


def memory_context_messages(memory: AIUserMemory | None) -> list[dict[str, str]]:
    if not memory:
        return []

    messages = []
    if memory.memory:
        messages.append({"role": "system", "content": f"关于当前用户的长期记忆：{memory.memory}"})
    if memory.conversation_summary:
        messages.append(
            {
                "role": "system",
                "content": f"当前用户较早对话的压缩摘要：{memory.conversation_summary}",
            }
        )
    return messages


def openai_message(item: AIConversationMessage) -> dict[str, str]:
    return {
        "role": "assistant" if item.sender == "ai" else "user",
        "content": item.content,
    }


async def build_messages_with_backend_context(
    session: AsyncSession,
    user: User,
    current_message: str,
) -> list[dict[str, str]]:
    memory = await get_user_memory(session, user.id)

    result = await session.execute(
        select(AIConversationMessage)
        .where(
            AIConversationMessage.user_id == user.id,
            AIConversationMessage.is_summarized.is_(False),
        )
        .order_by(AIConversationMessage.created_at.desc(), AIConversationMessage.id.desc())
        .limit(RECENT_MESSAGE_LIMIT)
    )
    recent_messages = list(reversed(result.scalars().all()))

    messages = memory_context_messages(memory)
    messages.extend(openai_message(item) for item in recent_messages)
    messages.append({"role": "user", "content": current_message})
    return messages


async def save_turn_and_summarize_if_needed(
    session: AsyncSession,
    user: User,
    user_message: str,
    assistant_message: str,
    url: str,
    headers: dict[str, str],
    model: str,
) -> None:
    if not assistant_message:
        return

    session.add_all(
        [
            AIConversationMessage(user_id=user.id, sender="user", content=user_message),
            AIConversationMessage(user_id=user.id, sender="ai", content=assistant_message),
        ]
    )
    await session.commit()

    await summarize_old_messages_if_needed(session, user.id, url, headers, model)


async def summarize_old_messages_if_needed(
    session: AsyncSession,
    user_id: Any,
    url: str,
    headers: dict[str, str],
    model: str,
) -> None:
    count_result = await session.execute(
        select(func.count())
        .select_from(AIConversationMessage)
        .where(
            AIConversationMessage.user_id == user_id,
            AIConversationMessage.is_summarized.is_(False),
        )
    )
    unsummarized_count = count_result.scalar_one()
    if unsummarized_count <= SUMMARY_TRIGGER_COUNT:
        return

    batch_result = await session.execute(
        select(AIConversationMessage)
        .where(
            AIConversationMessage.user_id == user_id,
            AIConversationMessage.is_summarized.is_(False),
        )
        .order_by(AIConversationMessage.created_at.asc(), AIConversationMessage.id.asc())
        .limit(SUMMARY_BATCH_COUNT)
    )
    batch = batch_result.scalars().all()
    if not batch:
        return

    formatted_dialogue = "\n".join(
        f"{'用户' if item.sender == 'user' else 'AI'}：{item.content}"
        for item in batch
    )
    memory = await get_user_memory(session, user_id)
    summary_payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": SUMMARY_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"已有历史摘要：{memory.conversation_summary if memory else '暂无'}\n\n"
                    f"需要合并进摘要的对话：\n{formatted_dialogue}"
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=summary_payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"Summarize conversation failed: {exc}")
        return

    choices = response.json().get("choices") or []
    message = choices[0].get("message") if choices else {}
    new_summary = ((message or {}).get("content") or "").strip()
    if not new_summary:
        return

    if memory is None:
        session.add(AIUserMemory(user_id=user_id, memory="", conversation_summary=new_summary))
    else:
        memory.conversation_summary = new_summary
    for item in batch:
        item.is_summarized = True
    await session.commit()
