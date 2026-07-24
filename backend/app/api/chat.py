"""Chat API endpoint: SSE streaming chat responses."""

import json
from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_async_session_factory, get_current_user_light
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
    api_key: str,
    llm_provider: str = "openai",
    session_factory=None,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events from the chat service.

    A **new** database session is created from the factory so the pool
    connection is acquired only for the write at the end (assistant
    message), never held during the LLM streaming phase.
    """
    if session_factory is None:
        yield f"data: {json.dumps({'type': 'error', 'content': 'Session factory not configured'})}\n\n"
        return

    async with session_factory() as db:
        try:
            async for event in process_chat_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                db=db,
                api_key=api_key,
                llm_provider=llm_provider,
                skip_save_user=True,
            ):
                yield f"data: {json.dumps(event, default=str)}\n\n"
            await db.commit()
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_light),
    session_factory=Depends(get_async_session_factory),
):
    """Stream a chat completion response using Server-Sent Events."""
    provider_name = current_user.llm_provider or "openai"

    # Validate / decrypt API key
    api_key: Optional[str] = current_user.openai_api_key
    if not api_key:
        return StreamingResponse(
            _error_stream(
                "No ha configurado su clave API. Vaya a su perfil para agregarla."
            ),
            media_type="text/event-stream",
        )

    try:
        decrypted_key = decrypt_api_key(api_key, settings.secret_key)
    except Exception:
        return StreamingResponse(
            _error_stream(
                "No ha configurado su clave API. Vaya a su perfil para agregarla."
            ),
            media_type="text/event-stream",
        )

    # ── Setup phase (brief session, committed and closed before streaming) ──
    async with session_factory() as db:
        # Resolve conversation
        conversation_id = request.conversation_id
        if conversation_id:
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
            title = request.title or None
            conv = Conversation(
                user_id=current_user.id,
                title=title,
            )
            db.add(conv)
            await db.flush()
            await db.refresh(conv)
            conversation_id = conv.id

        # Save user message
        from app.models.message import Message

        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        db.add(user_msg)
        await db.commit()
    # ── Session returned to pool. Streaming starts with NO session held. ──

    return StreamingResponse(
        _event_generator(
            user_id=current_user.id,
            conversation_id=conversation_id,
            message=request.message,
            api_key=decrypted_key,
            llm_provider=provider_name,
            session_factory=session_factory,
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
