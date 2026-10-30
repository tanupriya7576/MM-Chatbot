# System Architecture: Multimodal AI Personal Assistant

## 1. High-Level Architecture Overview

The **Multimodal AI Personal Assistant** is designed with a clean, decoupled, and modular architecture. It connects a modern React frontend with a high-performance Python FastAPI backend, supported by PostgreSQL and vector similarity search.

```
┌─────────────────────────────────────────────────────────────┐
│                       React Frontend                        │
│  (Chat UI, Drag-and-Drop Upload, Modality Pills, Voice STT) │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (REST)                   │
│   /api/chat  /api/files  /api/documents  /api/conversations │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Orchestration Layer                   │
│                    (app/services/search_service)             │
│                      Query Classification                   │
└───────┬──────────────────────┼───────────────────────┬──────┘
        │                      │                       │
        ▼                      ▼                       ▼
┌──────────────┐       ┌──────────────┐        ┌──────────────┐
│  RAG Engine  │       │  Web Search  │        │   Document   │
│  Embeddings  │       │  Synthesis   │        │   Service    │
│  Vector Sim  │       │  DuckDuckGo  │        │   DOCX Gen   │
└───────┬──────┘       └───────┬──────┘        └───────┬──────┘
        │                      │                       │
        └──────────────────────┼───────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         LLM Service                         │
│            Gemini 1.5 Flash / OpenAI / Assistant            │
│               (Grounded Response + Citations)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                     │
│      conversations, messages, documents, document_chunks    │
│           (pgvector cosine vector similarity search)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Multimodal Input Processing
- **Text:** Direct user prompt ingestion through conversational API.
- **Images (`.png`, `.jpg`, `.jpeg`, `.webp`):** Processed via Pillow into normalized dimensions and encoded for Vision models (e.g., Gemini 1.5 Flash Vision / GPT-4o-mini).
- **Documents (`.pdf`, `.docx`, `.txt`, `.md`):** Extracted page-by-page or section-by-section using `pypdf` and `python-docx`.

### 2.2 RAG (Retrieval-Augmented Generation) Pipeline
1. **Document Upload:** User uploads a PDF, DOCX, or text file.
2. **Text Cleaning & Extraction:** Normalizes text, identifies page markers.
3. **Recursive Chunking:** Chunks text into ~800 character blocks with a 150 character sliding overlap to preserve context across boundaries.
4. **Vector Embeddings:** Generates embeddings (e.g. Gemini `text-embedding-004` or portable embeddings).
5. **Persistence:** Saves chunks, embeddings, and metadata into PostgreSQL.
6. **Query Retrieval:**
   - Computes query vector embedding.
   - Evaluates cosine similarity:
     $$\text{cosine\_similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$
   - Filters by conversation or document ID.
   - Retrieves top-$K$ chunks exceeding similarity threshold.
7. **Context Construction & Grounding:**
   - Pours excerpts into prompt with strict anti-hallucination system instructions.
   - LLM cites specific document chunks in its answer.

### 2.3 Web Search Orchestration
- **Intent Routing:** Automatically identifies temporal queries (e.g., "latest news", "current trends", "today", "search online") vs document questions.
- **Search Execution:** Queries DuckDuckGo without requiring paid API keys, returning structured results (titles, URLs, snippets).
- **Evidence Synthesis:** Incorporates web results into prompt context and formats clickable markdown citations.

### 2.4 Document Generation & Versioned Editing
- **Creation:** Generates structured `.docx` files complete with title headers, styled section headings, bulleted lists, and conclusions based on natural language instructions.
- **Updating:** Parses an existing document, applies requested changes via LLM, and creates a new versioned copy (`report_updated_xxxx.docx`) to guarantee non-destructive editing.

---

## 3. Database Schema

### `conversations`
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID) |
| `title` | VARCHAR(255) | Conversation title |
| `created_at` | TIMESTAMP | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | Last updated timestamp |

### `messages`
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID) |
| `conversation_id` | VARCHAR(36) | Foreign Key -> `conversations.id` |
| `role` | VARCHAR(32) | 'user', 'assistant', 'system' |
| `content` | TEXT | Message text |
| `metadata_json` | TEXT | JSON containing citations, query type, attached files |
| `created_at` | TIMESTAMP | Creation timestamp |

### `documents`
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID) |
| `conversation_id` | VARCHAR(36) | Foreign Key -> `conversations.id` (nullable) |
| `filename` | VARCHAR(255) | Original or generated filename |
| `file_type` | VARCHAR(64) | Extension / MIME type |
| `file_path` | VARCHAR(512) | Absolute path on disk |
| `file_size` | INTEGER | File size in bytes |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Update timestamp |

### `document_chunks`
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID) |
| `document_id` | VARCHAR(36) | Foreign Key -> `documents.id` |
| `chunk_index` | INTEGER | Sequential chunk index |
| `content` | TEXT | Text excerpt of the chunk |
| `embedding_json` | TEXT | Embedding vector array (compatible with pgvector) |
| `metadata_json` | TEXT | Page number, char count, etc. |
| `created_at` | TIMESTAMP | Ingestion timestamp |
