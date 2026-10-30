# Multimodal AI Personal Assistant

A modular, clean, and beginner-friendly **Multimodal AI Personal Assistant** that enables users to interact with artificial intelligence through multiple input and output modalities.

The assistant combines conversational intelligence, grounded document question-answering with **Retrieval-Augmented Generation (RAG)**, dynamic **Web Search**, multimodal **Image and Document Understanding**, and automated **Document Creation and Versioned Editing** (`.docx`).

---

## 1. Description

The Multimodal AI Personal Assistant is designed as a practical MVP that brings together key modern AI capabilities without unnecessary over-engineering:
- **Multimodal Interaction**: Chat via text, upload documents (PDF, DOCX, TXT), and analyze images (diagrams, charts, screenshots).
- **RAG (Retrieval-Augmented Generation)**: Answers questions grounded in uploaded documents with semantic vector search, citations, and anti-hallucination guardrails.
- **Web Search**: Automatically detects when external or real-time information is needed, searches the web, and returns answers with clickable source citations.
- **Document Creation & Updating**: Generates structured Microsoft Word (`.docx`) reports from instructions, or modifies existing documents while preserving originals through versioning.
- **Personal Assistant UX**: Conversation history, context preservation across turns, speech-to-text (voice input), and text-to-speech (voice output).

---

## 2. Features

### Implemented MVP Features
- [x] **Conversational Text Chat**: Natural language dialogue with session memory and multi-turn context.
- [x] **Multi-API Provider Failover (100% Free Tiers)**:
  - Priority 1: Google Gemini 3.5 Flash-Lite (Fast, vision OCR capable).
  - Priority 2: Google Gemini 3.8 Flash (Heavy reasoning).
  - Priority 3: OpenAI Client fallback.
  - Priority 4: Hugging Face Inference API fallback.
  - Priority 5: Offline Local Fallback.
- [x] **AI Image Generation**:
  - Photorealistic text-to-image synthesis using Pollinations AI (FLUX.1 model, 100% free, unlimited).
  - Saved locally with instant preview cards and full-resolution download links.
- [x] **Web Image Search**:
  - Searches and displays real photos of people, monuments, and places via DuckDuckGo Images and Wikimedia Commons API.
- [x] **Multimodal Input Support**:
  - **Images**: PNG, JPG, JPEG, WEBP processed via Pillow and multimodal vision models to solve questions, exam problems, and handwritten text.
  - **Documents**: PDF, DOCX, TXT, MD, CSV, JSON parsed with structure and page tracking.
- [x] **RAG Engine**:
  - Text extraction and cleaning.
  - Recursive chunking (~800 characters with 150-character overlap).
  - Embeddings generation (Google Gemini / text-embedding-004).
  - Vector similarity search (SQLite fallback and pgvector).
  - Top-$K$ retrieval with similarity scoring and grounding prompt.
  - Source citations display with snippet previews and match percentages.
- [x] **Real-Time Web Search Integration**:
  - Automatic query intent classification (Image Gen vs. Web Search vs. RAG vs. General).
  - Tavily AI Search integration (1,000 free searches) with DuckDuckGo fallback.
  - Source citations with clickable titles and URLs.
- [x] **Document Creation**:
  - Generates structured `.docx` reports with titles, headings, bullet points, and conclusions.
  - Direct download links for generated files.
- [x] **Document Updating**:
  - Modifies existing documents based on natural language instructions.
  - Creates versioned copies (`filename_updated_xxxx.docx`) to preserve original files.
- [x] **Voice Controls**:
  - Voice Speech-to-Text (STT) using native browser Web Speech API.
  - Voice Text-to-Speech (TTS) audio read-aloud button on assistant responses.
- [x] **Modern React UI**:
  - Sidebar with conversation drawer, new chat button, and system health badge.
  - Message stream with markdown formatting, syntax highlighting, image preview cards, and download chips.
  - Attachment tray with image previews and document icons.
  - Dedicated Document Assistant modal.
- [x] **Unified Deployment**:
  - FastAPI serves the unified React UI directly at `http://localhost:5173/` with zero Node.js build step needed.

### Future Improvements (Post-MVP)
- User authentication and multi-user tenancy.
- Long-term cross-session memory and user profiles.
- Native video ingestion and audio transcription via Whisper API.
- Direct export to PDF and PowerPoint (`.pptx`).
- Advanced autonomous multi-agent workflows.

---

## 3. Architecture

```text
┌──────────────────────────────────────────────┐
│                React Frontend                │
│   (Chat UI, Modality Pills, Voice STT/TTS)   │
└──────────────────────┬───────────────────────┘
                       │ HTTP REST / SSE Stream
                       ▼
┌──────────────────────────────────────────────┐
│            FastAPI Backend Service           │
│     /api/chat  /api/files  /api/documents    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│            AI Orchestration Layer            │
│             Query Classification             │
└──────┬───────────────┼───────────────┬───────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ RAG Engine  │ │ Web Search  │ │  Document   │
│ Vector Sim  │ │ DuckDuckGo  │ │   Service   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                 LLM Service                  │
│       Gemini 1.5 Flash / OpenAI / Mock       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             PostgreSQL + pgvector            │
│  (conversations, messages, documents, chunks)│
└──────────────────────────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | React 18, Tailwind CSS | Modern responsive UI, component architecture |
| **Backend** | Python 3.12, FastAPI | Asynchronous REST APIs, Pydantic validation |
| **Database** | PostgreSQL 15+ / SQLite | Persistent relational storage for chats and documents |
| **Vector Search** | pgvector / NumPy cosine | High-dimensional embedding storage and similarity search |
| **AI / LLM** | Google Gemini (1.5 Flash) / OpenAI | Multimodal reasoning, grounded generation, vision |
| **Embeddings** | Gemini `text-embedding-004` / Vectorizer | Document chunk semantic embeddings |
| **Web Search** | DuckDuckGo Search API | Free real-time web research |
| **Document Processing**| `python-docx`, `pypdf`, `Pillow` | Parsing and generating Word, PDF, and image assets |

---

## 5. Project Structure

```text
multimodal-ai-assistant/
│
├── frontend/
│   ├── public/
│   │   └── index.html               # Production standalone React 18 client
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          # Conversation list & system health
│   │   │   ├── MessageList.jsx      # Message stream & starter prompts
│   │   │   ├── MessageItem.jsx      # Message bubble, citations & TTS
│   │   │   ├── InputBar.jsx         # Textarea, file tray & voice STT
│   │   │   └── DocumentModal.jsx    # Document creator / updater modal
│   │   ├── services/
│   │   │   └── api.js               # REST client methods
│   │   ├── App.jsx                  # Root state orchestration
│   │   ├── index.css                # Tailwind directives & scrollbars
│   │   └── main.jsx                 # Vite mount entry
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js               # Vite dev configuration
│   └── README.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py              # Conversational & streaming endpoints
│   │   │   ├── files.py             # File upload and asset serving
│   │   │   ├── documents.py         # Document CRUD, creation & update
│   │   │   ├── search.py            # Direct search & RAG query routes
│   │   │   ├── conversations.py     # Conversation session CRUD
│   │   │   └── health.py            # Server health monitoring
│   │   ├── services/
│   │   │   ├── llm_service.py       # Multi-provider LLM abstraction
│   │   │   ├── rag_service.py       # Chunking, embeddings & vector search
│   │   │   ├── search_service.py    # Query routing & DuckDuckGo search
│   │   │   ├── document_service.py  # DOCX generation and editing
│   │   │   ├── multimodal_service.py# Image processing & document parsing
│   │   │   └── conversation_service.py # Session management
│   │   ├── db/
│   │   │   └── database.py          # SQLAlchemy engine & pgvector init
│   │   ├── models/
│   │   │   └── models.py            # Database tables
│   │   ├── schemas/
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   ├── utils/
│   │   │   ├── file_parser.py       # PDF/DOCX parsing & chunking logic
│   │   │   └── logger.py            # Structured logging
│   │   ├── config.py                # Environment configuration
│   │   └── main.py                  # FastAPI app & static mounting
│   ├── tests/
│   │   └── test_api.py              # Automated test suite
│   ├── uploads/                     # Uploaded documents and images
│   ├── generated/                   # Generated and updated DOCX files
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example
│   └── README.md
│
├── docs/
│   ├── architecture.md              # Detailed architecture documentation
│   └── api.md                       # Comprehensive API reference
│
├── .env.example                     # Root environment variable template
├── .gitignore
└── README.md
```

---

## 6. Prerequisites

- **Python**: Version 3.10, 3.11, or 3.12.
- **Node.js** (Optional): Version 18+ (only needed if running the standalone Vite dev server).
- **PostgreSQL** (Recommended): Version 15+ with the `pgvector` extension.
  - *Note: If PostgreSQL is not installed locally, the backend automatically uses SQLite so you can test immediately without any setup friction.*
- **API Keys** (Optional for offline testing, recommended for production AI):
  - Google Gemini API Key (`GEMINI_API_KEY`) or OpenAI API Key (`OPENAI_API_KEY`).

---

## 7. Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/multimodal-ai-assistant.git
cd multimodal-ai-assistant
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows):
.\venv\Scripts\activate

# Activate virtual environment (macOS/Linux):
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup (PostgreSQL with pgvector)
Create a PostgreSQL database:
```sql
CREATE DATABASE multimodal_ai;
\c multimodal_ai;
CREATE EXTENSION IF NOT EXISTS vector;
```

Configure your connection string in `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/multimodal_ai
```

*(If you want to run with SQLite first, simply leave `DATABASE_URL=sqlite:///./assistant.db`)*

### 4. Frontend Setup (Optional Vite Server)
If you wish to use the Vite development server:
```bash
cd ../frontend
npm install
npm run dev
```

---

## 8. Environment Variables

Create `.env` inside the `backend/` directory by copying `.env.example`:

```env
# LLM Provider Configuration
# Options: gemini, openai, mock
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

# Embeddings Model Configuration
# Options: gemini, local
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/text-embedding-004

# Web Search Configuration
# Options: duckduckgo (free, no key required), tavily, serpapi
SEARCH_ENGINE=duckduckgo
SEARCH_API_KEY=

# Database Configuration
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/multimodal_ai
# DATABASE_URL=sqlite:///./assistant.db

# Storage & File Limits
UPLOAD_DIR=./uploads
GENERATED_DIR=./generated
MAX_FILE_SIZE_MB=20

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=*
```

---

## 9. Running the Application

### Option A: Complete App with Zero-Node Setup (Recommended)
Start the FastAPI server:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.
The full React 18 interface will load immediately with complete functionality!

### Option B: Running with Separate Vite Frontend
1. **Start Backend**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```
2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open **[http://localhost:5173](http://localhost:5173)**.

---

## 10. API Documentation

FastAPI provides interactive Swagger documentation out of the box:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Detailed Reference**: See [docs/api.md](docs/api.md) for curl examples and schemas.

---

## 11. Core Workflows

### RAG Workflow
```text
Upload Document (PDF / DOCX / TXT)
       ↓
Validation & Size Checks
       ↓
Text & Section Extraction
       ↓
Recursive Chunking (~800 chars, 150 overlap)
       ↓
Generate Vector Embeddings
       ↓
Store Chunks & Embeddings in Database
       ↓
User Question
       ↓
Compute Query Embedding
       ↓
Vector Cosine Similarity Search
       ↓
Retrieve Top-K Chunks
       ↓
Construct Grounded Context Prompt
       ↓
LLM Synthesizes Answer
       ↓
Display Response + Evidence Citations
```

### Web Search Workflow
```text
User Query
       ↓
Query Classifier (Detects temporal / external inquiry)
       ↓
DuckDuckGo Search Engine Execution
       ↓
Extract Titles, URLs & Snippets
       ↓
LLM Evidence Synthesis
       ↓
Display Answer + Clickable Sources
```

### Document Creation & Updating Workflow
```text
User Instruction (e.g. "Create a report on AI" / "Add conclusion to attached doc")
       ↓
Intent Classifier routes to Document Action
       ↓
LLM produces structured markdown outline
       ↓
python-docx renders styled Word document (.docx)
       ↓
Save to disk (generated/) and register in Database
       ↓
Provide download button in chat
```

---

## 12. Limitations

- **Authentication**: Designed for a single-user / single-session MVP. No user accounts or role permissions are implemented.
- **File Formats**: Currently supports PDF, DOCX, TXT, MD, CSV, JSON, PNG, JPG, and WEBP. Specialized formats (e.g., spreadsheets with macros, proprietary CAD files) are not supported.
- **Session Memory**: Context is preserved within the active conversation. Long-term cross-session knowledge bases are not implemented.
- **Voice Capabilities**: Relies on standard browser Web Speech APIs (`webkitSpeechRecognition` & `speechSynthesis`), which require a modern browser (Google Chrome or Microsoft Edge recommended).

---

## 13. Disclaimer

This application is built for educational, research, and developer demonstration purposes. AI models can occasionally produce inaccurate or incomplete information. Users should independently verify facts retrieved from web searches or document syntheses when precision is critical.
