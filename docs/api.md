# API Documentation: Multimodal AI Personal Assistant

Base URL: `http://localhost:8000`

Interactive OpenAPI / Swagger Docs: `http://localhost:8000/docs`

---

## 1. System Health

### `GET /health`
Returns the operational status of the server, database connection, LLM provider, and search engine.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "llm_provider": "gemini",
  "search_engine": "duckduckgo"
}
```

---

## 2. Chat & Multimodal Interaction

### `POST /api/chat`
Main conversational endpoint orchestrating general query processing, RAG, Web Search, Vision, and Document generation.

**Request Body**:
```json
{
  "message": "What does my uploaded report say about transformer architecture?",
  "conversation_id": "optional-uuid-here",
  "attached_file_ids": ["doc-uuid-1"],
  "enable_web_search": false,
  "enable_rag": true
}
```

**Response `200 OK`**:
```json
{
  "conversation_id": "c4b8e21a-...",
  "response": "According to page 4 of the uploaded report, transformers utilize self-attention mechanisms...",
  "query_type": "rag",
  "sources": [
    {
      "type": "document",
      "title": "report.pdf",
      "chunk": 2,
      "score": 0.84,
      "snippet": "Self-attention computes representations of a single sequence..."
    }
  ],
  "created_document": null
}
```

### `POST /api/chat/stream`
Server-Sent Events (SSE) streaming endpoint for real-time assistant responses.

---

## 3. File Management

### `POST /api/files/upload`
Uploads an image, PDF, DOCX, or text file. Text documents are automatically chunked and indexed into the vector database.

**Form Data**:
- `file`: Binary file upload
- `conversation_id`: (optional) string UUID

**Response `201 Created`**:
```json
{
  "id": "e817a32b-...",
  "filename": "market_research.pdf",
  "file_type": "pdf",
  "file_size": 245100,
  "created_at": "2026-10-15T12:00:00Z",
  "updated_at": "2026-10-15T12:00:00Z",
  "conversation_id": "c4b8e21a-...",
  "chunks_count": 8
}
```

### `GET /api/files/{filename}`
Retrieves an uploaded file or image preview.

---

## 4. Document Operations

### `GET /api/documents`
Lists uploaded and generated documents.

### `GET /api/documents/{id}/download`
Downloads the requested document file.

### `POST /api/documents/create`
Generates a structured DOCX report from natural language instructions.

**Request Body**:
```json
{
  "title": "Quantum Computing 2026",
  "instructions": "Include introduction, 3 major breakthroughs, and a conclusion.",
  "file_format": "docx"
}
```

**Response `200 OK`**:
```json
{
  "document_id": "93a10df1-...",
  "filename": "Quantum_Computing_2026_a81f9b.docx",
  "file_path": ".../backend/generated/Quantum_Computing_2026_a81f9b.docx",
  "download_url": "/api/documents/93a10df1-.../download",
  "message": "Successfully created document 'Quantum Computing 2026' as a downloadable DOCX."
}
```

### `POST /api/documents/{id}/update`
Applies requested modifications to an existing document, creating an updated version.

---

## 5. Web Search & Direct RAG

### `POST /api/search`
Queries DuckDuckGo and returns structured web sources.

**Request Body**:
```json
{
  "query": "latest multimodal AI models",
  "max_results": 5
}
```

### `POST /api/rag/query`
Direct vector similarity query across indexed documents.

**Request Body**:
```json
{
  "query": "convolutional neural networks",
  "conversation_id": "optional-uuid",
  "top_k": 4
}
```

---

## 6. Conversations

### `GET /api/conversations`
Lists all active conversation sessions.

### `POST /api/conversations`
Creates a new conversation session.

### `GET /api/conversations/{id}`
Retrieves messages and attached documents for a session.

### `DELETE /api/conversations/{id}`
Deletes a conversation and its messages.
