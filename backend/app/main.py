"""DocChat FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create data dir and tables on startup."""
    # Ensure data directory exists (for SQLite, Chroma, uploads)
    import os

    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_path, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.auth import router as auth_router  # noqa: E402
from app.api.users import router as users_router  # noqa: E402
from app.api.documents import router as documents_router  # noqa: E402
from app.api.conversations import router as conversations_router  # noqa: E402
from app.api.chat import router as chat_router  # noqa: E402

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(conversations_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}
