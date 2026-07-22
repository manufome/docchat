"""Integration tests for user profile API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_set_api_key_success(client):
    """RED: Authenticated user can set API key."""
    # Register a user
    register_resp = await client.post(
        "/api/auth/register",
        json={"email": "apikey@test.com", "password": "securePass123"},
    )
    token = register_resp.json()["access_token"]

    # Set API key
    response = await client.put(
        "/api/users/me/api-key",
        json={"openai_api_key": "sk-test-key-12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_set_api_key_unauthenticated(client):
    """TRIANGULATE: Cannot set API key without auth."""
    response = await client.put(
        "/api/users/me/api-key",
        json={"openai_api_key": "sk-test-key-12345"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_set_api_key_empty(client):
    """TRIANGULATE: Empty API key is rejected."""
    register_resp = await client.post(
        "/api/auth/register",
        json={"email": "emptykey@test.com", "password": "securePass123"},
    )
    token = register_resp.json()["access_token"]

    response = await client.put(
        "/api/users/me/api-key",
        json={"openai_api_key": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
