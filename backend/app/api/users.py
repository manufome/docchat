"""User profile API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import encrypt_api_key
from app.models.user import User
from app.schemas.user import ApiKeyRequest, ApiKeyResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.put("/me/api-key", response_model=ApiKeyResponse)
async def set_api_key(
    data: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store the user's OpenAI API key, encrypted with Fernet derived from SECRET_KEY."""
    encrypted = encrypt_api_key(data.openai_api_key, settings.secret_key)
    current_user.openai_api_key = encrypted
    await db.flush()

    return ApiKeyResponse(message="API key guardada correctamente")
