"""Document management API endpoints: upload, list, delete."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.db.chroma import get_chroma_collection
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _validate_file(file: UploadFile) -> tuple[str, str]:
    """Validate the uploaded file's type and extension.

    Returns
    -------
    tuple[str, str]
        ``(file_extension, file_type)`` – the validated extension and type.

    Raises
    ------
    HTTPException
        If the file type is unsupported.
    """
    # Validate by extension
    ext = ""
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()

    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate by MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo MIME del archivo no soportado.",
        )

    type_map = {"pdf": "pdf", "docx": "docx", "xlsx": "xlsx"}
    return ext, type_map[ext]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for processing.

    Accepts PDF, DOCX, and XLSX files up to 10 MB. Maximum 4 files per user.
    """
    # Validate file type
    ext, file_type = _validate_file(file)

    # Validate file size
    contents = await file.read()
    file_size = len(contents)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {settings.max_upload_size_mb} MB.",
        )

    # Check file count limit
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id)
    )
    existing_docs = result.scalars().all()
    if len(existing_docs) >= settings.max_files_per_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Límite de {settings.max_files_per_user} documentos alcanzado.",
        )

    # Determine filename (avoid duplicates by appending counter)
    filename = file.filename or f"document.{ext}"
    base_dir = Path(settings.upload_dir) / current_user.id
    base_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = filename
    # If filename already exists in user's docs, prepend a counter
    existing_names = {d.filename for d in existing_docs}
    counter = 1
    while stored_filename in existing_names:
        name_parts = filename.rsplit(".", 1)
        stored_filename = f"{name_parts[0]}_{counter}.{ext}"
        counter += 1

    # Save file
    file_path = base_dir / f"{uuid.uuid4().hex}_{stored_filename}"
    file_path.write_bytes(contents)

    # Create Document record
    document = Document(
        user_id=current_user.id,
        filename=stored_filename,
        file_type=file_type,
        file_size=file_size,
        file_path=str(file_path),
        status="processing",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Launch processing (synchronous for small files in dev)
    chroma_collection = get_chroma_collection()
    await process_document(
        user_id=current_user.id,
        document_id=document.id,
        file_path=str(file_path),
        file_type=file_type,
        filename=stored_filename,
        db=db,
        chroma_collection=chroma_collection,
    )

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the authenticated user, newest first."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
        )
        for doc in docs
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document, its file on disk, and its chunks from ChromaDB.

    Returns 404 if the document does not exist or belongs to another user.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        )

    # Remove from ChromaDB
    try:
        chroma_collection = get_chroma_collection()
        chroma_collection.delete(where={"document_id": document.id})
    except Exception:
        # ChromaDB might not have the data; continue
        pass

    # Delete file from disk
    if document.file_path:
        try:
            os.unlink(document.file_path)
        except FileNotFoundError:
            pass

    # Delete DB record
    await db.delete(document)
    await db.flush()

    return {"detail": "Documento eliminado correctamente."}
