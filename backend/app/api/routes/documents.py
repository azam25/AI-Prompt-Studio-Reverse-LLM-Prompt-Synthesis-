"""Document API routes."""
import os
import uuid
import shutil
from typing import List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from app.config import settings
from app.models.document import (
    Document,
    DocumentUploadResponse,
    DocumentListResponse
)
from app.services.document_processor import get_document_processor
from app.services.vector_store import get_vector_store

router = APIRouter()

# In-memory document store (in production, use a database)
documents_store: dict[str, Document] = {}


def ensure_upload_dir():
    """Ensure upload directory exists."""
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a document and process it for embedding.
    
    Supports: PDF, DOCX, TXT, Markdown files.
    """
    ensure_upload_dir()
    
    # Validate file type
    filename = file.filename
    ext = Path(filename).suffix.lower()
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown'}
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, f"{file_id}{ext}")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process document
    try:
        processor = get_document_processor()
        document, chunks = processor.process_file(file_path, filename)
        
        # Add to vector store
        vector_store = get_vector_store()
        chunk_count = vector_store.add_chunks(chunks)
        
        # Store document metadata
        documents_store[document.id] = document
        
        return DocumentUploadResponse(
            id=document.id,
            filename=filename,
            document_type=document.document_type.value,
            chunk_count=chunk_count,
            message=f"Successfully processed {filename} into {chunk_count} chunks"
        )
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    docs = list(documents_store.values())
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    return documents_store[document_id]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = documents_store[document_id]
    
    # Remove from vector store
    vector_store = get_vector_store()
    deleted_chunks = vector_store.delete_document(document_id)
    
    # Remove file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Remove from store
    del documents_store[document_id]
    
    return {
        "message": f"Deleted document {document.filename}",
        "deleted_chunks": deleted_chunks
    }


@router.delete("/")
async def clear_all_documents():
    """Clear all documents and embeddings."""
    # Clear vector store
    vector_store = get_vector_store()
    vector_store.clear()
    
    # Delete all files
    for doc in documents_store.values():
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    
    # Clear store
    count = len(documents_store)
    documents_store.clear()
    
    return {"message": f"Cleared {count} documents"}


@router.get("/stats")
async def get_stats():
    """Get document and vector store statistics."""
    vector_store = get_vector_store()
    stats = vector_store.get_stats()
    stats["documents"] = len(documents_store)
    return stats
