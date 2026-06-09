"""FastAPI Users 的认证和用户管理相关代码。"""

import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from backend.database import User, get_user_db


SECRET = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"


class UserRead(schemas.BaseUser[uuid.UUID]):
    # 返回给前端看的用户字段
    display_name: str | None = None


class UserCreate(schemas.BaseUserCreate):
    # 注册时前端要提交的字段
    display_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    # 更新用户时允许修改的字段
    display_name: str | None = None


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        # 注册成功后的回调
        print(f"User {user.id} has registered")


async def get_user_manager(user_db=Depends(get_user_db)):
    # 把 UserManager 作为依赖提供给 FastAPI Users
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    # JWT token 的生成和校验规则
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# 用于保护接口：只有登录且 active 的用户才能进来
current_user = fastapi_users.current_user(active=True)
