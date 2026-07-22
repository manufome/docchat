"""Auth-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AuthRegister(BaseModel):
    """Registration request body."""

    email: EmailStr
    password: str = Field(min_length=8)


class AuthLogin(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile response."""

    id: str
    email: str
    created_at: datetime
