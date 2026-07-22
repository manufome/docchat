"""Tests for the RAG embedding module.

Uses monkey-patching to avoid loading the actual sentence-transformers model.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.rag.embedding import embed_query, embed_texts


def _fake_embed(texts: list[str], **kwargs) -> np.ndarray:
    """Return 384-dim unit vectors matching all-MiniLM-L6-v2 shape."""
    out = np.zeros((len(texts), 384), dtype=np.float32)
    for i, t in enumerate(texts):
        out[i, 0] = 1.0
    # Normalise to unit length
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / norms


@pytest.fixture(autouse=True)
def mock_model():
    """Replace SentenceTransformer with a lightweight fake for all tests."""
    fake_model = MagicMock()
    fake_model.encode.side_effect = _fake_embed

    with patch("app.rag.embedding.sentence_transformers.SentenceTransformer",
               return_value=fake_model):
        yield fake_model


class TestEmbedTexts:
    """RED→GREEN→REFACTOR: embeds list of texts into fixed-dimension vectors."""

    def test_returns_list_of_lists(self):
        """Output is a list of float lists, one per input text."""
        result = embed_texts(["hola mundo"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], list)
        assert all(isinstance(v, float) for v in result[0])

    def test_vector_dimension(self):
        """Each vector has 384 dimensions (all-MiniLM-L6-v2)."""
        result = embed_texts(["test"])
        assert len(result[0]) == 384

    def test_multiple_texts(self):
        """Multiple texts return one vector per text."""
        texts = ["primero", "segundo", "tercero"]
        result = embed_texts(texts)
        assert len(result) == 3

    def test_normalize_embeddings_enabled(self):
        """Normalized embeddings have unit L2 norm (within tolerance)."""
        result = embed_texts(["texto de prueba"])
        norm = np.linalg.norm(result[0])
        assert abs(norm - 1.0) < 1e-5

    def test_empty_list(self):
        """Empty list returns empty list."""
        result = embed_texts([])
        assert result == []


class TestEmbedQuery:
    """RED→GREEN→REFACTOR: single-query convenience wrapper."""

    def test_returns_single_vector(self):
        """embed_query returns a single list of floats."""
        result = embed_query("¿Qué dice el documento?")
        assert isinstance(result, list)
        assert len(result) == 384

    def test_consistent_with_embed_texts(self):
        """embed_query(x) equals embed_texts([x])[0]."""
        query = "consulta de prueba"
        vec_a = embed_query(query)
        vec_b = embed_texts([query])[0]
        assert vec_a == vec_b
