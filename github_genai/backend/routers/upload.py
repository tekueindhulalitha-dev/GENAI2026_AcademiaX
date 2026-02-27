# backend/routers/upload.py
"""
Upload & Doc Space endpoints.

POST /upload/pdf                – Upload a PDF, extract text, generate AI summary
GET  /upload/documents          – List all user documents (Doc Space page)
POST /upload/notes              – Save a text note
GET  /upload/documents/{id}     – Get document content
DELETE /upload/documents/{id}   – Delete a document
"""

import io
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from models.database import Document, Paper, User, Workspace, get_db
from models.schemas  import DocumentOut, NoteCreate, UploadResponse
from utils.groq_client import summarize_pdf_text
from utils.security    import get_current_user
from utils.vector_db   import create_embedding

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload & Doc Space"])


# ── Upload PDF ────────────────────────────────────────────────
@router.post("/pdf", response_model=UploadResponse)
async def upload_pdf(
    file:         UploadFile    = File(...),
    workspace_id: Optional[int] = Form(None),
    auto_summary: bool          = Form(True),
    create_emb:   bool          = Form(True),
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    """
    Powers the Upload PDF page pipeline:
    1. Receive PDF file
    2. Extract text (PyMuPDF)
    3. Parse basic metadata from filename
    4. Generate AI summary via Groq (if auto_summary=True)
    5. Save to documents table
    6. Optionally link to a workspace
    7. Create a Paper record so it appears in the user's library
    8. Generate vector embedding (if create_emb=True)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()
    size_bytes = len(contents)

    # ── Extract text with PyMuPDF ─────────────────────────────
    text, page_count = _extract_pdf_text(contents)

    # ── AI Summary ────────────────────────────────────────────
    ai_summary = None
    if auto_summary and text.strip():
        try:
            ai_summary = summarize_pdf_text(text, title=file.filename)
        except RuntimeError as e:
            logger.warning(f"AI summary failed: {e}")

    # ── Validate workspace ────────────────────────────────────
    ws_name = None
    if workspace_id:
        ws = db.query(Workspace).filter_by(
            id=workspace_id, owner_id=current_user.id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found.")
        ws_name = ws.name

    # ── Save to Document table ────────────────────────────────
    doc = Document(
        name         = file.filename,
        doc_type     = "pdf",
        content      = text,
        size_bytes   = size_bytes,
        page_count   = page_count,
        workspace_id = workspace_id,
        owner_id     = current_user.id,
    )
    db.add(doc)

    # ── Create Paper record for the uploaded PDF ──────────────
    paper = Paper(
        source       = "upload",
        title        = file.filename.replace(".pdf", ""),
        abstract     = ai_summary or text[:500],
        full_text    = text,
        ai_summary   = ai_summary,
        owner_id     = current_user.id,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # ── Link to workspace ─────────────────────────────────────
    if workspace_id:
        from models.database import WorkspacePaper
        db.add(WorkspacePaper(workspace_id=workspace_id, paper_id=paper.id))
        db.commit()

    # ── Vector embedding ──────────────────────────────────────
    if create_emb and text.strip():
        try:
            create_embedding(db, paper)
        except Exception as e:
            logger.warning(f"Embedding failed for uploaded PDF: {e}")

    db.refresh(doc)
    return UploadResponse(
        document_id = doc.id,
        name        = file.filename,
        pages       = page_count,
        size_bytes  = size_bytes,
        ai_summary  = ai_summary,
        workspace   = ws_name,
    )


# ── List documents ────────────────────────────────────────────
@router.get("/documents", response_model=List[DocumentOut])
def list_documents(
    doc_type:     Optional[str] = None,
    workspace_id: Optional[int] = None,
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    """Powers the Doc Space page – returns all docs for the current user."""
    q = db.query(Document).filter_by(owner_id=current_user.id)
    if doc_type:
        q = q.filter_by(doc_type=doc_type)
    if workspace_id:
        q = q.filter_by(workspace_id=workspace_id)
    return q.order_by(Document.created_at.desc()).all()


# ── Get document content ──────────────────────────────────────
@router.get("/documents/{doc_id}")
def get_document(
    doc_id:       int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    doc = db.query(Document).filter_by(id=doc_id, owner_id=current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "id":           doc.id,
        "name":         doc.name,
        "doc_type":     doc.doc_type,
        "content":      doc.content,
        "size_bytes":   doc.size_bytes,
        "page_count":   doc.page_count,
        "workspace_id": doc.workspace_id,
        "created_at":   doc.created_at,
    }


# ── Save note ────────────────────────────────────────────────
@router.post("/notes", response_model=DocumentOut, status_code=201)
def save_note(
    data:         NoteCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Save a text note from the Doc Space → Notes tab."""
    doc = Document(
        name         = data.name,
        doc_type     = "note",
        content      = data.content,
        size_bytes   = len(data.content.encode()),
        page_count   = 0,
        workspace_id = data.workspace_id,
        owner_id     = current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── Delete document ───────────────────────────────────────────
@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id:       int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    doc = db.query(Document).filter_by(id=doc_id, owner_id=current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(doc)
    db.commit()


# ── PDF text extraction ───────────────────────────────────────
def _extract_pdf_text(contents: bytes) -> tuple[str, int]:
    """
    Extract text from PDF bytes using PyMuPDF (fitz).
    Returns (full_text, page_count).
    Falls back to empty string if extraction fails.
    """
    try:
        import fitz  # PyMuPDF
        doc    = fitz.open(stream=contents, filetype="pdf")
        pages  = doc.page_count
        text   = "\n\n".join(
            doc.load_page(i).get_text("text")
            for i in range(min(pages, 50))   # cap at 50 pages
        )
        doc.close()
        return text, pages
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return "", 0
