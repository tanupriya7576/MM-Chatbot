import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Conversation, Message, Document
from app.utils.logger import logger

class ConversationService:
    @staticmethod
    def get_or_create_conversation(db: Session, conversation_id: Optional[str] = None, title: Optional[str] = None) -> Conversation:
        if conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                return conv
            logger.info(f"Conversation {conversation_id} not found. Creating a new one.")

        new_conv = Conversation(title=title or "New Conversation")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        return new_conv

    @staticmethod
    def list_conversations(db: Session, limit: int = 50) -> List[Conversation]:
        return db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(limit).all()

    @staticmethod
    def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def delete_conversation(db: Session, conversation_id: str) -> bool:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        metadata_str = json.dumps(metadata or {})
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_json=metadata_str
        )
        db.add(msg)
        
        # Update conversation's updated_at timestamp
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            from datetime import datetime, timezone
            conv.updated_at = datetime.now(timezone.utc)
            # Update title from first user message if default
            if conv.title == "New Conversation" and role == "user":
                summary = content.strip().split("\n")[0][:40]
                if summary:
                    conv.title = summary

        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_history(db: Session, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Returns recent message history formatted for LLM context."""
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        # Limit to the last N messages
        recent = messages[-limit:] if len(messages) > limit else messages
        history = []
        for m in recent:
            history.append({
                "role": m.role,
                "content": m.content
            })
        return history
