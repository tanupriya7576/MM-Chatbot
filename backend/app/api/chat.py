import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Document as DBDocument
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.conversation_service import ConversationService
from app.services.llm_service import llm_service
from app.services.multimodal_service import multimodal_service
from app.services.rag_service import rag_service
from app.services.search_service import search_service
from app.services.document_service import document_service
from app.services.image_gen_service import image_gen_service
from app.utils.file_parser import is_image_file, is_document_file
from app.utils.logger import logger

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Main multimodal conversational endpoint.
    Orchestrates routing between General LLM, Document RAG, Web Search, Vision, and Document Actions.
    """
    try:
        # 1. Get or create conversation
        conv = ConversationService.get_or_create_conversation(db, conversation_id=req.conversation_id)
        conv_id = conv.id

        # 2. Inspect attached files
        attached_docs = []
        attached_images = []
        if req.attached_file_ids:
            files_db = db.query(DBDocument).filter(DBDocument.id.in_(req.attached_file_ids)).all()
            for f in files_db:
                if is_image_file(f.filename):
                    attached_images.append(f)
                else:
                    attached_docs.append(f)

        # 3. Route user query
        query_type = search_service.classify_query(
            query=req.message,
            has_attached_docs=len(attached_docs) > 0,
            has_attached_images=len(attached_images) > 0,
            force_rag=req.enable_rag,
            force_web=req.enable_web_search
        )
        logger.info(f"Query '{req.message[:50]}...' routed to: {query_type}")

        # 4. Handle Document Creation Action
        if query_type == "document_creation":
            # Extract document title from prompt or generate a suitable one
            title = req.message.replace("create a report on", "").replace("create a document on", "").strip()
            if len(title) > 50:
                title = title[:50]
            if not title:
                title = "Generated Report"

            doc_action = await document_service.create_document(
                db=db,
                title=title,
                instructions=req.message,
                conversation_id=conv_id
            )

            assistant_reply = (
                f"### 📄 Document Created Successfully\n\n"
                f"I have created the document **{doc_action['filename']}** based on your instructions.\n\n"
                f"- **Format:** Microsoft Word (.docx)\n"
                f"- **Download:** [Click here to download your document]({doc_action['download_url']})\n\n"
                f"You can review it and request any updates or modifications right here!"
            )

            # Persist messages
            ConversationService.add_message(db, conv_id, role="user", content=req.message)
            ConversationService.add_message(
                db,
                conv_id,
                role="assistant",
                content=assistant_reply,
                metadata={"query_type": query_type, "created_document": doc_action}
            )

            return ChatResponse(
                conversation_id=conv_id,
                response=assistant_reply,
                query_type=query_type,
                sources=[],
                created_document=doc_action
            )

        # 5. Handle Document Update Action
        if query_type == "document_update" and attached_docs:
            target_doc = attached_docs[0]
            doc_action = await document_service.update_document(
                db=db,
                document_id=target_doc.id,
                modification_instructions=req.message,
                conversation_id=conv_id
            )

            assistant_reply = (
                f"### 📝 Document Updated Successfully\n\n"
                f"I have applied your modifications to **{target_doc.filename}** and generated a new version: **{doc_action['filename']}**.\n\n"
                f"- **Original File:** {target_doc.filename}\n"
                f"- **Updated File:** {doc_action['filename']}\n"
                f"- **Download:** [Click here to download updated document]({doc_action['download_url']})\n\n"
                f"The original file has been preserved intact."
            )

            ConversationService.add_message(db, conv_id, role="user", content=req.message)
            ConversationService.add_message(
                db,
                conv_id,
                role="assistant",
                content=assistant_reply,
                metadata={"query_type": query_type, "created_document": doc_action}
            )

            return ChatResponse(
                conversation_id=conv_id,
                response=assistant_reply,
                query_type=query_type,
                sources=[],
                created_document=doc_action
            )

        # 6. Handle AI Image Generation Action
        if query_type == "image_generation":
            gen_res = await image_gen_service.generate_ai_image(req.message)
            img_url = gen_res["image_url"]
            prompt_used = gen_res["prompt"]
            assistant_reply = (
                f"### 🎨 AI Generated Image\n\n"
                f"Here is the generated image for: **\"{prompt_used}\"**\n\n"
                f"![{prompt_used}]({img_url})\n\n"
                f"- **Model**: FLUX.1 (Free AI Generator)\n"
                f"- **Direct Link**: [Open Full Resolution Image]({gen_res.get('direct_url', img_url)})"
            )
            ConversationService.add_message(db, conv_id, role="user", content=req.message)
            ConversationService.add_message(
                db,
                conv_id,
                role="assistant",
                content=assistant_reply,
                metadata={"query_type": query_type, "generated_image": gen_res}
            )
            return ChatResponse(
                conversation_id=conv_id,
                response=assistant_reply,
                query_type=query_type,
                sources=[],
                created_document=None
            )

        # 7. Handle Web Image Search Action
        if query_type == "web_image_search":
            found_images = await image_gen_service.search_web_images(req.message, max_results=2)
            if found_images:
                primary = found_images[0]
                assistant_reply = (
                    f"### 📷 Image Search Result\n\n"
                    f"Here is the image for **\"{primary['title']}\"**:\n\n"
                    f"![{primary['title']}]({primary['image_url']})\n\n"
                    f"🔗 **Source**: [{primary['title']}]({primary['source_url']})"
                )
            else:
                assistant_reply = f"I searched the web for images regarding '{req.message}', but couldn't retrieve a direct preview. Please try specifying the person or place name."

            ConversationService.add_message(db, conv_id, role="user", content=req.message)
            ConversationService.add_message(
                db,
                conv_id,
                role="assistant",
                content=assistant_reply,
                metadata={"query_type": query_type, "web_images": found_images}
            )
            return ChatResponse(
                conversation_id=conv_id,
                response=assistant_reply,
                query_type=query_type,
                sources=[],
                created_document=None
            )

        # 8. Gather Context: RAG and/or Web Search
        rag_context = ""
        web_context = ""
        sources = []

        # RAG context retrieval
        if query_type in ["rag", "hybrid"] or (attached_docs and not req.enable_web_search):
            doc_ids = [d.id for d in attached_docs] if attached_docs else None
            chunks = await rag_service.retrieve_relevant_chunks(
                db=db,
                query=req.message,
                conversation_id=conv_id,
                document_ids=doc_ids,
                top_k=4
            )
            if chunks:
                rag_context = rag_service.build_context_string(chunks)
                for c in chunks:
                    sources.append({
                        "type": "document",
                        "title": c["filename"],
                        "chunk": c["chunk_index"],
                        "score": c["score"],
                        "snippet": c["content"][:200]
                    })

        # Web Search retrieval
        if query_type in ["web_search", "hybrid"]:
            search_results = await search_service.search(query=req.message)
            if search_results:
                web_context = search_service.format_search_context(search_results)
                for r in search_results:
                    sources.append({
                        "type": "web",
                        "title": r["title"],
                        "url": r["url"],
                        "snippet": r["snippet"]
                    })

        # Multimodal Image Preparation
        images_base64 = []
        for img_doc in attached_images:
            try:
                processed = multimodal_service.process_image(img_doc.file_path)
                images_base64.append(processed)
            except Exception as e:
                logger.error(f"Error processing image {img_doc.filename}: {e}")

        # 7. Get Recent Conversation History for Context
        history = ConversationService.get_history(db, conv_id, limit=6)

        # 8. Generate LLM Response
        llm_response = await llm_service.generate_response(
            prompt=req.message,
            conversation_history=history,
            context_docs=rag_context,
            web_context=web_context,
            images_base64=images_base64 if images_base64 else None
        )

        # 9. Persist User and Assistant Messages
        user_meta = {
            "attached_file_ids": req.attached_file_ids
        }
        ConversationService.add_message(db, conv_id, role="user", content=req.message, metadata=user_meta)

        assistant_meta = {
            "query_type": query_type,
            "sources": sources
        }
        ConversationService.add_message(db, conv_id, role="assistant", content=llm_response, metadata=assistant_meta)

        return ChatResponse(
            conversation_id=conv_id,
            response=llm_response,
            query_type=query_type,
            sources=sources,
            created_document=None
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Assistant processing error: {str(e)}")


@router.post("/stream")
async def chat_stream_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    """
    conv = ConversationService.get_or_create_conversation(db, conversation_id=req.conversation_id)
    conv_id = conv.id

    # Retrieve context
    attached_docs = []
    if req.attached_file_ids:
        attached_docs = db.query(DBDocument).filter(
            DBDocument.id.in_(req.attached_file_ids),
            ~DBDocument.file_type.in_(["png", "jpg", "jpeg", "webp"])
        ).all()

    query_type = search_service.classify_query(
        query=req.message,
        has_attached_docs=len(attached_docs) > 0,
        force_rag=req.enable_rag,
        force_web=req.enable_web_search
    )

    rag_context = ""
    sources = []
    if query_type in ["rag", "hybrid"] or attached_docs:
        doc_ids = [d.id for d in attached_docs] if attached_docs else None
        chunks = await rag_service.retrieve_relevant_chunks(
            db=db,
            query=req.message,
            conversation_id=conv_id,
            document_ids=doc_ids,
            top_k=4
        )
        if chunks:
            rag_context = rag_service.build_context_string(chunks)
            for c in chunks:
                sources.append({
                    "type": "document",
                    "title": c["filename"],
                    "chunk": c["chunk_index"],
                    "score": c["score"]
                })

    web_context = ""
    if query_type in ["web_search", "hybrid"]:
        search_results = await search_service.search(query=req.message)
        if search_results:
            web_context = search_service.format_search_context(search_results)
            for r in search_results:
                sources.append({
                    "type": "web",
                    "title": r["title"],
                    "url": r["url"]
                })

    history = ConversationService.get_history(db, conv_id, limit=6)

    async def event_generator():
        accumulated_text = []
        try:
            async for token in llm_service.generate_response_stream(
                prompt=req.message,
                conversation_history=history,
                context_docs=rag_context,
                web_context=web_context
            ):
                accumulated_text.append(token)
                data = json.dumps({"token": token, "done": False})
                yield f"data: {data}\n\n"

            # Finalize and persist
            full_response = "".join(accumulated_text)
            ConversationService.add_message(db, conv_id, role="user", content=req.message)
            ConversationService.add_message(
                db,
                conv_id,
                role="assistant",
                content=full_response,
                metadata={"query_type": query_type, "sources": sources}
            )

            done_payload = json.dumps({
                "done": True,
                "conversation_id": conv_id,
                "query_type": query_type,
                "sources": sources
            })
            yield f"data: {done_payload}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            err_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {err_data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
