"""Tests for FastAPI dependency injection."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import get_settings, get_current_user
from app.core.security import create_access_token
from app.models.user import User


def test_get_settings_returns_settings():
    """RED: get_settings returns the Settings singleton."""
    s = get_settings()
    assert s.app_name == "DocChat"
    assert s.secret_key == "test-secret-key-for-testing-purposes-only"


@pytest.mark.asyncio
async def test_get_current_user_valid_token(async_session):
    """RED: Valid JWT returns the corresponding user."""
    user = User(email="jwtuser@test.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    token = create_access_token({"sub": user.id})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = await get_current_user(credentials=creds, db=async_session)
    assert result.id == user.id
    assert result.email == "jwtuser@test.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(async_session):
    """TRIANGULATE: Invalid token raises 401."""
    creds = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid-token"
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=creds, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(async_session):
    """TRIANGULATE: Valid token but user deleted raises 401."""
    token = create_access_token({"sub": "nonexistent-user-id"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=creds, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_credentials(async_session):
    """TRIANGULATE: Missing credentials raises 401."""
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=None, db=async_session)
    assert exc.value.status_code == 401
