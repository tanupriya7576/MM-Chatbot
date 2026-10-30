from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Health Schema ---
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm_provider: str
    search_engine: str

# --- Message Schemas ---
class MessageBase(BaseModel):
    role: str
    content: str
    metadata_json: Optional[str] = "{}"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Document & Chunk Schemas ---
class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    conversation_id: Optional[str] = None
    chunks_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Conversation Schemas ---
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True

# --- Search Schemas ---
class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str

class SearchQueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class SearchQueryResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

# --- RAG Schemas ---
class RAGSourceItem(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float

class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 4

class RAGQueryResponse(BaseModel):
    query: str
    context: str
    sources: List[RAGSourceItem]

# --- Document Action Schemas ---
class DocumentCreateRequest(BaseModel):
    title: str
    instructions: str
    conversation_id: Optional[str] = None
    file_format: Optional[str] = "docx"  # "docx" or "txt"

class DocumentUpdateRequest(BaseModel):
    instructions: str
    conversation_id: Optional[str] = None

class DocumentActionResponse(BaseModel):
    document_id: str
    filename: str
    file_path: str
    download_url: str
    message: str

# --- Chat Request & Response Schemas ---
class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    attached_file_ids: Optional[List[str]] = Field(default=[], description="Uploaded file IDs")
    enable_web_search: Optional[bool] = Field(None, description="Force enable/disable web search")
    enable_rag: Optional[bool] = Field(None, description="Force enable/disable RAG")

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    query_type: str  # 'general', 'rag', 'web_search', 'hybrid', 'document_creation', 'document_update'
    sources: List[Dict[str, Any]] = []
    created_document: Optional[Dict[str, Any]] = None
