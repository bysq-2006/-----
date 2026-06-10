"""Database engine and session dependencies."""

from collections.abc import AsyncGenerator

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.models import User


DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# 数据库引擎，负责和数据库建立连接通道
engine = create_async_engine(DATABASE_URL)

# 会话工厂，用来创建每次请求需要的 AsyncSession
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_user_db() -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    # 为 FastAPI Users 提供“用户数据库操作对象”
    async with async_session_maker() as session:
        yield SQLAlchemyUserDatabase(session, User)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
