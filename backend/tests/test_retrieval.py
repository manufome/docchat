"""Integration tests for ChromaDB-backed retrieval.

Uses EphemeralClient (in-memory) to avoid filesystem contamination.
Real embeddings are faked at the embedding module level.
"""

from unittest.mock import patch

import chromadb
import numpy as np
import pytest
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from app.rag.retrieval import retrieve_chunks


_coll_counter: int = 0


@pytest.fixture
def collection() -> Collection:
    """Provide a fresh in-memory ChromaDB collection per test."""
    global _coll_counter
    _coll_counter += 1
    client = chromadb.Client(
        Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )
    return client.get_or_create_collection(
        f"test_docs_{_coll_counter}",
        metadata={"hnsw:space": "cosine"},
    )


@pytest.fixture(autouse=True)
def mock_embedding():
    """Mock embed_query to return a fixed 384-dim unit vector."""
    fake_vec = np.zeros(384, dtype=np.float32)
    fake_vec[0] = 1.0
    with patch("app.rag.retrieval.embed_query", return_value=fake_vec.tolist()):
        yield


def _add_test_chunk(
    collection: Collection,
    chunk_id: str,
    text: str,
    user_id: str,
    document_id: str = "doc-1",
    document_name: str = "test.pdf",
) -> None:
    """Helper to insert a chunk into the test collection."""
    vec = np.zeros(384, dtype=np.float32).tolist()
    collection.add(
        ids=[chunk_id],
        embeddings=[vec],
        metadatas=[{
            "user_id": user_id,
            "document_id": document_id,
            "document_name": document_name,
            "page_num": 1,
            "chunk_index": 0,
        }],
        documents=[text],
    )


class TestRetrieveChunks:
    """RED→GREEN→REFACTOR: ChromaDB retrieval with user_id filtering."""

    def test_retrieve_existing_chunks(self, collection):
        """GIVEN chunks exist WHEN retrieved THEN they are returned."""
        _add_test_chunk(collection, "c1", "contenido del documento", "user-a")
        _add_test_chunk(collection, "c2", "más contenido relevante", "user-a")

        results = retrieve_chunks(collection, [1.0] + [0.0] * 383, user_id="user-a", k=5)
        assert len(results) == 2
        ids = {r["id"] for r in results}
        assert ids == {"c1", "c2"}

    def test_user_id_filter_prevents_cross_user_access(self, collection):
        """GIVEN chunks from user-a WHEN user-b queries THEN no results returned."""
        _add_test_chunk(collection, "c1", "user a content", "user-a")
        _add_test_chunk(collection, "c2", "more user a content", "user-a")

        results = retrieve_chunks(
            collection, [1.0] + [0.0] * 383, user_id="user-b", k=5
        )
        assert len(results) == 0

    def test_returns_chunks_with_distances(self, collection):
        """Each result includes id, document, metadata, and distance."""
        _add_test_chunk(collection, "c1", "texto de prueba", "user-a")
        results = retrieve_chunks(collection, [1.0] + [0.0] * 383, user_id="user-a")
        assert len(results) == 1
        r = results[0]
        assert "id" in r
        assert "document" in r
        assert r["document"] == "texto de prueba"
        assert "metadata" in r
        assert "distance" in r

    def test_empty_results_when_no_data(self, collection):
        """GIVEN no chunks WHEN retrieved THEN empty list."""
        results = retrieve_chunks(collection, [1.0] + [0.0] * 383, user_id="user-a")
        assert results == []

    def test_respects_k_parameter(self, collection):
        """GIVEN 5 chunks WHEN k=2 THEN only 2 returned."""
        for i in range(5):
            _add_test_chunk(collection, f"c{i}", f"content {i}", "user-a")
        results = retrieve_chunks(collection, [1.0] + [0.0] * 383, user_id="user-a", k=2)
        assert len(results) == 2

    def test_mixed_users_filters_correctly(self, collection):
        """GIVEN chunks from multiple users WHEN filtered THEN only matching user."""
        _add_test_chunk(collection, "c1", "user a content", "user-a")
        _add_test_chunk(collection, "c2", "user b content", "user-b")
        _add_test_chunk(collection, "c3", "more user a", "user-a")

        results = retrieve_chunks(collection, [1.0] + [0.0] * 383, user_id="user-a", k=5)
        assert len(results) == 2
        assert all(r["metadata"]["user_id"] == "user-a" for r in results)
