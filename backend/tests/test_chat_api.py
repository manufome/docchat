"""Integration tests for the SSE chat endpoint.

RED→GREEN→REFACTOR: POST /api/chat/stream.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import create_access_token


async def _register_user(client, email: str, password: str = "SecurePass123") -> tuple[str, str]:
    """Register a user and return (token, user_id)."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]["id"]


class TestChatStream:
    """RED→GREEN→REFACTOR: POST /api/chat/stream SSE streaming."""

    @pytest.mark.asyncio
    async def test_stream_requires_auth(self, client):
        """GIVEN no auth WHEN stream THEN 401."""
        response = await client.post(
            "/api/chat/stream",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stream_with_existing_conversation(self, client):
        """GIVEN valid inputs WHEN stream THEN SSE events received."""
        token, user_id = await _register_user(client, "chat-exist@test.com")

        # Set up API key
        await client.put(
            "/api/users/me/api-key",
            json={"openai_api_key": "sk-real-key-for-testing"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Create a conversation
        conv_resp = await client.post(
            "/api/conversations",
            json={"title": "Test Chat"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conv_id = conv_resp.json()["id"]

        # Mock the chat_service.process_chat_message to yield events
        async def mock_process(*args, **kwargs):
            yield {"type": "token", "content": "Hola "}
            yield {"type": "token", "content": "mundo"}
            yield {"type": "citation", "citation": {"index": 1, "document_name": "doc.pdf", "page": 1, "text_preview": "test"}}
            yield {"type": "done", "message_id": "msg-1"}

        with (
            patch("app.api.chat.decrypt_api_key") as mock_decrypt,
            patch("app.api.chat.process_chat_message", side_effect=mock_process),
        ):
            mock_decrypt.return_value = "sk-test-key"

            response = await client.post(
                "/api/chat/stream",
                json={"conversation_id": conv_id, "message": "¿Cómo estás?"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            headers = {k.lower(): v for k, v in response.headers.items()}
            assert headers["content-type"] == "text/event-stream; charset=utf-8"
            assert headers["cache-control"] == "no-cache"
            assert headers["x-accel-buffering"] == "no"

            # Parse SSE events from the response
            body = response.text
            events = []
            for line in body.strip().split("\n"):
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

            assert len(events) == 4
            assert events[0]["type"] == "token"
            assert events[1]["type"] == "token"
            assert events[2]["type"] == "citation"
            assert events[3]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_creates_new_conversation(self, client):
        """GIVEN no conversation_id WHEN stream THEN new conversation created."""
        token, user_id = await _register_user(client, "chat-new@test.com")

        # Set up API key
        await client.put(
            "/api/users/me/api-key",
            json={"openai_api_key": "sk-real-key-for-testing"},
            headers={"Authorization": f"Bearer {token}"},
        )

        async def mock_process(*args, **kwargs):
            yield {"type": "token", "content": "Respuesta"}
            yield {"type": "done", "message_id": "msg-1"}

        with (
            patch("app.api.chat.decrypt_api_key") as mock_decrypt,
            patch("app.api.chat.process_chat_message", side_effect=mock_process),
        ):
            mock_decrypt.return_value = "sk-test-key"

            response = await client.post(
                "/api/chat/stream",
                json={"message": "Hola"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            body = response.text
            events = [json.loads(line[6:]) for line in body.strip().split("\n") if line.startswith("data: ")]
            assert len(events) == 2

    @pytest.mark.asyncio
    async def test_stream_no_api_key(self, client):
        """GIVEN user without API key WHEN stream THEN error event."""
        token, user_id = await _register_user(client, "chat-nokey@test.com")

        with (
            patch("app.api.chat.decrypt_api_key", side_effect=Exception("No key")),
        ):
            response = await client.post(
                "/api/chat/stream",
                json={"message": "Hola"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            body = response.text
            events = [json.loads(line[6:]) for line in body.strip().split("\n") if line.startswith("data: ")]
            assert events[0]["type"] == "error"

    @pytest.mark.asyncio
    async def test_stream_error_handling(self, client):
        """GIVEN process_chat_message raises BEFORE streaming WHEN stream THEN error event."""
        token, user_id = await _register_user(client, "chat-error@test.com")

        with (
            patch("app.api.chat.decrypt_api_key") as mock_decrypt,
            patch("app.api.chat.process_chat_message", side_effect=Exception("Algo salió mal")),
        ):
            mock_decrypt.return_value = "sk-test-key"

            response = await client.post(
                "/api/chat/stream",
                json={"message": "Hola"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            body = response.text
            events = [json.loads(line[6:]) for line in body.strip().split("\n") if line.startswith("data: ")]
            assert events[0]["type"] == "error"
