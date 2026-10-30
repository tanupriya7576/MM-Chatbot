from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import (
    SearchQueryRequest,
    SearchQueryResponse,
    SearchResultItem,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSourceItem
)
from app.services.search_service import search_service
from app.services.rag_service import rag_service
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Search & RAG"])

@router.post("/search", response_model=SearchQueryResponse)
async def perform_web_search(req: SearchQueryRequest):
    """
    Direct web search endpoint.
    """
    try:
        results = await search_service.search(query=req.query, max_results=req.max_results)
        items = [SearchResultItem(**r) for r in results]
        return SearchQueryResponse(query=req.query, results=items)
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/query", response_model=RAGQueryResponse)
async def perform_rag_query(req: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    Direct vector RAG retrieval endpoint.
    """
    try:
        chunks = await rag_service.retrieve_relevant_chunks(
            db=db,
            query=req.query,
            conversation_id=req.conversation_id,
            document_ids=req.document_ids,
            top_k=req.top_k or 4
        )
        context = rag_service.build_context_string(chunks)
        items = [RAGSourceItem(**c) for c in chunks]
        return RAGQueryResponse(query=req.query, context=context, sources=items)
    except Exception as e:
        logger.error(f"RAG API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
