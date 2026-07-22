"""User-profile-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ApiKeyRequest(BaseModel):
    """Request body to store an OpenAI API key."""

    openai_api_key: str = Field(min_length=1)


class ApiKeyResponse(BaseModel):
    """Response after storing an API key."""

    message: str
