# Backend: Multimodal AI Personal Assistant

This is the FastAPI backend service powering the Multimodal AI Personal Assistant.

## Features
- **FastAPI REST APIs** for chat, file uploads, document management, search, and health checks.
- **RAG Engine** with recursive chunking and vector similarity retrieval compatible with **PostgreSQL + pgvector** (and automatic SQLite fallback for zero-setup local runs).
- **Multi-provider LLM service** supporting Google Gemini (Gemini 1.5 Flash), OpenAI, and an offline mock fallback engine.
- **Web Search** via DuckDuckGo (free, zero API key required) and search APIs.
- **Document Creation & Updating** producing structured Microsoft Word (`.docx`) files.
- **Multimodal image understanding** for diagrams, photos, and screenshots.

## Quickstart

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your API keys (e.g., `LLM_API_KEY`) and database URL.
By default, `DATABASE_URL=sqlite:///./assistant.db` is configured so that the entire backend runs immediately without needing an external database installed.
To connect to PostgreSQL:
```env
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/multimodal_ai
```

### 4. Run Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) for the UI or [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger API documentation.

### 5. Running Tests
```bash
pytest tests/
```
