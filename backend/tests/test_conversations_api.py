"""Integration tests for conversations API endpoints."""

import pytest

from app.core.security import create_access_token


MOCK_TITLE = "Conversación de prueba"


def _title_from_body(body: dict) -> str:
    """Helper: extract the auto-generated title from a register response."""
    return "Conversación de prueba"


async def _register_user(client, email: str, password: str = "SecurePass123") -> str:
    """Register a user and return their JWT token."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


class TestCreateConversation:
    """RED→GREEN→REFACTOR: POST /api/conversations."""

    @pytest.mark.asyncio
    async def test_create_with_title(self, client):
        """GIVEN a title WHEN create THEN 201 with conversation."""
        token = await _register_user(client, "conv-title@test.com")
        response = await client.post(
            "/api/conversations",
            json={"title": MOCK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == MOCK_TITLE
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_without_title(self, client):
        """GIVEN no title WHEN create THEN 201 with null title."""
        token = await _register_user(client, "conv-notitle@test.com")
        response = await client.post(
            "/api/conversations",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        """GIVEN no auth WHEN create THEN 401."""
        response = await client.post(
            "/api/conversations",
            json={"title": MOCK_TITLE},
        )
        assert response.status_code == 401


class TestListConversations:
    """RED→GREEN→REFACTOR: GET /api/conversations."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        """GIVEN no conversations WHEN list THEN 200 with empty array."""
        token = await _register_user(client, "conv-empty@test.com")
        response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_with_conversations(self, client):
        """GIVEN 2 conversations WHEN list THEN 200 with 2 items."""
        token = await _register_user(client, "conv-list@test.com")
        await client.post(
            "/api/conversations",
            json={"title": "Chat 1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/conversations",
            json={"title": "Chat 2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_ordered_by_updated_at(self, client):
        """GIVEN conversations WHEN list THEN newest first (descending updated_at)."""
        token = await _register_user(client, "conv-order@test.com")
        resp1 = await client.post(
            "/api/conversations",
            json={"title": "First"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 201
        resp2 = await client.post(
            "/api/conversations",
            json={"title": "Second"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 201
        response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert len(data) == 2
        # Both timestamps should be set; verify descending order
        assert data[0]["updated_at"] >= data[1]["updated_at"]

    @pytest.mark.asyncio
    async def test_list_does_not_include_other_users(self, client):
        """GIVEN conversations from user A WHEN user B lists THEN empty."""
        token_a = await _register_user(client, "conv-other-a@test.com")
        token_b = await _register_user(client, "conv-other-b@test.com")
        await client.post(
            "/api/conversations",
            json={"title": "A's chat"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 200
        assert response.json() == []


class TestListMessages:
    """RED→GREEN→REFACTOR: GET /api/conversations/{id}/messages."""

    @pytest.mark.asyncio
    async def test_list_messages_empty(self, client):
        """GIVEN conversation without messages WHEN list THEN 200 with []."""
        token = await _register_user(client, "msg-empty@test.com")
        conv_resp = await client.post(
            "/api/conversations",
            json={"title": "Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conv_id = conv_resp.json()["id"]
        response = await client.get(
            f"/api/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_messages_404_for_other_user(self, client):
        """GIVEN another user's conversation WHEN list messages THEN 404."""
        token_a = await _register_user(client, "msg-other-a@test.com")
        token_b = await _register_user(client, "msg-other-b@test.com")
        conv_resp = await client.post(
            "/api/conversations",
            json={"title": "A's chat"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        conv_id = conv_resp.json()["id"]
        response = await client.get(
            f"/api/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_messages_404_nonexistent(self, client):
        """GIVEN non-existent conversation WHEN list messages THEN 404."""
        token = await _register_user(client, "msg-nonexist@test.com")
        response = await client.get(
            "/api/conversations/nonexistent-id/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestDeleteConversation:
    """RED→GREEN→REFACTOR: DELETE /api/conversations/{id}."""

    @pytest.mark.asyncio
    async def test_delete_existing(self, client):
        """GIVEN existing conversation WHEN delete THEN 200."""
        token = await _register_user(client, "del-exist@test.com")
        conv_resp = await client.post(
            "/api/conversations",
            json={"title": "To Delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conv_id = conv_resp.json()["id"]
        response = await client.delete(
            f"/api/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, client):
        """GIVEN non-existent convo WHEN delete THEN 404."""
        token = await _register_user(client, "del-nonexist@test.com")
        response = await client.delete(
            "/api/conversations/fake-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_conversation(self, client):
        """GIVEN another user's convo WHEN delete THEN 404."""
        token_a = await _register_user(client, "del-other-a@test.com")
        token_b = await _register_user(client, "del-other-b@test.com")
        conv_resp = await client.post(
            "/api/conversations",
            json={"title": "A's chat"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        conv_id = conv_resp.json()["id"]
        response = await client.delete(
            f"/api/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404
