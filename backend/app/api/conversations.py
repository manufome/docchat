"""Conversations API endpoints: CRUD for conversations and messages."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _conversation_to_response(conv: Conversation) -> dict:
    """Convert a Conversation model to a response dict."""
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


def _message_to_response(msg: Message) -> dict:
    """Convert a Message model to a response dict."""
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "citations": msg.citations,
        "created_at": msg.created_at,
    }


async def _get_user_conversation(
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
) -> Conversation:
    """Fetch a conversation by ID, ensuring it belongs to the user.

    Raises 404 if not found or not owned by the user.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada.",
        )
    return conv


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation. Title is optional; if omitted, it can be
    auto-generated later based on the first message."""
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    return _conversation_to_response(conversation)


@router.get("", response_model=list[dict])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's conversations, newest first."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [_conversation_to_response(c) for c in convs]


@router.get("/{conversation_id}/messages", response_model=list[dict])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List messages for a conversation, ordered by creation time.

    Returns 404 if the conversation doesn't exist or belongs to another user.
    """
    conv = await _get_user_conversation(conversation_id, current_user.id, db)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    msgs = result.scalars().all()
    return [_message_to_response(m) for m in msgs]


@router.delete("/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hard-delete a conversation and its messages.

    Returns 404 if the conversation doesn't exist or belongs to another user.
    """
    conv = await _get_user_conversation(conversation_id, current_user.id, db)

    await db.delete(conv)
    await db.flush()

    return {"detail": "Conversación eliminada correctamente."}
