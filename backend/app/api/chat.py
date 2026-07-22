"""Chat API endpoint: SSE streaming chat responses."""

import json
from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import decrypt_api_key
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.chat_service import process_chat_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _event_generator(
    user_id: str,
    conversation_id: str,
    message: str,
    db: AsyncSession,
    api_key: str,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events from the chat service.

    Always yields a terminal error event on failure so the stream is never
    left hanging.
    """
    try:
        async for event in process_chat_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            db=db,
            openai_api_key=api_key,
        ):
            yield f"data: {json.dumps(event, default=str)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat completion response using Server-Sent Events.

    The client sends a user message. The server streams token deltas,
    citations, and a done event as SSE ``data:`` frames.

    If the user has no OpenAI API key configured, an error event is emitted
    immediately.
    """
    # Validate / decrypt API key
    api_key: Optional[str] = current_user.openai_api_key
    if not api_key:
        return StreamingResponse(
            _error_stream("No has configurado tu clave API de OpenAI. Ve a tu perfil para agregarla."),
            media_type="text/event-stream",
        )

    try:
        decrypted_key = decrypt_api_key(api_key, settings.secret_key)
    except Exception:
        return StreamingResponse(
            _error_stream("No has configurado tu clave API de OpenAI. Ve a tu perfil para agregarla."),
            media_type="text/event-stream",
        )

    # Resolve conversation
    conversation_id = request.conversation_id
    if conversation_id:
        # Verify the conversation belongs to the user
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            return StreamingResponse(
                _error_stream("Conversación no encontrada."),
                media_type="text/event-stream",
            )
    else:
        # Create a new conversation
        title = request.title or None
        conv = Conversation(
            user_id=current_user.id,
            title=title,
        )
        db.add(conv)
        await db.flush()
        await db.refresh(conv)
        conversation_id = conv.id

    return StreamingResponse(
        _event_generator(
            user_id=current_user.id,
            conversation_id=conversation_id,
            message=request.message,
            db=db,
            api_key=decrypted_key,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _error_stream(message: str) -> AsyncGenerator[str, None]:
    """Yield a single SSE error event."""
    yield f"data: {json.dumps({'type': 'error', 'content': message})}\n\n"
