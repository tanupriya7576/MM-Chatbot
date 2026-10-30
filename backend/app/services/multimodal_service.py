import base64
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from app.utils.file_parser import is_image_file, is_document_file, extract_text_from_file
from app.utils.logger import logger

class MultimodalService:
    @staticmethod
    def process_image(file_path: str, max_size: int = 1024) -> Dict[str, str]:
        """
        Reads, optionally downsamples, and base64 encodes an image for LLM vision models.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at: {file_path}")

        ext = path.suffix.lower().lstrip(".")
        mime_type = "image/png" if ext == "png" else "image/jpeg"
        if ext == "webp":
            mime_type = "image/webp"

        try:
            if HAS_PIL:
                with Image.open(path) as img:
                    # Convert RGBA to RGB if saving as JPEG
                    if img.mode in ("RGBA", "P") and ext in ("jpg", "jpeg"):
                        img = img.convert("RGB")

                    # Resize if larger than max_size to save memory and token count
                    if max(img.width, img.height) > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                    buffer = io.BytesIO()
                    format_name = "PNG" if ext == "png" else "JPEG"
                    if ext == "webp":
                        format_name = "WEBP"
                    img.save(buffer, format=format_name)
                    b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            else:
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")

            return {
                "mime_type": mime_type,
                "data": b64_data,
                "filename": path.name
            }
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
            raise

    @staticmethod
    def process_document(file_path: str) -> Dict[str, Any]:
        """
        Extracts textual content and section metadata from a document.
        """
        full_text, sections = extract_text_from_file(file_path)
        return {
            "full_text": full_text,
            "sections": sections,
            "filename": Path(file_path).name,
            "char_count": len(full_text)
        }

multimodal_service = MultimodalService()
