"""Text chunking with overlap for RAG pipelines.

Splits text into overlapping chunks of approximately `chunk_size` characters.
Overlap ensures context continuity between adjacent chunks.
"""

from typing import Union

from pydantic import BaseModel


class TextChunk(BaseModel):
    """A single chunk of text with its metadata."""

    text: str
    metadata: dict
    chunk_id: str  # unique: doc_id:chunk_index


def chunk_text(
    text: str,
    document_id: str,
    document_name: str,
    user_id: str,
    page_num: Union[int, str] = 1,
    chunk_size: int = 512,
    overlap: int = 128,
) -> list[TextChunk]:
    """Split text into overlapping chunks of approximately *chunk_size* characters.

    Parameters
    ----------
    text:
        The full document text to chunk.
    document_id:
        Unique identifier for the source document.
    document_name:
        Display name of the source document.
    user_id:
        Owner of the document (used as metadata for access filtering).
    page_num:
        Page number or sheet name. Passed as metadata.
    chunk_size:
        Target maximum size of each chunk in characters.
    overlap:
        Number of characters from the end of a chunk to repeat at the
        start of the next chunk.

    Returns
    -------
    list[TextChunk]
        Ordered list of text chunks with metadata.
    """
    # Normalise line endings, split into paragraphs
    text = text.replace("\r\n", "\n")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[TextChunk] = []
    current_text = ""

    for para in paragraphs:
        # Single paragraph longer than chunk_size → split with sliding window
        if len(para) > chunk_size:
            # Flush any accumulated text first
            if current_text:
                _finalize_chunk(
                    chunks, current_text, document_id, user_id,
                    document_name, page_num,
                )
                current_text = ""

            step = chunk_size - overlap
            if step <= 0:
                step = 1  # safety: avoid infinite loop
            for i in range(0, len(para), step):
                chunk_str = para[i : i + chunk_size]
                chunk_str = chunk_str.strip()
                if chunk_str:
                    _finalize_chunk(
                        chunks, chunk_str, document_id, user_id,
                        document_name, page_num,
                    )
            current_text = ""
            continue

        # Append paragraph to current buffer
        if current_text:
            candidate = current_text + "\n\n" + para
        else:
            candidate = para

        if len(candidate) > chunk_size and current_text:
            # Finalise current chunk
            _finalize_chunk(
                chunks, current_text, document_id, user_id,
                document_name, page_num,
            )
            # Start new buffer with overlap from finished chunk
            current_text = (current_text[-overlap:] if overlap > 0 else "")
            if current_text:
                current_text += "\n\n"
            current_text += para
        else:
            current_text = candidate

    # Last chunk
    if current_text.strip():
        _finalize_chunk(
            chunks, current_text, document_id, user_id,
            document_name, page_num,
        )

    return chunks


def _finalize_chunk(
    chunks: list[TextChunk],
    text: str,
    document_id: str,
    user_id: str,
    document_name: str,
    page_num: Union[int, str],
) -> None:
    """Create a TextChunk and append it to *chunks*."""
    idx = len(chunks)
    chunks.append(
        TextChunk(
            text=text,
            metadata={
                "user_id": user_id,
                "document_id": document_id,
                "document_name": document_name,
                "page_num": page_num,
                "chunk_index": idx,
            },
            chunk_id=f"{document_id}:{idx}",
        )
    )
