"""User profile API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import encrypt_api_key
from app.models.user import LLM_PROVIDERS, User
from app.schemas.user import ApiKeyRequest, ApiKeyResponse, UserProviderResponse

router = APIRouter(prefix="/api/users", tags=["users"])

PROVIDER_NAMES = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
    "groq": "Groq",
}


@router.put("/me/api-key", response_model=ApiKeyResponse)
async def set_api_key(
    data: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store the user's API key for the chosen provider, encrypted with Fernet."""
    if data.provider not in LLM_PROVIDERS:
        return ApiKeyResponse(message=f"Proveedor no válido: {data.provider}")

    encrypted = encrypt_api_key(data.api_key, settings.secret_key)
    current_user.openai_api_key = encrypted
    current_user.llm_provider = data.provider
    await db.flush()

    provider_name = PROVIDER_NAMES.get(data.provider, data.provider)
    return ApiKeyResponse(
        message=f"API key de {provider_name} guardada correctamente."
    )


@router.get("/me/provider", response_model=UserProviderResponse)
async def get_provider(
    current_user: User = Depends(get_current_user),
):
    """Return the user's current LLM provider and whether they have a key set."""
    return UserProviderResponse(
        provider=current_user.llm_provider,
        has_key=bool(current_user.openai_api_key),
    )
