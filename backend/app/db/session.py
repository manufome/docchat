"""Async SQLAlchemy session management.

SQLite concurrency strategy
---------------------------
SQLite only allows one writer at a time. We use a **QueuePool with a single
connection** so that all database operations are serialized through one
connection. This avoids "database is locked" errors because there is never
more than one write attempt at any moment.

The pool's ``pool_timeout`` is set to 30 seconds — if a second request
arrives while the first holds the connection, it waits up to 30 s for the
connection to be returned rather than failing immediately.

WAL mode is applied directly to the database file at module import time
(for persistence) and via a pool connect event on each new connection, so
reads never block writes and vice versa.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

# ── Ensure WAL mode is active on the database file ──────────────────────
# Applied directly at import time (persists in the file) AND via the
# pool connect event so every new connection also has it.
import sqlalchemy as sa

_db_url = sa.make_url(settings.database_url)
_db_path = _db_url.database
if _db_path and os.path.isfile(_db_path):
    import sqlite3

    _conn = sqlite3.connect(_db_path)
    _conn.execute("PRAGMA journal_mode=wal")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.close()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=1,
    max_overflow=0,
    pool_timeout=30,
    connect_args={
        "check_same_thread": False,
        "timeout": 5,
    },
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and a busy timeout on each new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=wal")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_async_session():
    """Context manager for async session (for testing/scripts)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
