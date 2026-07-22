"""Chat-related Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body to send a message in a conversation.

    If ``conversation_id`` is omitted, a new conversation is created
    automatically. Optionally provide a ``title`` for the new conversation.
    """

    conversation_id: Optional[str] = None
    title: Optional[str] = None
    message: str = Field(min_length=1)


class StreamEvent(BaseModel):
    """SSE event emitted during streaming chat responses."""

    event: str  # "token" | "citation" | "error" | "done"
    data: str
