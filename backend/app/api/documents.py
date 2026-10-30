import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Document as DBDocument, DocumentChunk
from app.schemas.schemas import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentActionResponse
)
from app.services.document_service import document_service
from app.utils.logger import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    conversation_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DBDocument)
    if conversation_id:
        query = query.filter((DBDocument.conversation_id == conversation_id) | (DBDocument.conversation_id.is_(None)))
    docs = query.order_by(DBDocument.created_at.desc()).all()
    
    results = []
    for d in docs:
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).count()
        results.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                file_size=d.file_size,
                created_at=d.created_at,
                updated_at=d.updated_at,
                conversation_id=d.conversation_id,
                chunks_count=chunk_count
            )
        )
    return results

@router.get("/{document_id}")
def get_document_detail(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    return {
        "document": DocumentResponse.model_validate(doc),
        "chunks": [DocumentChunkResponse.model_validate(c) for c in chunks]
    }

@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

@router.post("/create", response_model=DocumentActionResponse)
async def create_document(req: DocumentCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a formatted document (DOCX) from instructions and saves it.
    """
    try:
        result = await document_service.create_document(
            db=db,
            title=req.title,
            instructions=req.instructions,
            conversation_id=req.conversation_id,
            file_format=req.file_format or "docx"
        )
        return DocumentActionResponse(**result)
    except Exception as e:
        logger.error(f"Document creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/update", response_model=DocumentActionResponse)
async def update_document(
    document_id: str,
    req: DocumentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Modifies an existing document according to instructions, saving an updated version.
    """
    try:
        result = await document_service.update_document(
            db=db,
            document_id=document_id,
            modification_instructions=req.instructions,
            conversation_id=req.conversation_id
        )
        return DocumentActionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Document update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
