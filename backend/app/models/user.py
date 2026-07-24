"""User model."""

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


LLM_PROVIDERS = ["openai", "gemini", "groq"]


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    openai_api_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    llm_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="openai")

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
