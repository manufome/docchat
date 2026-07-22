"""ChromaDB retrieval for RAG pipelines.

Always filters by *user_id* to prevent cross-user data leakage.
"""

from app.rag.embedding import embed_query


def retrieve_chunks(
    collection,
    query_embedding: list[float],
    user_id: str,
    k: int = 5,
) -> list[dict]:
    """Retrieve the top‑k most similar chunks for a user.

    Parameters
    ----------
    collection:
        A ChromaDB ``Collection`` instance.
    query_embedding:
        The embedding vector of the user's query.
    user_id:
        The authenticated user's ID.  Used as a metadata filter so that
        only chunks belonging to this user are considered.
    k:
        Number of chunks to return (default 5).

    Returns
    -------
    list[dict]
        Each dict contains ``id``, ``document``, ``metadata``, and ``distance``.
        Empty list when nothing matches.
    """
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"user_id": user_id},
    )

    if not results["ids"] or not results["ids"][0]:
        return []

    retrieved = []
    for i, chunk_id in enumerate(results["ids"][0]):
        retrieved.append(
            {
                "id": chunk_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0.0,
            }
        )

    return retrieved
