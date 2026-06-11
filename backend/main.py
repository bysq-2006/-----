"""应用入口，只负责把路由挂到 FastAPI 上。"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import UserCreate, UserRead, UserUpdate, auth_backend, current_user, fastapi_users
from backend.chat import router as chat_router
from backend.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时先建表
    await create_db_and_tables()
    yield


app = FastAPI(title="FastAPI Users Minimal Example", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(chat_router, prefix="/v1", tags=["openai-compatible"])


@app.get("/")
async def root():
    return {"message": "FastAPI Users minimal example"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/me")
async def me(user=Depends(current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }

# cd d:\bysq\景区数字人
# uvicorn backend.main:app --reload

# pip install -r backend\requirements.txt
# uvicorn backend.main:app --reload --log-level debug --access-log