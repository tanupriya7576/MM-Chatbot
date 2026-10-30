import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from app.config import settings, BASE_DIR
from app.db.database import init_db
from app.utils.logger import logger

# Import API Routers
from app.api.health import router as health_router
from app.api.conversations import router as conversations_router
from app.api.files import router as files_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables and Directories
    logger.info("Starting up Multimodal AI Assistant backend...")
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.GENERATED_DIR, exist_ok=True)
    yield
    # Shutdown
    logger.info("Shutting down Multimodal AI Assistant backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multimodal AI Personal Assistant API with RAG, Web Search, Vision, and Document Management",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs for details."}
    )

# Include API Routers
app.include_router(health_router)
app.include_router(conversations_router)
app.include_router(files_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)

# Mount Static Directories for uploads and generated documents
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=settings.GENERATED_DIR), name="generated")

# Mount Frontend static assets and index.html if available
frontend_dist = BASE_DIR.parent / "frontend" / "dist"
frontend_static = BASE_DIR.parent / "frontend" / "public"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    @app.get("/")
    def serve_frontend_dist():
        return FileResponse(str(frontend_dist / "index.html"))

elif frontend_static.exists():
    # If using standalone browser-executable React without Node build step
    app.mount("/static", StaticFiles(directory=str(frontend_static)), name="static")
    @app.get("/")
    @app.get("/chat")
    @app.get("/app")
    def serve_frontend_public():
        return FileResponse(str(frontend_static / "index.html"))

@app.get("/api")
def api_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
