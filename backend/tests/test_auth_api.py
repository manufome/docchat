"""Integration tests for auth API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Sanity check: health endpoint works."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success(client):
    """RED: Register with valid data returns 201 and JWT."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "newuser@test.com", "password": "securePass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@test.com"
    assert "id" in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """TRIANGULATE: Duplicate email returns 409."""
    await client.post(
        "/api/auth/register",
        json={"email": "dupe@test.com", "password": "securePass123"},
    )
    response = await client.post(
        "/api/auth/register",
        json={"email": "dupe@test.com", "password": "anotherPass456"},
    )
    assert response.status_code == 409
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """TRIANGULATE: Invalid email returns 422."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "securePass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    """TRIANGULATE: Short password returns 422."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "password": "1234567"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    """RED: Login with valid credentials returns 200 and JWT."""
    await client.post(
        "/api/auth/register",
        json={"email": "logintest@test.com", "password": "securePass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "logintest@test.com", "password": "securePass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "logintest@test.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """TRIANGULATE: Wrong password returns 401."""
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpw@test.com", "password": "correctPass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpw@test.com", "password": "wrongPassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """TRIANGULATE: Non-existent user returns 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "password": "somePassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    """RED: GET /me with valid token returns user profile."""
    register_resp = await client.post(
        "/api/auth/register",
        json={"email": "meuser@test.com", "password": "securePass123"},
    )
    token = register_resp.json()["access_token"]

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "meuser@test.com"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    """TRIANGULATE: GET /me without token returns 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
