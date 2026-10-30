import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal AI Personal Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 5173
    CORS_ORIGINS: str = "*"

    # Multi-API Keys Configuration (Leave blank if not available)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # Primary and fallback providers
    LLM_PROVIDER: str = "auto"  # auto rotates: gemini -> openai -> huggingface -> mock
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    
    # Embedding settings
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Web Search Settings
    SEARCH_ENGINE: str = "auto"  # auto chooses: tavily (if key provided) -> duckduckgo (free & keyless)
    SEARCH_API_KEY: str = ""
    SEARCH_MAX_RESULTS: int = 5

    # Database settings
    # Default is SQLite for instant zero-config startup; easily configured for PostgreSQL + pgvector
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'assistant.db'}"

    # File Storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    GENERATED_DIR: str = str(BASE_DIR / "generated")
    MAX_FILE_SIZE_MB: int = 20

    # RAG Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_RETRIEVAL: int = 4
    SIMILARITY_THRESHOLD: float = 0.3

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.GENERATED_DIR, exist_ok=True)
