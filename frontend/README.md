# Frontend: Multimodal AI Personal Assistant

This is the React frontend for the Multimodal AI Personal Assistant.

## Features
- **Modern Responsive Chat Interface** with dark theme and card styling.
- **Message History** with Markdown rendering, tables, code blocks, and timestamps.
- **Multimodal File Upload Tray** supporting images (with previews), PDFs, DOCX, and text files.
- **RAG & Web Search Citations Drawer** showing match scores and external links.
- **Voice Speech-to-Text (STT)** input via the Web Speech API.
- **Voice Text-to-Speech (TTS)** audio read-aloud button on assistant messages.
- **Document Creation & Updating Modal** to generate and modify downloadable Word documents.
- **Zero-Node Execution Option:** The frontend is also served directly by FastAPI at `http://localhost:8000/` using modern in-browser React 18, so you can run the full UI without installing Node.js.

## Running with Node & Vite (Optional)

If you have Node.js installed:

```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.
API calls are automatically proxied to the backend at `http://localhost:8000`.
