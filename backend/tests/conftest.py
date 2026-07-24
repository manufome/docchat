"""Global test configuration and fixtures."""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variables before any app imports
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-testing-purposes-only"
)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

# Import ALL models so they register on Base.metadata
from app.models import User, Document, Conversation, Message  # noqa: E402, F401
from app.db.base import Base  # noqa: E402


@pytest.fixture
async def async_session():
    """Provide a fresh async session with clean tables per test."""
    from app.core.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client():
    """Provide an async test client with file-based database.

    SQLite in-memory databases are per-connection, so we use a file-based
    database to ensure the app's get_db sessions share the same data.
    """
    from app.core.deps import get_async_session_factory, get_db
    from app.main import app

    # Use a temp file for the test database
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db_path = tmp_db.name
    tmp_db.close()

    db_url = f"sqlite+aiosqlite:///{tmp_db_path}"

    # Create the test engine and tables (models are already registered on Base)
    test_engine = create_async_engine(db_url, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a session factory bound to this engine
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Override database dependencies in the app
    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async def override_get_session_factory():
        return test_session_factory

    app.dependency_overrides[get_async_session_factory] = override_get_session_factory

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    app.dependency_overrides.clear()
    await test_engine.dispose()
    os.unlink(tmp_db_path)
