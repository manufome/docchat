"""Chat service: core RAG+LLM orchestration for streaming chat responses."""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import select

from app.core.config import settings
from app.db.chroma import get_chroma_collection
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.rag.embedding import embed_query
from app.rag.prompt import build_rag_prompt
from app.rag.retrieval import retrieve_chunks
from app.services.citation_service import build_citation_map, parse_citations


async def save_user_message(
    db,
    conversation_id: str,
    user_id: str,
    content: str,
) -> str:
    """Save a user message to the database and return its ID."""
    msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg.id


async def save_assistant_message(
    db,
    conversation_id: str,
    content: str,
    citations: Optional[list[dict]] = None,
) -> str:
    """Save an assistant message with optional citations and return its ID."""
    msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        citations=citations,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg.id


async def update_conversation_timestamp(db, conversation_id: str) -> None:
    """Touch the conversation's updated_at timestamp."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        conv.updated_at = datetime.now(timezone.utc)
        await db.flush()


async def process_chat_message(
    user_id: str,
    conversation_id: str,
    message: str,
    db,
    openai_api_key: str,
) -> AsyncGenerator[dict, None]:
    """Orchestrate the full RAG+LLM chat pipeline.

    Steps
    -----
    1. Save the user's message to the database.
    2. Embed the message for retrieval.
    3. Retrieve relevant chunks from ChromaDB (user_id filtered, k=5).
    4. If no chunks found, yield an error event and stop.
    5. Build the RAG prompt with context chunks.
    6. Stream the response from OpenAI.
    7. Parse citations from the streamed response.
    8. Save the assistant message with citations to the database.
    9. Update the conversation timestamp.

    Yields
    ------
    dict
        SSE event dicts with ``type`` and event-specific fields.
    """
    # 1. Save user message
    await save_user_message(db, conversation_id, user_id, message)

    # 2. Embed the query
    query_embedding = embed_query(message)

    # 3. Retrieve chunks
    chroma_collection = get_chroma_collection()
    chunks = retrieve_chunks(
        collection=chroma_collection,
        query_embedding=query_embedding,
        user_id=user_id,
        k=5,
    )

    # 4. No chunks → check if user has documents
    if not chunks:
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id).limit(1)
        )
        has_docs = doc_result.scalar_one_or_none() is not None

        if not has_docs:
            yield {
                "type": "error",
                "content": "No tienes documentos subidos. Sube al menos un documento para empezar a chatear.",
            }
        else:
            yield {
                "type": "error",
                "content": "No encontré información relevante en tus documentos para responder esa pregunta.",
            }
        return

    # 5. Build prompt
    messages = build_rag_prompt(message, chunks)
    citation_map = build_citation_map(chunks)

    # 6. Stream from OpenAI
    client = AsyncOpenAI(api_key=openai_api_key)
    full_response: list[str] = []

    try:
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            max_tokens=settings.openai_max_tokens,
            timeout=settings.openai_timeout_seconds,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_response.append(delta.content)
                yield {"type": "token", "content": delta.content}

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "incorrect" in error_msg.lower():
            yield {
                "type": "error",
                "content": "No has configurado tu clave API de OpenAI. Ve a tu perfil para agregarla.",
            }
        else:
            yield {"type": "error", "content": f"Error al comunicarse con OpenAI: {error_msg}"}
        return

    # 7. Parse citations from the full response
    full_text = "".join(full_response)
    clean_text, citations = parse_citations(full_text, citation_map)

    # 8. Save assistant message
    msg_id = await save_assistant_message(db, conversation_id, clean_text, citations)

    # Emit citation events
    for citation in citations:
        yield {"type": "citation", "citation": citation}

    # 9. Update conversation timestamp
    await update_conversation_timestamp(db, conversation_id)

    # Done
    yield {"type": "done", "message_id": msg_id}
