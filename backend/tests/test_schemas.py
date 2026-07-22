"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import AuthRegister, AuthLogin, TokenResponse, UserResponse
from app.schemas.user import ApiKeyRequest, ApiKeyResponse
from app.schemas.document import DocumentResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
)
from app.schemas.chat import ChatRequest, StreamEvent


class TestAuthSchemas:
    def test_valid_registration(self):
        """RED: Valid registration data passes validation."""
        data = AuthRegister(email="user@example.com", password="securePass123")
        assert data.email == "user@example.com"
        assert data.password == "securePass123"

    def test_invalid_email_format(self):
        """TRIANGULATE: Invalid email is rejected."""
        with pytest.raises(ValidationError):
            AuthRegister(email="not-an-email", password="securePass123")

    def test_short_password(self):
        """TRIANGULATE: Password shorter than 8 chars is rejected."""
        with pytest.raises(ValidationError):
            AuthRegister(email="user@example.com", password="1234567")

    def test_empty_email(self):
        """TRIANGULATE: Empty email is rejected."""
        with pytest.raises(ValidationError):
            AuthRegister(email="", password="securePass123")

    def test_valid_login(self):
        """RED: Valid login data passes validation."""
        data = AuthLogin(email="user@example.com", password="securePass123")
        assert data.email == "user@example.com"

    def test_token_response(self):
        """RED: Token response is built correctly."""
        data = TokenResponse(access_token="jwt.token.here", token_type="bearer")
        assert data.access_token == "jwt.token.here"
        assert data.token_type == "bearer"

    def test_user_response(self):
        """RED: User response includes id, email, created_at."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        data = UserResponse(id="uuid-123", email="test@test.com", created_at=now)
        assert str(data.id) == "uuid-123"
        assert data.email == "test@test.com"
        assert data.created_at == now


class TestUserSchemas:
    def test_valid_api_key_request(self):
        """RED: Valid API key request passes."""
        data = ApiKeyRequest(openai_api_key="sk-valid-key-12345")
        assert data.openai_api_key == "sk-valid-key-12345"

    def test_empty_api_key_rejected(self):
        """TRIANGULATE: Empty API key is rejected."""
        with pytest.raises(ValidationError):
            ApiKeyRequest(openai_api_key="")

    def test_api_key_response(self):
        """RED: API key response message."""
        data = ApiKeyResponse(message="API key guardada correctamente")
        assert data.message == "API key guardada correctamente"


class TestDocumentSchemas:
    def test_document_response(self):
        """RED: Document response with all fields."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        data = DocumentResponse(
            id="doc-123",
            filename="report.pdf",
            file_type="pdf",
            file_size=2048,
            status="ready",
            chunk_count=5,
            created_at=now,
        )
        assert data.filename == "report.pdf"
        assert data.file_type == "pdf"
        assert data.file_size == 2048
        assert data.status == "ready"
        assert data.chunk_count == 5


class TestConversationSchemas:
    def test_conversation_create_with_title(self):
        """RED: Create conversation with title."""
        data = ConversationCreate(title="Mi consulta")
        assert data.title == "Mi consulta"

    def test_conversation_create_without_title(self):
        """TRIANGULATE: Create conversation without title defaults to None."""
        data = ConversationCreate()
        assert data.title is None

    def test_conversation_response(self):
        """RED: Conversation response."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        data = ConversationResponse(
            id="conv-123", title="Test", created_at=now, updated_at=now
        )
        assert data.id == "conv-123"
        assert data.title == "Test"

    def test_message_response(self):
        """RED: Message response."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        data = MessageResponse(
            id="msg-123",
            role="user",
            content="¿Qué dice el documento?",
            citations=None,
            created_at=now,
        )
        assert data.role == "user"
        assert data.content == "¿Qué dice el documento?"
        assert data.citations is None

    def test_message_response_with_citations(self):
        """TRIANGULATE: Message with citations."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        citations = {"sources": [{"page": 1, "text": "Relevant content"}]}
        data = MessageResponse(
            id="msg-456",
            role="assistant",
            content="Respuesta con referencias",
            citations=citations,
            created_at=now,
        )
        assert data.citations == citations
        assert data.citations["sources"][0]["page"] == 1


class TestChatSchemas:
    def test_chat_request(self):
        """RED: Chat request with conversation_id and message."""
        data = ChatRequest(
            conversation_id="conv-123", message="¿Qué dice el PDF?"
        )
        assert data.conversation_id == "conv-123"
        assert data.message == "¿Qué dice el PDF?"

    def test_chat_request_empty_message(self):
        """TRIANGULATE: Empty message is rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(conversation_id="conv-123", message="")

    def test_stream_event(self):
        """RED: Stream event with token."""
        data = StreamEvent(event="token", data="texto")
        assert data.event == "token"
        assert data.data == "texto"
