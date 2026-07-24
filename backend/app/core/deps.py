"""FastAPI dependency injection: settings, database session, current user."""

from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import async_session_factory
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_settings():
    """Return the application settings singleton."""
    return settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_async_session_factory():
    """Return the async session factory for explicit session management.

    Used by endpoints that need to create and close sessions manually
    (e.g. the SSE chat stream) so the pool connection is never held
    during long-running operations.
    """
    return async_session_factory


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token.

    Uses ``Depends(get_db)`` so the session is held for the request's
    full lifecycle. For long-running responses (SSE streaming), use
    ``get_current_user_light`` instead to avoid holding a pool connection.
    """
    return await _query_user(credentials, db)


async def get_current_user_light(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session_factory=Depends(get_async_session_factory),
) -> User:
    """Extract the current user with a brief, immediately-released session.

    Uses the session factory directly instead of ``Depends(get_db)`` so
    the pool connection is acquired and released within this function,
    never held for the entire request lifecycle.
    """
    async with session_factory() as db:
        return await _query_user(credentials, db)


async def _query_user(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: AsyncSession,
) -> User:
    """Shared user lookup logic for both ``get_current_user`` variants."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = verify_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
