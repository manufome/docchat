"""User-profile-related Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyRequest(BaseModel):
    """Request body to store an API key for an LLM provider."""

    api_key: str = Field(min_length=1)
    provider: str = Field(default="openai", pattern="^(openai|gemini|groq)$")


class ApiKeyResponse(BaseModel):
    """Response after storing an API key."""

    message: str


class UserProviderResponse(BaseModel):
    """Current user's LLM provider setting."""

    provider: str
    has_key: bool
