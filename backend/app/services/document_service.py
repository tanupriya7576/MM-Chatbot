import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
try:
    from docx import Document as DocxDocument
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
from app.config import settings
from app.models.models import Document as DBDocument
from app.services.llm_service import llm_service
from app.utils.file_parser import extract_text_from_file
from app.utils.logger import logger

class DocumentService:
    @staticmethod
    async def create_document(
        db: Session,
        title: str,
        instructions: str,
        conversation_id: Optional[str] = None,
        file_format: str = "docx"
    ) -> Dict[str, Any]:
        """
        Generates a structured document (e.g. DOCX) based on user instructions and saves it.
        """
        logger.info(f"Creating new document '{title}' with format '{file_format}'")

        # Prompt LLM to produce structured content
        doc_prompt = f"""You are a professional technical writer and document designer.
Generate the complete content for a document titled: "{title}".
User instructions: "{instructions}"

Format your output with clear section headers starting with '#' for Title, '##' for main sections, and '###' for sub-sections.
Include introduction, detailed sections with explanations, bullet points where appropriate, and a conclusion.
Make the content thorough, well-written, and informative.
"""
        generated_content = await llm_service.generate_response(prompt=doc_prompt)

        # Generate file (DOCX if python-docx installed, otherwise formatted TXT)
        ext = "docx" if HAS_DOCX else "txt"
        filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:40]}_{uuid.uuid4().hex[:6]}.{ext}"
        file_path = os.path.join(settings.GENERATED_DIR, filename)

        if HAS_DOCX:
            doc = DocxDocument()

            # Document Title
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(title)
            title_run.font.size = Pt(24)
            title_run.font.bold = True
            title_run.font.color.rgb = RGBColor(30, 58, 138)  # Deep Indigo
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()  # Spacing

            # Parse generated markdown-like text into DOCX paragraphs and headings
            for line in generated_content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("### "):
                    p = doc.add_heading(line.replace("### ", ""), level=3)
                elif line.startswith("## "):
                    p = doc.add_heading(line.replace("## ", ""), level=2)
                elif line.startswith("# "):
                    if line.replace("# ", "").lower() != title.lower():
                        p = doc.add_heading(line.replace("# ", ""), level=1)
                elif line.startswith("- ") or line.startswith("* "):
                    p = doc.add_paragraph(line[2:], style="List Bullet")
                elif re.match(r"^\d+\.\s", line):
                    p = doc.add_paragraph(re.sub(r"^\d+\.\s", "", line), style="List Number")
                else:
                    p = doc.add_paragraph(line)
                    p.paragraph_format.line_spacing = 1.15
                    p.paragraph_format.space_after = Pt(6)

            doc.save(file_path)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n" + generated_content)

        file_size = os.path.getsize(file_path)

        # Register document in database
        db_doc = DBDocument(
            filename=filename,
            file_type=ext,
            file_path=file_path,
            file_size=file_size,
            conversation_id=conversation_id
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        logger.info(f"Successfully created document: {filename} (ID: {db_doc.id})")

        return {
            "document_id": db_doc.id,
            "filename": filename,
            "file_path": file_path,
            "download_url": f"/api/documents/{db_doc.id}/download",
            "message": f"Successfully created document '{title}' as a downloadable DOCX."
        }

    @staticmethod
    async def update_document(
        db: Session,
        document_id: str,
        modification_instructions: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reads an existing document, applies requested modifications using LLM,
        and saves a new versioned copy to preserve the original.
        """
        orig_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not orig_doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        logger.info(f"Updating document: {orig_doc.filename} based on instructions: {modification_instructions}")

        # Extract current text from original document
        orig_text, _ = extract_text_from_file(orig_doc.file_path)

        # Prompt LLM to update content while respecting existing structure
        update_prompt = f"""You are a professional document editor.
Here is the current content of an existing document:
=== CURRENT DOCUMENT START ===
{orig_text[:4000]}
=== CURRENT DOCUMENT END ===

User requested modifications:
"{modification_instructions}"

Rewrite the document incorporating the requested modifications faithfully.
Maintain headers with '#', '##', '###', and clear bullet points.
Return the complete, revised document.
"""
        updated_content = await llm_service.generate_response(prompt=update_prompt)

        # Create new versioned file name
        base_name = Path(orig_doc.filename).stem
        ext = "docx" if HAS_DOCX else "txt"
        new_filename = f"{base_name}_updated_{uuid.uuid4().hex[:4]}.{ext}"
        new_file_path = os.path.join(settings.GENERATED_DIR, new_filename)

        if HAS_DOCX:
            # Build DOCX for updated document
            doc = DocxDocument()
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(f"Updated: {base_name}")
            title_run.font.size = Pt(20)
            title_run.font.bold = True
            title_run.font.color.rgb = RGBColor(16, 185, 129)  # Emerald green header
            doc.add_paragraph()

            for line in updated_content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("### "):
                    doc.add_heading(line.replace("### ", ""), level=3)
                elif line.startswith("## "):
                    doc.add_heading(line.replace("## ", ""), level=2)
                elif line.startswith("# "):
                    doc.add_heading(line.replace("# ", ""), level=1)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:], style="List Bullet")
                elif re.match(r"^\d+\.\s", line):
                    doc.add_paragraph(re.sub(r"^\d+\.\s", "", line), style="List Number")
                else:
                    p = doc.add_paragraph(line)
                    p.paragraph_format.space_after = Pt(6)

            doc.save(new_file_path)
        else:
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(f"# Updated: {base_name}\n\n" + updated_content)

        file_size = os.path.getsize(new_file_path)

        # Save new document record in DB
        new_db_doc = DBDocument(
            filename=new_filename,
            file_type=ext,
            file_path=new_file_path,
            file_size=file_size,
            conversation_id=conversation_id or orig_doc.conversation_id
        )
        db.add(new_db_doc)
        db.commit()
        db.refresh(new_db_doc)

        logger.info(f"Successfully saved updated document copy: {new_filename} (ID: {new_db_doc.id})")

        return {
            "document_id": new_db_doc.id,
            "filename": new_filename,
            "file_path": new_file_path,
            "download_url": f"/api/documents/{new_db_doc.id}/download",
            "message": f"Successfully updated document and created '{new_filename}'."
        }

document_service = DocumentService()
