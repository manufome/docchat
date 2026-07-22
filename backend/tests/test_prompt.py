"""Tests for the RAG prompt module."""

from app.rag.prompt import RAG_SYSTEM_PROMPT, build_rag_prompt


class TestBuildRagPrompt:
    """RED→GREEN→REFACTOR: RAG prompt construction."""

    def test_returns_system_and_user_messages(self):
        """Output contains exactly two messages: system and user."""
        chunks = [
            {"id": "c1", "document": "El gato es negro.",
             "metadata": {"document_name": "doc1.pdf", "page_num": 2}, "distance": 0.1},
        ]
        messages = build_rag_prompt("¿De qué color es el gato?", chunks)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_system_prompt_is_constant(self):
        """System prompt is the RAG_SYSTEM_PROMPT constant."""
        messages = build_rag_prompt("test", [])
        assert messages[0]["content"] == RAG_SYSTEM_PROMPT

    def test_context_includes_chunk_content(self):
        """Chunk content appears inside the context delimiters."""
        chunks = [
            {"id": "c1", "document": "Contenido relevante.",
             "metadata": {"document_name": "informe.pdf", "page_num": 1}, "distance": 0.5},
        ]
        messages = build_rag_prompt("consulta", chunks)
        user_msg = messages[1]["content"]
        assert "---INICIO FRAGMENTOS---" in user_msg
        assert "---FIN FRAGMENTOS---" in user_msg
        assert "Contenido relevante." in user_msg
        assert "[1]" in user_msg

    def test_multiple_chunks_get_sequential_citations(self):
        """Chunks are cited [1], [2], ... in order."""
        chunks = [
            {"id": "c1", "document": "Texto A.",
             "metadata": {"document_name": "a.pdf", "page_num": 1}, "distance": 0.1},
            {"id": "c2", "document": "Texto B.",
             "metadata": {"document_name": "b.pdf", "page_num": 2}, "distance": 0.2},
        ]
        messages = build_rag_prompt("consulta", chunks)
        user_msg = messages[1]["content"]
        assert "[1]" in user_msg
        assert "[2]" in user_msg

    def test_empty_chunks_still_produces_prompt(self):
        """Empty chunks result in a prompt with no context."""
        messages = build_rag_prompt("solo pregunta", [])
        user_msg = messages[1]["content"]
        assert "---INICIO FRAGMENTOS---" in user_msg
        # No chunk content
        assert "---FIN FRAGMENTOS---" in user_msg
        assert "solo pregunta" in user_msg

    def test_source_name_in_context(self):
        """Document name and page appear in the context."""
        chunks = [
            {"id": "c1", "document": "texto",
             "metadata": {"document_name": "manual.pdf", "page_num": 5}, "distance": 0.3},
        ]
        messages = build_rag_prompt("pregunta", chunks)
        user_msg = messages[1]["content"]
        assert "manual.pdf" in user_msg
        assert "Página: 5" in user_msg
