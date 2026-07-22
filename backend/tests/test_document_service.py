"""Tests for the document processing service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_chroma_collection():
    return MagicMock()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_process_document_pdf_success(mock_db, mock_chroma_collection):
    """GIVEN a PDF WHEN process_document completes THEN status is ready and chunks stored."""
    from app.models.document import Document
    from app.services.document_service import process_document

    doc = Document(
        id="doc-1", user_id="user-1", filename="test.pdf",
        file_type="pdf", file_size=1024, status="processing",
    )
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = doc
    mock_db.execute.return_value = scalar_mock

    with patch("app.services.document_service.parse_pdf",
               new=AsyncMock(return_value=[{"page_num": 1, "text": "contenido del pdf"}])):
        with patch("app.services.document_service.chunk_text") as mock_chunk:
            mock_chunk.return_value = [
                MagicMock(text="chunk1 text", chunk_id="doc-1:0",
                          metadata={"user_id": "user-1", "document_id": "doc-1",
                                    "document_name": "test.pdf", "page_num": 1,
                                    "chunk_index": 0}),
            ]
            with patch("app.services.document_service.embed_texts",
                       return_value=[[0.1] * 384]):
                await process_document(
                    user_id="user-1", document_id="doc-1",
                    file_path="/tmp/test.pdf", file_type="pdf",
                    filename="test.pdf", db=mock_db,
                    chroma_collection=mock_chroma_collection,
                )

    assert doc.status == "ready"
    assert doc.chunk_count == 1
    # Verify chroma add was called
    mock_chroma_collection.add.assert_called_once()
    call_kwargs = mock_chroma_collection.add.call_args[1]
    assert call_kwargs["ids"] == ["doc-1:0"]
    assert call_kwargs["documents"] == ["chunk1 text"]


@pytest.mark.asyncio
async def test_process_document_failure_sets_failed(mock_db, mock_chroma_collection):
    """GIVEN a document WHEN an error occurs THEN status is 'failed'."""
    from app.models.document import Document
    from app.services.document_service import process_document

    doc = Document(
        id="doc-2", user_id="user-1", filename="bad.pdf",
        file_type="pdf", file_size=512, status="processing",
    )
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = doc
    mock_db.execute.return_value = scalar_mock

    with patch("app.services.document_service.parse_pdf",
               side_effect=Exception("Parse error")):
        await process_document(
            user_id="user-1", document_id="doc-2",
            file_path="/tmp/bad.pdf", file_type="pdf",
            filename="bad.pdf", db=mock_db,
            chroma_collection=mock_chroma_collection,
        )

    assert doc.status == "failed"
    assert doc.chunk_count is None
    # Chroma add should NOT have been called
    mock_chroma_collection.add.assert_not_called()
