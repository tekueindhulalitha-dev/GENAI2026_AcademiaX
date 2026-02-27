# backend/routers/chat.py
"""
Chat endpoints – powers the AI Assistant page.

POST /chat/message              – send message, get AI response
GET  /chat/{workspace_id}/history – fetch conversation history
DELETE /chat/{workspace_id}/history – clear conversation history
"""

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import (
    ConversationHistory, Paper, User, Workspace, WorkspacePaper, get_db,
)
from models.schemas  import ChatMessage, ChatResponse, ConversationOut
from utils.groq_client  import chat_with_context
from utils.security     import get_current_user
from utils.vector_db    import workspace_semantic_search

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Chat"])


# ── Send message ──────────────────────────────────────────────
@router.post("/message", response_model=ChatResponse)
def send_message(
    msg:          ChatMessage,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Core chat endpoint for the AI Assistant page.

    Flow:
    1. Verify user owns the workspace
    2. Retrieve semantically relevant papers as context
    3. Fetch conversation history for multi-turn awareness
    4. Call Groq Llama 3.3 70B with full context
    5. Persist both turns to conversation_history
    6. Return the AI response
    """
    # 1. Verify workspace ownership
    ws = db.query(Workspace).filter_by(
        id=msg.workspace_id, owner_id=current_user.id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    # 2. Get relevant papers via semantic search
    relevant = workspace_semantic_search(
        db,
        query        = msg.content,
        workspace_id = msg.workspace_id,
        owner_id     = current_user.id,
        top_k        = 5,
    )

    # Fall back to all workspace papers if no embeddings yet
    if not relevant:
        all_papers = (
            db.query(Paper)
            .join(WorkspacePaper, WorkspacePaper.paper_id == Paper.id)
            .filter(WorkspacePaper.workspace_id == msg.workspace_id)
            .all()
        )
        paper_dicts = [_paper_to_dict(p) for p in all_papers]
    else:
        paper_dicts = [_paper_to_dict(p) for p, _ in relevant]

    # 3. Conversation history (last 10 turns)
    history_rows = (
        db.query(ConversationHistory)
        .filter_by(workspace_id=msg.workspace_id)
        .order_by(ConversationHistory.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": row.role, "content": row.content} for row in history_rows]

    # 4. Call Groq
    try:
        ai_response = chat_with_context(
            user_message          = msg.content,
            workspace_papers      = paper_dicts,
            conversation_history  = history,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 5. Persist both turns
    db.add(ConversationHistory(
        workspace_id = msg.workspace_id,
        role         = "user",
        content      = msg.content,
    ))
    db.add(ConversationHistory(
        workspace_id = msg.workspace_id,
        role         = "assistant",
        content      = ai_response,
    ))
    db.commit()

    return ChatResponse(
        response     = ai_response,
        workspace_id = msg.workspace_id,
        model        = "llama-3.3-70b-versatile",
    )


# ── Get history ───────────────────────────────────────────────
@router.get("/{workspace_id}/history", response_model=List[ConversationOut])
def get_history(
    workspace_id: int,
    limit:        int     = 50,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return the last `limit` messages for a workspace chatbot session."""
    ws = db.query(Workspace).filter_by(
        id=workspace_id, owner_id=current_user.id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    rows = (
        db.query(ConversationHistory)
        .filter_by(workspace_id=workspace_id)
        .order_by(ConversationHistory.created_at.asc())
        .limit(limit)
        .all()
    )
    return rows


# ── Clear history ─────────────────────────────────────────────
@router.delete("/{workspace_id}/history", status_code=204)
def clear_history(
    workspace_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Clears all conversation history for a workspace (Clear chat button)."""
    ws = db.query(Workspace).filter_by(
        id=workspace_id, owner_id=current_user.id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    db.query(ConversationHistory).filter_by(workspace_id=workspace_id).delete()
    db.commit()


# ── Helper ────────────────────────────────────────────────────
def _paper_to_dict(paper: Paper) -> dict:
    authors = paper.authors or "[]"
    try:
        authors = json.loads(authors)
    except Exception:
        authors = [authors]
    return {
        "title":    paper.title,
        "authors":  authors,
        "abstract": paper.abstract or "",
    }
