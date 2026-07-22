"""ChromaDB client factory.

Provides a singleton-like accessor that can be initialised during app
lifespan and reused throughout the application.
"""

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from app.core.config import settings

_client = None


def get_chroma_client():
    """Return the singleton ChromaDB persistent client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_chroma_collection() -> Collection:
    """Return the singleton ChromaDB ``documents`` collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        "documents",
        metadata={"hnsw:space": "cosine"},
    )
