"""Integration tests for document API endpoints."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import create_access_token


@pytest.fixture
async def user_token(client):
    """Register a test user and return a valid JWT."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": "doc-test@example.com", "password": "SecurePass123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.fixture(autouse=True)
def chroma_mock():
    """Mock ChromaDB collection globally so real ChromaDB is never needed."""
    coll = MagicMock()
    patcher = patch("app.api.documents.get_chroma_collection", return_value=coll)
    patcher.start()
    yield coll
    patcher.stop()


class TestUploadDocument:
    """RED→GREEN→REFACTOR: POST /api/documents/upload."""

    @pytest.mark.asyncio
    async def test_upload_pdf_success(self, client, user_token):
        """GIVEN a valid PDF WHEN upload THEN 201 with processing status."""
        with patch("app.api.documents.process_document", new=AsyncMock()):
            pdf_bytes = b"%PDF-1.4 fake pdf content for testing"
            response = await client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                headers={"Authorization": f"Bearer {user_token}"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "processing"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_upload_rejects_too_large(self, client, user_token):
        """GIVEN a file >10 MB WHEN upload THEN 413."""
        big_data = b"x" * (11 * 1024 * 1024)
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("big.pdf", io.BytesIO(big_data), "application/pdf")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_type(self, client, user_token):
        """GIVEN a .txt file WHEN upload THEN 400."""
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client):
        """GIVEN no auth WHEN upload THEN 401."""
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_rejects_excess_files(self, client, user_token):
        """GIVEN user with 4+ docs WHEN upload THEN 409."""
        for i in range(4):
            with patch("app.api.documents.process_document", new=AsyncMock()):
                resp = await client.post(
                    "/api/documents/upload",
                    files={"file": (f"doc{i}.pdf", io.BytesIO(b"data"), "application/pdf")},
                    headers={"Authorization": f"Bearer {user_token}"},
                )
                assert resp.status_code == 201

        response = await client.post(
            "/api/documents/upload",
            files={"file": ("extra.pdf", io.BytesIO(b"data"), "application/pdf")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_upload_runs_processing(self, client, user_token):
        """GIVEN a valid upload WHEN done THEN process_document is called."""
        with patch("app.api.documents.process_document", new=AsyncMock()) as mock_proc:
            pdf_bytes = b"%PDF-1.4 test"
            response = await client.post(
                "/api/documents/upload",
                files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 201
            mock_proc.assert_awaited_once()


class TestListDocuments:
    """RED→GREEN→REFACTOR: GET /api/documents."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client, user_token):
        """GIVEN no documents WHEN list THEN 200 with empty array."""
        response = await client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_with_documents(self, client, user_token):
        """GIVEN 2 documents WHEN list THEN 200 with 2 items."""
        with patch("app.api.documents.process_document", new=AsyncMock()):
            for i in range(2):
                await client.post(
                    "/api/documents/upload",
                    files={"file": (f"doc{i}.pdf", io.BytesIO(b"data"), "application/pdf")},
                    headers={"Authorization": f"Bearer {user_token}"},
                )
        response = await client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestDeleteDocument:
    """RED→GREEN→REFACTOR: DELETE /api/documents/{id}."""

    @pytest.mark.asyncio
    async def test_delete_existing(self, client, user_token):
        """GIVEN an existing document WHEN delete THEN 200."""
        with patch("app.api.documents.process_document", new=AsyncMock()):
            create_resp = await client.post(
                "/api/documents/upload",
                files={"file": ("del.pdf", io.BytesIO(b"data"), "application/pdf")},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            doc_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, client, user_token):
        """GIVEN a non-existent ID WHEN delete THEN 404."""
        response = await client.delete(
            "/api/documents/nonexistent-id",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_document(self, client):
        """GIVEN a document from user A WHEN user B deletes THEN 404."""
        with patch("app.api.documents.process_document", new=AsyncMock()):
            resp_a = await client.post(
                "/api/auth/register",
                json={"email": "usera@test.com", "password": "Pass1234"},
            )
            assert resp_a.status_code == 201
            token_a = resp_a.json()["access_token"]
            upload_resp = await client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            doc_id = upload_resp.json()["id"]

        resp_b = await client.post(
            "/api/auth/register",
            json={"email": "userb@test.com", "password": "Pass5678"},
        )
        token_b = resp_b.json()["access_token"]
        response = await client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404
