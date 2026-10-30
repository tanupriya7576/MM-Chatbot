import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from app.main import app
from app.utils.file_parser import chunk_text, extract_text_from_file, is_allowed_file, is_image_file
from app.services.search_service import search_service

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "llm_provider" in data

def test_create_and_list_conversations(client):
    # Create conversation
    create_resp = client.post("/api/conversations", json={"title": "Test Chat Session"})
    assert create_resp.status_code == 201
    conv = create_resp.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test Chat Session"

    # List conversations
    list_resp = client.get("/api/conversations")
    assert list_resp.status_code == 200
    convs = list_resp.json()
    assert any(c["id"] == conv_id for c in convs)

    # Get conversation details
    detail_resp = client.get(f"/api/conversations/{conv_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == conv_id

    # Clean up
    del_resp = client.delete(f"/api/conversations/{conv_id}")
    assert del_resp.status_code == 200

def test_file_parser_allowed():
    assert is_allowed_file("report.pdf") is True
    assert is_allowed_file("document.docx") is True
    assert is_allowed_file("notes.txt") is True
    assert is_allowed_file("photo.png") is True
    assert is_allowed_file("malicious.exe") is False
    assert is_image_file("photo.jpg") is True
    assert is_image_file("document.pdf") is False

def test_text_chunking():
    sample_text = (
        "Artificial Intelligence (AI) is transforming technology. "
        "Retrieval-Augmented Generation (RAG) enhances LLMs with external knowledge. "
        "Vector databases index chunks of text using high-dimensional embeddings."
    )
    chunks = chunk_text(sample_text, chunk_size=80, overlap=20)
    assert len(chunks) >= 1
    assert all(len(c) > 0 for c in chunks)

def test_query_routing():
    # General
    assert search_service.classify_query("Tell me a bedtime story") == "general"
    
    # Document creation
    assert search_service.classify_query("Create a report on Machine Learning") == "document_creation"
    
    # Web search
    assert search_service.classify_query("What is the latest news today in AI?") == "web_search"
    
    # RAG
    assert search_service.classify_query("What does the uploaded document say about CNN?", has_attached_docs=True) == "rag"
    
    # Hybrid
    assert search_service.classify_query("Compare this document with the latest online trends", has_attached_docs=True) == "hybrid"

    # AI Image Generation
    assert search_service.classify_query("generate an image of a red sports car") == "image_generation"
    assert search_service.classify_query("photo banao ek robot ki") == "image_generation"

    # Web Image Search
    assert search_service.classify_query("show me a photo of Eiffel Tower") == "web_image_search"
    assert search_service.classify_query("Sachin Tendulkar ki photo dikhao") == "web_image_search"

def test_chat_endpoint_mock_response(client):
    resp = client.post("/api/chat", json={
        "message": "Hello, who are you and what can you do?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    assert "response" in data
    assert len(data["response"]) > 0
    assert data["query_type"] == "general"

def test_document_creation_endpoint(client):
    resp = client.post("/api/documents/create", json={
        "title": "Quantum Computing Primer",
        "instructions": "Create an introduction, 3 key milestones, and a conclusion.",
        "file_format": "docx"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "document_id" in data
    assert "download_url" in data
    assert data["filename"].endswith(".docx") or data["filename"].endswith(".txt")
