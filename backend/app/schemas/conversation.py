"""Conversation and message Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    """Request body to create a new conversation."""

    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation metadata."""

    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Message in a conversation."""

    id: str
    role: str
    content: str
    citations: Optional[Any] = None
    created_at: datetime
