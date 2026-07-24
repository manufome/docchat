"""Chat service: core RAG+LLM orchestration for streaming chat responses."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Optional

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
from app.services.llm_providers import PROVIDER_DISPLAY, PROVIDER_STREAM


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
    api_key: str,
    llm_provider: str = "openai",
    skip_save_user: bool = False,
) -> AsyncGenerator[dict, None]:
    """Orchestrate the full RAG+LLM chat pipeline.

    Parameters
    ----------
    skip_save_user
        When True, skips saving the user message. Used by the SSE endpoint
        which already saves and commits the user message before streaming.

    Steps
    -----
    1. Save the user's message to the database (unless *skip_save_user*).
    2. Embed the message for retrieval.
    3. Retrieve relevant chunks from ChromaDB (user_id filtered, k=5).
    4. If no chunks found, yield an error event and stop.
    5. Build the RAG prompt with context chunks.
    6. Stream the response from the configured LLM provider.
    7. Parse citations from the streamed response.
    8. Save the assistant message with citations to the database.
    9. Update the conversation timestamp.

    Yields
    ------
    dict
        SSE event dicts with ``type`` and event-specific fields.
    """
    provider_name = PROVIDER_DISPLAY.get(llm_provider, llm_provider)

    # 1. Save user message (skip if caller already did for early commit)
    if not skip_save_user:
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
                "content": "No tiene documentos subidos. Suba al menos un documento para empezar a chatear.",
            }
        else:
            yield {
                "type": "error",
                "content": "No se encontró información relevante en sus documentos para responder esa pregunta.",
            }
        return

    # 5. Build prompt
    messages = build_rag_prompt(message, chunks)
    citation_map = build_citation_map(chunks)

    # 6. Stream from the configured provider
    stream_fn = PROVIDER_STREAM.get(llm_provider)
    if not stream_fn:
        yield {
            "type": "error",
            "content": f"Proveedor LLM no válido: {provider_name}",
        }
        return

    full_response: list[str] = []

    try:
        # Wrap the LLM stream with a per-token timeout so the stream never
        # hangs forever if the provider stops responding mid-stream.
        llm_gen = stream_fn(messages, api_key)
        timeout = getattr(settings, "openai_timeout_seconds", 30)
        while True:
            try:
                token = await asyncio.wait_for(llm_gen.__anext__(), timeout=timeout)
                full_response.append(token)
                yield {"type": "token", "content": token}
            except StopAsyncIteration:
                break
    except asyncio.TimeoutError:
        yield {
            "type": "error",
            "content": (
                f"{provider_name} no está respondiendo. "
                f"Puede intentar de nuevo o cambiar a otro proveedor desde Configuración."
            ),
        }
        return

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "incorrect" in error_msg.lower() or "API_KEY" in error_msg or "not found" in error_msg.lower() and "api" in error_msg.lower():
            yield {
                "type": "error",
                "content": f"No ha configurado su clave API de {provider_name}. Vaya a su perfil para agregarla.",
            }
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            retry_info = ""
            import re
            match = re.search(r"retry in (\d+\.?\d*)s", error_msg, re.IGNORECASE)
            if match:
                seconds = float(match.group(1))
                if seconds < 120:
                    retry_info = f" Puede intentar de nuevo en unos {int(seconds)} segundos."
                else:
                    retry_info = f" Puede intentar de nuevo en aproximadamente {int(seconds // 60)} minutos."
            yield {
                "type": "error",
                "content": (
                    f"{provider_name} agotó su cuota gratuita por ahora. "
                    f"La capa gratuita de {provider_name} tiene límites bajos de solicitudes por minuto."
                    f"{retry_info}"
                    f" También puede cambiar a otro proveedor (Groq tiene un plan gratuito más generoso) desde Configuración."
                ),
            }
        else:
            yield {
                "type": "error",
                "content": f"Error al comunicarse con {provider_name}: {error_msg}",
            }
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
