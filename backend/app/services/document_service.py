"""Document processing pipeline orchestration.

Parses, chunks, embeds, and stores document chunks into ChromaDB.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.rag.chunking import chunk_text
from app.rag.embedding import embed_texts
from app.services.parser_service import parse_docx, parse_pdf, parse_xlsx


async def process_document(
    user_id: str,
    document_id: str,
    file_path: str,
    file_type: str,
    filename: str,
    db: AsyncSession,
    chroma_collection,
) -> None:
    """Run the full document processing pipeline.

    1. Parse the file based on *file_type*.
    2. Chunk the extracted text.
    3. Embed each chunk.
    4. Store embeddings in ChromaDB.
    5. Update the Document record to ``ready`` (or ``failed`` on error).

    Parameters
    ----------
    user_id:
        Document owner.
    document_id:
        Document primary key (UUID).
    file_path:
        Absolute path to the saved file on disk.
    file_type:
        ``pdf``, ``docx``, or ``xlsx``.
    filename:
        Original uploaded filename.
    db:
        SQLAlchemy async session.
    chroma_collection:
        ChromaDB collection to store/query embeddings.
    """
    try:
        # 1. Parse
        if file_type == "pdf":
            pages = await parse_pdf(file_path)
        elif file_type == "docx":
            pages = await parse_docx(file_path)
        elif file_type == "xlsx":
            pages = await parse_xlsx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        all_chunks: list[dict] = []
        all_embeddings: list[list[float]] = []
        all_metadatas: list[dict] = []
        all_ids: list[str] = []

        for page in pages:
            text = page["text"]
            if not text:
                continue

            chunks = chunk_text(
                text=text,
                document_id=document_id,
                document_name=filename,
                user_id=user_id,
                page_num=page["page_num"],
            )

            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadatas.append(chunk.metadata)
                all_ids.append(chunk.chunk_id)

        if all_chunks:
            chunk_texts = [c.text for c in all_chunks]
            all_embeddings = embed_texts(chunk_texts)

            # 4. Store in ChromaDB
            chroma_collection.add(
                ids=all_ids,
                embeddings=all_embeddings,
                metadatas=all_metadatas,
                documents=chunk_texts,
            )

        # 5. Update document status
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "ready"
            doc.chunk_count = len(all_chunks)
            await db.flush()

    except Exception:
        # Mark as failed on any error
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "failed"
            doc.chunk_count = None
            await db.flush()
