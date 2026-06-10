"""ORM models."""

import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # SQLAlchemy 的声明式基类，所有 ORM 表都要继承它
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    # 额外加一个显示名称字段
    display_name: Mapped[str | None] = mapped_column(String(length=100), nullable=True)


class AIConversationMessage(Base):
    __tablename__ = "ai_conversation_messages"
    __table_args__ = (
        CheckConstraint("sender IN ('user', 'ai')", name="ck_ai_conversation_sender"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    sender: Mapped[str] = mapped_column(String(length=20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_summarized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AIUserMemory(Base):
    __tablename__ = "ai_user_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    memory: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conversation_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
