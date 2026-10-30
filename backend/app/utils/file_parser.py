import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.utils.logger import logger

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
    "json": "application/json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp"
}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt", "md", "csv", "json"}

def is_allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS

def is_image_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in IMAGE_EXTENSIONS

def is_document_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in DOCUMENT_EXTENSIONS

def extract_text_from_file(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts text and page/section metadata from supported document files.
    Returns: (full_text, pages_or_sections_list)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower().lstrip(".")
    full_text = ""
    sections: List[Dict[str, Any]] = []

    try:
        if ext == "pdf":
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                if page_text:
                    sections.append({
                        "page_number": idx + 1,
                        "content": page_text
                    })
                    full_text += f"\n--- Page {idx + 1} ---\n{page_text}"

        elif ext == "docx":
            import docx
            doc = docx.Document(str(path))
            paras = []
            for p in doc.paragraphs:
                if p.text.strip():
                    paras.append(p.text.strip())
            
            # Also extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_data:
                        paras.append(" | ".join(row_data))

            full_text = "\n\n".join(paras)
            sections.append({"page_number": 1, "content": full_text})

        elif ext in ["txt", "md", "csv", "json"]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    full_text = f.read()
            except UnicodeDecodeError:
                with open(path, "r", encoding="latin-1") as f:
                    full_text = f.read()
            sections.append({"page_number": 1, "content": full_text})

        else:
            raise ValueError(f"Unsupported file format for text extraction: .{ext}")

    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        raise

    return full_text.strip(), sections


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Recursively split text into readable chunks with overlap,
    respecting paragraphs and sentence boundaries.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If paragraph itself is larger than chunk_size, split by sentences or chunks
            if len(para) > chunk_size:
                sentences = para.split(". ")
                sub_chunk = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(sub_chunk) + len(sent) + 2 <= chunk_size:
                        sub_chunk = (sub_chunk + ". " + sent).strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        if len(sent) > chunk_size:
                            # Hard split with overlap
                            start = 0
                            while start < len(sent):
                                end = min(start + chunk_size, len(sent))
                                chunks.append(sent[start:end])
                                start += chunk_size - overlap
                            sub_chunk = ""
                        else:
                            sub_chunk = sent
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
