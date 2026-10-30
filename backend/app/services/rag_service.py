import json
import math
try:
    import numpy as np
except ImportError:
    np = None
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import Document, DocumentChunk
from app.utils.file_parser import chunk_text, extract_text_from_file
from app.utils.logger import logger

class RAGService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.model_name = settings.EMBEDDING_MODEL

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding vector for a given text snippet.
        Supports Gemini, OpenAI, or deterministic local vector generation.
        """
        text = text.replace("\n", " ").strip()
        if not text:
            return [0.0] * 64

        # 1. Gemini Embedding
        if self.gemini_key:
            try:
                try:
                    from google import genai
                    client = genai.Client(api_key=self.gemini_key)
                    result = client.models.embed_content(
                        model="text-embedding-004",
                        contents=text
                    )
                    if hasattr(result, "embedding") and result.embedding:
                        return list(result.embedding.values)
                    if hasattr(result, "embeddings") and result.embeddings:
                        return list(result.embeddings[0].values)
                except ImportError:
                    import google.generativeai as genai
                    genai.configure(api_key=self.gemini_key)
                    result = genai.embed_content(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embedding = result.get("embedding", [])
                    if embedding:
                        return embedding
            except Exception as e:
                logger.warning(f"Gemini embedding error: {e}. Falling back to deterministic embedding.")

        # 2. OpenAI Embedding
        if self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding error: {e}. Falling back to deterministic embedding.")

        # 3. Deterministic Local Embedding Fallback
        return self._generate_local_embedding(text)

    def _generate_local_embedding(self, text: str, dim: int = 128) -> List[float]:
        """
        Deterministic hash-based frequency embedding vector for offline testing.
        Normalized to unit length for accurate cosine similarity.
        """
        vec = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h = hash(word) % dim
            vec[h] += 1.0

        # Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def index_document(self, db: Session, document: Document) -> int:
        """
        Extracts, chunks, embeds, and saves chunks for a document.
        Returns the number of indexed chunks.
        """
        logger.info(f"Indexing document: {document.filename} (ID: {document.id})")
        full_text, sections = extract_text_from_file(document.file_path)

        if not full_text.strip():
            logger.warning(f"No text extracted from document {document.filename}")
            return 0

        # Split text into chunks
        chunks = chunk_text(
            full_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )

        logger.info(f"Created {len(chunks)} chunks for {document.filename}")

        # Delete any existing chunks for this document
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()

        # Generate embeddings and store chunks
        for idx, chunk_content in enumerate(chunks):
            embedding = await self.get_embedding(chunk_content)
            chunk_obj = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_content,
                embedding_json=json.dumps(embedding),
                metadata_json=json.dumps({
                    "filename": document.filename,
                    "chunk_index": idx,
                    "char_count": len(chunk_content)
                })
            )
            db.add(chunk_obj)

        db.commit()
        logger.info(f"Successfully indexed {len(chunks)} chunks for {document.filename}")
        return len(chunks)

    async def retrieve_relevant_chunks(
        self,
        db: Session,
        query: str,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Computes query embedding, queries vector database, and returns top-K relevant chunks.
        """
        query_embedding = await self.get_embedding(query)
        if np is not None:
            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = float(np.linalg.norm(q_vec))
        else:
            q_vec = query_embedding
            q_norm = math.sqrt(sum(x * x for x in q_vec))

        if q_norm == 0:
            return []

        # Query candidates from DB
        query_builder = db.query(DocumentChunk).join(Document)
        if document_ids:
            query_builder = query_builder.filter(Document.id.in_(document_ids))
        elif conversation_id:
            query_builder = query_builder.filter(
                (Document.conversation_id == conversation_id) | (Document.conversation_id.is_(None))
            )

        candidate_chunks = query_builder.all()
        if not candidate_chunks:
            return []

        scored_chunks: List[Tuple[float, DocumentChunk, str]] = []

        for chunk in candidate_chunks:
            if not chunk.embedding_json:
                continue
            try:
                emb_list = json.loads(chunk.embedding_json)
                if np is not None:
                    c_emb = np.array(emb_list, dtype=np.float32)
                    c_norm = float(np.linalg.norm(c_emb))
                    score = float(np.dot(q_vec, c_emb) / (q_norm * c_norm)) if c_norm > 0 else 0.0
                else:
                    c_norm = math.sqrt(sum(x * x for x in emb_list))
                    dot = sum(x * y for x, y in zip(q_vec, emb_list))
                    score = float(dot / (q_norm * c_norm)) if c_norm > 0 else 0.0

                # Also boost if literal keywords match in content
                keywords = [k for k in query.lower().split() if len(k) > 3]
                match_boost = sum(0.05 for kw in keywords if kw in chunk.content.lower())
                total_score = score + min(match_boost, 0.2)

                scored_chunks.append((total_score, chunk, chunk.document.filename if chunk.document else "document"))
            except Exception as e:
                logger.error(f"Error computing similarity for chunk {chunk.id}: {e}")

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_chunks[:top_k]

        results = []
        for score, chunk, filename in top_matches:
            results.append({
                "document_id": chunk.document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "score": round(score, 4)
            })

        return results

    def build_context_string(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Constructs context block for the LLM prompt.
        """
        if not chunks:
            return ""

        context_parts = []
        for c in chunks:
            context_parts.append(
                f"[Source: {c['filename']} | Chunk #{c['chunk_index']} | Score: {c['score']}]:\n"
                f"{c['content']}\n"
            )
        return "\n".join(context_parts)

rag_service = RAGService()
