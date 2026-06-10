"""OpenAI-compatible chat route."""

import os
import json
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import current_user
from backend.chat.context import (
    build_messages_with_backend_context,
    save_turn_and_summarize_if_needed,
)
from backend.database import User, get_async_session


load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

router = APIRouter()


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]] = Field(min_length=1)
    stream: bool = False

    model_config = ConfigDict(extra="allow")


def deepseek_target() -> tuple[str, dict[str, str]]:
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DEEPSEEK_API_KEY is not configured",
        )

    return f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions", {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }


def message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip()
    return str(content).strip()


def current_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        content = message_text(message.get("content", ""))
        if message.get("role") == "user" and content:
            return content

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="messages must contain a non-empty user message",
    )


def assistant_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices") or []
    message = choices[0].get("message") if choices else {}
    return message_text((message or {}).get("content", ""))


def stream_text(raw_body: bytes) -> str:
    pieces: list[str] = []
    for line in raw_body.decode("utf-8", errors="ignore").splitlines():
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data in {"", "[DONE]"}:
            continue

        try:
            delta = (json.loads(data).get("choices") or [{}])[0].get("delta") or {}
        except json.JSONDecodeError:
            continue

        content = delta.get("content")
        if content:
            pieces.append(str(content))
    return "".join(pieces).strip()


async def stream_deepseek_and_persist(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    session: AsyncSession,
    user: User,
    user_message: str,
):
    raw_body = bytearray()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                raw_body.extend(chunk)
                yield chunk

    await save_turn_and_summarize_if_needed(
        session,
        user,
        user_message,
        stream_text(bytes(raw_body)),
        url,
        headers,
        payload["model"],
    )


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    current_message = current_user_message(request.messages)

    payload = request.model_dump(exclude_none=True)
    payload["messages"] = await build_messages_with_backend_context(session, user, current_message)
    payload["model"] = payload.get("model") or DEEPSEEK_MODEL

    url, headers = deepseek_target()

    if request.stream:
        return StreamingResponse(
            stream_deepseek_and_persist(
                url,
                headers,
                payload,
                session,
                user,
                current_message,
            ),
            media_type="text/event-stream",
        )

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM API error: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM request failed: {exc}",
        ) from exc

    response_json = response.json()
    await save_turn_and_summarize_if_needed(
        session,
        user,
        current_message,
        assistant_text(response_json),
        url,
        headers,
        payload["model"],
    )

    return response_json
