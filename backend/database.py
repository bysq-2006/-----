"""数据库和用户表相关代码。"""

from collections.abc import AsyncGenerator

from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = "sqlite+aiosqlite:///./app.db"


class Base(DeclarativeBase):
    # SQLAlchemy 的声明式基类，所有 ORM 表都要继承它
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    # 额外加一个显示名称字段
    display_name: Mapped[str | None] = mapped_column(String(length=100), nullable=True)


# 数据库引擎，负责和数据库建立连接通道
engine = create_async_engine(DATABASE_URL)

# 会话工厂，用来创建每次请求需要的 AsyncSession
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables() -> None:
    # 启动时创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user_db() -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    # 为 FastAPI Users 提供“用户数据库操作对象”
    async with async_session_maker() as session:
        yield SQLAlchemyUserDatabase(session, User)
