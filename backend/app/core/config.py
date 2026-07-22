"""Application configuration via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    app_name: str = "DocChat"
    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./backend/data/docchat.db"
    chroma_path: str = "./backend/data/chroma"
    upload_dir: str = "./backend/data/uploads"
    cors_origins: str = "http://localhost:5173"
    max_upload_size_mb: int = 10
    max_files_per_user: int = 4
    openai_max_tokens: int = 2048
    openai_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
