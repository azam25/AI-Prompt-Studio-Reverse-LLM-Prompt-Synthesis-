"""Document models for AI Prompt Studio."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "md"


class DocumentChunk(BaseModel):
    """A chunk of a document with its embedding."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict = Field(default_factory=dict)


class Document(BaseModel):
    """A document uploaded to the system."""
    id: str
    filename: str
    document_type: DocumentType
    file_path: str
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: str
    filename: str
    document_type: str
    chunk_count: int
    message: str


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: List[Document]
    total: int


class RetrievedContext(BaseModel):
    """Context retrieved from vector store."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)
