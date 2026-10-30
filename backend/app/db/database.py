import json
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.utils.logger import logger

# Determine if using SQLite or PostgreSQL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Engine options
engine_args = {}
if is_sqlite:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_pre_ping"] = True
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_engine(settings.DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and pgvector extension if available."""
    try:
        if not is_sqlite and "postgres" in settings.DATABASE_URL:
            # Attempt to create pgvector extension if PostgreSQL is used
            try:
                with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                logger.info("PostgreSQL pgvector extension verified/enabled.")
            except Exception as e:
                logger.warning(f"pgvector extension check failed (running without vector extension): {e}")

        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
