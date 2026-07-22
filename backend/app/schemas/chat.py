"""Chat-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body to send a message in a conversation."""

    conversation_id: str
    message: str = Field(min_length=1)


class StreamEvent(BaseModel):
    """SSE event emitted during streaming chat responses."""

    event: str  # "token" | "citation" | "error" | "done"
    data: str
