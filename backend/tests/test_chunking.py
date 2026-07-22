"""Tests for the RAG chunking module."""

import pytest
from app.rag.chunking import TextChunk, chunk_text


class TestChunkText:
    """RED→GREEN→REFACTOR: Text chunking with overlap."""

    def test_short_text_single_chunk(self):
        """Text shorter than chunk_size produces one chunk."""
        text = "Este es un texto corto para probar la fragmentación."
        chunks = chunk_text(
            text=text,
            document_id="doc-1",
            document_name="test.txt",
            user_id="user-1",
        )
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_id == "doc-1:0"

    def test_metadata_propagation(self):
        """Each chunk carries correct metadata."""
        text = "Contenido del documento de prueba."
        chunks = chunk_text(
            text=text,
            document_id="doc-42",
            document_name="informe.pdf",
            user_id="user-7",
            page_num=3,
        )
        chunk = chunks[0]
        assert chunk.metadata["user_id"] == "user-7"
        assert chunk.metadata["document_id"] == "doc-42"
        assert chunk.metadata["document_name"] == "informe.pdf"
        assert chunk.metadata["page_num"] == 3
        assert chunk.metadata["chunk_index"] == 0

    def test_multiple_chunks_no_overlap(self):
        """Long text splits into multiple chunks when overlap=0."""
        paragraph = "Este es un párrafo de prueba con contenido suficiente. " * 50
        text = paragraph  # ~3250 chars
        chunks = chunk_text(
            text=text,
            document_id="doc-1",
            document_name="test.txt",
            user_id="user-1",
            chunk_size=512,
            overlap=0,
        )
        assert len(chunks) > 1
        # Each chunk (except possibly last) should be at most chunk_size
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:
                assert len(chunk.text) <= 512, f"Chunk {i} exceeds chunk_size"
            assert chunk.chunk_id == f"doc-1:{i}"

    def test_overlap_increases_chunk_count(self):
        """Text split with overlap produces more chunks due to smaller step."""
        paragraph = "Contenido de prueba con suficiente texto para generar múltiples fragmentos. " * 30
        text = paragraph * 3
        chunks_overlap = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=256, overlap=128,
        )
        chunks_no_overlap = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=256, overlap=0,
        )
        # Overlap shrinks the step from 256 to 128, roughly doubling chunk count
        assert len(chunks_overlap) > len(chunks_no_overlap)
        # Verify each chunk is at most chunk_size (the sliding window enforces this)
        for c in chunks_overlap:
            assert len(c.text) <= 256

    def test_overlap_content_preserved(self):
        """Overlap characters from previous chunk appear at start of next chunk."""
        # Create text where we can predict the boundary
        para = "ABCDEFGHIJ" * 60  # 600 chars
        text = para
        chunk_size = 300
        overlap = 50
        chunks = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=chunk_size, overlap=overlap,
        )
        if len(chunks) >= 2:
            # The last `overlap` chars of chunk 0 should appear at the start of chunk 1
            chunk0_tail = chunks[0].text[-overlap:]
            chunk1_head = chunks[1].text[:overlap]
            assert chunk0_tail == chunk1_head, (
                f"Overlap mismatch: {chunk0_tail!r} != {chunk1_head!r}"
            )

    def test_exact_chunk_size_boundary(self):
        """Text exactly at chunk_size boundary without newlines."""
        text = "A" * 512
        chunks = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=512, overlap=0,
        )
        assert len(chunks) == 1
        assert chunks[0].text == "A" * 512

    def test_empty_text(self):
        """Empty text returns empty list."""
        chunks = chunk_text(
            "", document_id="doc-1", document_name="t.txt",
            user_id="u1",
        )
        assert chunks == []

    def test_whitespace_only_text(self):
        """Whitespace-only text returns empty list."""
        chunks = chunk_text(
            "   \n\n  \n   ", document_id="doc-1", document_name="t.txt",
            user_id="u1",
        )
        assert chunks == []

    def test_chunk_ids_are_unique_and_sequential(self):
        """Chunk IDs follow doc_id:chunk_index pattern and are sequential."""
        paragraph = "Párrafo de prueba. " * 100
        text = paragraph * 5
        chunks = chunk_text(
            text, document_id="doc-x", document_name="test.txt",
            user_id="u1", chunk_size=256, overlap=32,
        )
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == f"doc-x:{i}"

    def test_paragraph_preservation(self):
        """Chunks respect paragraph boundaries when possible."""
        text = (
            "Primer párrafo corto.\n\n"
            "Segundo párrafo también breve.\n\n"
            "Tercero.\n\n"
            "Cuarto párrafo con algo más de contenido para probar."
        )
        # Large chunk_size means everything fits
        chunks = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=2000, overlap=0,
        )
        assert len(chunks) == 1
        # Paragraph structure should be preserved
        assert "Primer párrafo" in chunks[0].text
        assert "Cuarto párrafo" in chunks[0].text

    def test_single_paragraph_longer_than_chunk_size(self):
        """A single paragraph longer than chunk_size is forced to split."""
        text = "Hello world. " * 200  # 2800 chars, no newlines
        chunks = chunk_text(
            text, document_id="doc-1", document_name="t.txt",
            user_id="u1", chunk_size=512, overlap=64,
        )
        assert len(chunks) >= 5  # 2800/512 ≈ 5.5
        # All chunks should have content
        assert all(c.text for c in chunks)
