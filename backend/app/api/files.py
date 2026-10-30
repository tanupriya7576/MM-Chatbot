import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.db.database import get_db
from app.models.models import Document as DBDocument
from app.schemas.schemas import DocumentResponse
from app.services.rag_service import rag_service
from app.utils.file_parser import is_allowed_file, is_document_file, is_image_file
from app.utils.logger import logger

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Uploads an image, PDF, DOCX, or text file.
    Validates file extension and size, saves file, and indexes document for RAG.
    """
    filename = file.filename or "uploaded_file"
    if not is_allowed_file(filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for '{filename}'. Allowed: PDF, DOCX, TXT, MD, CSV, PNG, JPG, WEBP."
        )

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    safe_name = f"{uuid.uuid4().hex[:8]}_{filename.replace(' ', '_')}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    # Read and check size
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size limit of {settings.MAX_FILE_SIZE_MB}MB."
        )

    # Save to disk
    with open(save_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = DBDocument(
        filename=filename,
        file_type=ext,
        file_path=save_path,
        file_size=len(content),
        conversation_id=conversation_id if conversation_id and conversation_id.strip() else None
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks_count = 0
    # If file is a textual document, automatically index chunks into vector database for RAG
    if is_document_file(filename):
        try:
            chunks_count = await rag_service.index_document(db, doc)
        except Exception as e:
            logger.error(f"Failed to index document {filename} for RAG: {e}")

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        conversation_id=doc.conversation_id,
        chunks_count=chunks_count
    )

@router.get("/{filename}")
def get_uploaded_file(filename: str):
    """Serve uploaded file securely."""
    safe_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path)
