"""Document-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document metadata returned to the client."""

    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: Optional[int] = None
    created_at: datetime
