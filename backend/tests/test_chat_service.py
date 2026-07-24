"""Tests for the chat service (core RAG+LLM orchestration).

RED→GREEN→REFACTOR: process_chat_message streaming pipeline.
"""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from app.services.chat_service import process_chat_message


@pytest.fixture
def mock_db():
    """Mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def mock_chunks():
    """Simulate retrieved ChromaDB chunks."""
    return [
        {
            "id": "chunk-1",
            "document": "La capital de Francia es París.",
            "metadata": {
                "user_id": "user-1",
                "document_id": "doc-1",
                "document_name": "geografia.pdf",
                "page_num": 2,
            },
            "distance": 0.15,
        },
        {
            "id": "chunk-2",
            "document": "París tiene la Torre Eiffel.",
            "metadata": {
                "user_id": "user-1",
                "document_id": "doc-1",
                "document_name": "geografia.pdf",
                "page_num": 3,
            },
            "distance": 0.22,
        },
    ]


class TestProcessChatMessage:
    """RED→GREEN→REFACTOR: Chat streaming orchestration."""

    @pytest.mark.asyncio
    async def test_streams_tokens(self, mock_db, mock_chunks):
        """GIVEN valid inputs WHEN streamed THEN tokens yielded."""
        with (
            patch("app.services.chat_service.save_user_message", new_callable=AsyncMock) as mock_save_user,
            patch("app.services.chat_service.embed_query") as mock_embed,
            patch("app.services.chat_service.retrieve_chunks") as mock_retrieve,
            patch("app.services.chat_service.build_rag_prompt") as mock_build,
            patch("app.services.chat_service.build_citation_map") as mock_cite_map,
            patch("app.services.chat_service.parse_citations") as mock_parse,
            patch("app.services.chat_service.save_assistant_message", new_callable=AsyncMock) as mock_save_assistant,
            patch("app.services.chat_service.update_conversation_timestamp", new_callable=AsyncMock) as mock_update_ts,
            patch("app.services.chat_service.get_chroma_collection"),
        ):
            mock_save_user.return_value = "msg-user-1"
            mock_embed.return_value = [0.1] * 384
            mock_retrieve.return_value = mock_chunks
            mock_build.return_value = [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User question"},
            ]
            mock_cite_map.return_value = {
                1: {"index": 1, "document_name": "geografia.pdf", "page": 2, "text_preview": "La capital..."},
                2: {"index": 2, "document_name": "geografia.pdf", "page": 3, "text_preview": "París..."},
            }
            mock_parse.return_value = ("La capital es París.", [])
            mock_save_assistant.return_value = "msg-assistant-1"

            # Mock OpenAI streaming response
            mock_stream = MagicMock()
            mock_stream.__aiter__.return_value = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="La "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="capital "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="es "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="París"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # finish
            ]

            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

            with patch("app.services.llm_providers.AsyncOpenAI", return_value=mock_client):
                events = []
                async for event in process_chat_message(
                    user_id="user-1",
                    conversation_id="conv-1",
                    message="¿Cuál es la capital de Francia?",
                    db=mock_db,
                    api_key="sk-test",
                    llm_provider="openai",
                ):
                    events.append(event)

        # Should have emitted tokens
        token_events = [e for e in events if e.get("type") == "token"]
        assert len(token_events) > 0
        # The full text should be accumulated
        full_text = "".join(e["content"] for e in token_events)
        assert "París" in full_text

        # Should have done event
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) == 1
        assert done_events[0]["message_id"] == "msg-assistant-1"

        # Verify save flow
        mock_save_user.assert_awaited_once()
        mock_embed.assert_called_once_with("¿Cuál es la capital de Francia?")
        mock_retrieve.assert_called_once()
        mock_build.assert_called_once()
        mock_save_assistant.assert_awaited_once()
        mock_update_ts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_emits_citations(self, mock_db, mock_chunks):
        """GIVEN chunks with citations WHEN streamed THEN citation events emitted."""
        with (
            patch("app.services.chat_service.save_user_message", new_callable=AsyncMock) as mock_save_user,
            patch("app.services.chat_service.embed_query") as mock_embed,
            patch("app.services.chat_service.retrieve_chunks") as mock_retrieve,
            patch("app.services.chat_service.build_rag_prompt") as mock_build,
            patch("app.services.chat_service.build_citation_map") as mock_cite_map,
            patch("app.services.chat_service.parse_citations") as mock_parse,
            patch("app.services.chat_service.save_assistant_message", new_callable=AsyncMock),
            patch("app.services.chat_service.update_conversation_timestamp", new_callable=AsyncMock),
            patch("app.services.chat_service.get_chroma_collection") as mock_get_chroma,
        ):
            mock_save_user.return_value = "msg-user-1"
            mock_embed.return_value = [0.1] * 384
            mock_retrieve.return_value = mock_chunks
            mock_build.return_value = [{"role": "system", "content": "X"}, {"role": "user", "content": "Y"}]

            citation_map = {
                1: {"index": 1, "document_name": "geografia.pdf", "page": 2, "text_preview": "La capital..."},
                2: {"index": 2, "document_name": "geografia.pdf", "page": 3, "text_preview": "París..."},
            }
            mock_cite_map.return_value = citation_map
            mock_parse.return_value = ("Respuesta[1][2].", [
                citation_map[1],
                citation_map[2],
            ])

            mock_stream = MagicMock()
            mock_stream.__aiter__.return_value = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Respuesta"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
            ]

            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

            with patch("app.services.llm_providers.AsyncOpenAI", return_value=mock_client):
                events = []
                async for event in process_chat_message(
                    user_id="user-1",
                    conversation_id="conv-1",
                    message="¿Capital?",
                    db=mock_db,
                    api_key="sk-test",
                    llm_provider="openai",
                ):
                    events.append(event)

            # Should have citation events (one per chunk)
            citation_events = [e for e in events if e.get("type") == "citation"]
            assert len(citation_events) == 2

    @pytest.mark.asyncio
    async def test_no_chunks_emits_error(self, mock_db):
        """GIVEN no chunks retrieved WHEN streamed THEN error event."""
        with (
            patch("app.services.chat_service.save_user_message", new_callable=AsyncMock) as mock_save_user,
            patch("app.services.chat_service.embed_query") as mock_embed,
            patch("app.services.chat_service.retrieve_chunks") as mock_retrieve,
            patch("app.services.chat_service.get_chroma_collection"),
        ):
            mock_save_user.return_value = "msg-user-1"
            mock_embed.return_value = [0.1] * 384
            mock_retrieve.return_value = []  # No chunks

            events = []
            async for event in process_chat_message(
                user_id="user-1",
                conversation_id="conv-1",
                message="Pregunta sin contexto",
                db=mock_db,
                api_key="sk-test",
                llm_provider="openai",
            ):
                events.append(event)

            error_events = [e for e in events if e.get("type") == "error"]
            assert len(error_events) == 1
            assert "relevante" in error_events[0]["content"]
