"""Embedding utilities using sentence-transformers.

The model is loaded once (lru_cache) and reused across calls.
all-MiniLM-L6-v2 produces 384-dimensional L2-normalised vectors.
"""

from functools import lru_cache

import numpy as np
import sentence_transformers


@lru_cache(maxsize=1)
def get_model() -> sentence_transformers.SentenceTransformer:
    """Load the sentence-transformers model (cached singleton)."""
    return sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into normalised 384-dimensional vectors.

    Parameters
    ----------
    texts:
        One or more text strings to embed.

    Returns
    -------
    list[list[float]]
        A list of vectors, one per input text.
    """
    if not texts:
        return []
    model = get_model()
    vectors: np.ndarray = model.encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single query string.

    Convenience wrapper around *embed_texts* for a single string.
    """
    return embed_texts([text])[0]
