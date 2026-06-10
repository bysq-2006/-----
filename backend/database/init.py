"""Database initialization and lightweight SQLite schema upgrades."""

from sqlalchemy import text

from backend.database.models import Base
from backend.database.session import engine


async def create_db_and_tables() -> None:
    # 启动时创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_existing_columns)


def _ensure_existing_columns(sync_conn) -> None:
    # create_all 不会修改已有表；这里补齐开发期 SQLite 里已存在表的新增字段。
    _add_column_if_missing(
        sync_conn,
        "ai_conversation_messages",
        "is_summarized",
        "BOOLEAN NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(
        sync_conn,
        "ai_user_memories",
        "conversation_summary",
        "TEXT NOT NULL DEFAULT ''",
    )
    _execute(
        sync_conn,
        "CREATE INDEX IF NOT EXISTS ix_ai_conversation_messages_user_unsummarized "
        "ON ai_conversation_messages (user_id, is_summarized)",
    )
    _execute(
        sync_conn,
        "CREATE INDEX IF NOT EXISTS ix_ai_user_memories_user_id "
        "ON ai_user_memories (user_id)",
    )


def _add_column_if_missing(sync_conn, table: str, column: str, column_type: str) -> None:
    columns = {row[1] for row in sync_conn.execute(text(f"PRAGMA table_info({table})"))}
    if columns and column not in columns:
        _execute(sync_conn, f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def _execute(sync_conn, sql: str) -> None:
    sync_conn.execute(text(sql))
