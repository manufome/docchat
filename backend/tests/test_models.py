"""Tests for SQLAlchemy models."""

import pytest
from sqlalchemy import select

from app.db.base import Base
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message


@pytest.mark.asyncio
async def test_create_user(async_session):
    """RED: Create a User and verify attributes."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_pw_placeholder",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_pw_placeholder"
    assert user.openai_api_key is None
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_email_unique_constraint(async_session):
    """TRIANGULATE: Duplicate email raises integrity error."""
    from sqlalchemy.exc import IntegrityError

    user1 = User(email="dupe@example.com", hashed_password="pw1")
    async_session.add(user1)
    await async_session.commit()

    user2 = User(email="dupe@example.com", hashed_password="pw2")
    async_session.add(user2)
    with pytest.raises(IntegrityError):
        await async_session.commit()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_create_document(async_session):
    """RED: Create a Document linked to a User."""
    user = User(email="doc_user@example.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    doc = Document(
        user_id=user.id,
        filename="test.pdf",
        file_type="pdf",
        file_size=1024,
        status="processing",
    )
    async_session.add(doc)
    await async_session.commit()
    await async_session.refresh(doc)

    assert doc.id is not None
    assert doc.filename == "test.pdf"
    assert doc.file_type == "pdf"
    assert doc.file_size == 1024
    assert doc.status == "processing"
    assert doc.chunk_count is None
    assert doc.created_at is not None
    assert doc.user_id == user.id


@pytest.mark.asyncio
async def test_create_conversation(async_session):
    """RED: Create a Conversation linked to a User."""
    user = User(email="conv_user@example.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    conv = Conversation(user_id=user.id, title="Mi primera consulta")
    async_session.add(conv)
    await async_session.commit()
    await async_session.refresh(conv)

    assert conv.id is not None
    assert conv.title == "Mi primera consulta"
    assert conv.user_id == user.id
    assert conv.created_at is not None
    assert conv.updated_at is not None


@pytest.mark.asyncio
async def test_create_message(async_session):
    """RED: Create a Message linked to a Conversation."""
    user = User(email="msg_user@example.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    conv = Conversation(user_id=user.id)
    async_session.add(conv)
    await async_session.commit()
    await async_session.refresh(conv)

    msg = Message(
        conversation_id=conv.id,
        role="user",
        content="¿Qué dice el documento?",
    )
    async_session.add(msg)
    await async_session.commit()
    await async_session.refresh(msg)

    assert msg.id is not None
    assert msg.role == "user"
    assert msg.content == "¿Qué dice el documento?"
    assert msg.citations is None
    assert msg.conversation_id == conv.id
    assert msg.created_at is not None


@pytest.mark.asyncio
async def test_cascade_delete_user_documents(async_session):
    """TRIANGULATE: Deleting a user cascades to documents."""
    user = User(email="cascade@example.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    doc = Document(
        user_id=user.id,
        filename="delete_test.pdf",
        file_type="pdf",
        file_size=500,
        status="ready",
    )
    async_session.add(doc)
    await async_session.commit()

    await async_session.delete(user)
    await async_session.commit()

    docs = await async_session.execute(
        select(Document).where(Document.user_id == user.id)
    )
    assert docs.scalars().all() == []


@pytest.mark.asyncio
async def test_cascade_delete_conversation_messages(async_session):
    """TRIANGULATE: Deleting a conversation cascades to messages."""
    user = User(email="cascade_msg@example.com", hashed_password="pw")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    conv = Conversation(user_id=user.id)
    async_session.add(conv)
    await async_session.commit()
    await async_session.refresh(conv)

    msg = Message(
        conversation_id=conv.id,
        role="user",
        content="test",
    )
    async_session.add(msg)
    await async_session.commit()

    await async_session.delete(conv)
    await async_session.commit()

    msgs = await async_session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    assert msgs.scalars().all() == []
