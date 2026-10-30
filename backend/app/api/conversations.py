import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Conversation, Message
from app.schemas.schemas import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreate,
    MessageResponse
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return ConversationService.list_conversations(db)

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(req: ConversationCreate, db: Session = Depends(get_db)):
    conv = ConversationService.get_or_create_conversation(db, title=req.title)
    return conv

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_detail(conversation_id: str, db: Session = Depends(get_db)):
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Format messages and metadata
    formatted_messages = []
    for m in conv.messages:
        meta = {}
        if m.metadata_json:
            try:
                meta = json.loads(m.metadata_json)
            except Exception:
                pass
        formatted_messages.append(
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                metadata_json=m.metadata_json,
                metadata=meta,
                created_at=m.created_at
            )
        )

    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=formatted_messages,
        documents=conv.documents
    )

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    success = ConversationService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully", "id": conversation_id}
