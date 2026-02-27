# backend/routers/papers.py
"""
Paper endpoints – matching Search Papers & AI Tools pages.

GET  /papers/search              – search arXiv + PubMed
POST /papers/import              – save a paper to the user's library
GET  /papers/                    – list all imported papers
GET  /papers/semantic-search     – vector similarity search
GET  /papers/{id}/related        – related papers
DELETE /papers/{id}              – remove a paper
POST /papers/ai-tools            – AI Summaries / Key Insights / Lit Review
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import (
    Paper, User, Workspace, WorkspacePaper, get_db,
)
from models.schemas  import (
    AIToolRequest, AIToolResponse, PaperImport, PaperOut,
    PaperSearchResult, SemanticSearchResult,
)
from utils.arxiv_client  import search_arxiv,  get_arxiv_paper
from utils.groq_client   import (
    extract_key_insights, generate_literature_review, generate_summaries,
)
from utils.pubmed_client import search_pubmed, get_pubmed_paper
from utils.security      import get_current_user
from utils.vector_db     import (
    create_embedding, get_related_papers, semantic_search,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/papers", tags=["Papers"])


# ── 1. SEARCH (arXiv + PubMed combined) ──────────────────────
@router.get("/search", response_model=List[PaperSearchResult])
async def search_papers(
    query:        str = Query(..., min_length=2, description="Search query"),
    source:       str = Query("all", description="arxiv | pubmed | all"),
    max_results:  int = Query(10, ge=1, le=50),
    _: User = Depends(get_current_user),
):
    """
    Powers the Search Papers page.
    Queries arXiv, PubMed, or both and returns merged results.
    """
    results: List[PaperSearchResult] = []

    if source in ("arxiv", "all"):
        results.extend(await search_arxiv(query, max_results))

    if source in ("pubmed", "all"):
        results.extend(await search_pubmed(query, max_results))

    # De-duplicate
    seen, unique = set(), []
    for r in results:
        key = (r.source, r.external_id)
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


# ── 2. IMPORT ─────────────────────────────────────────────────
@router.post("/import", response_model=PaperOut)
async def import_paper(
    data:         PaperImport,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Save a search result or manual entry to the user's library.
    Creates a vector embedding automatically.
    Optionally links the paper to a workspace via workspace_id.
    """
    # Check for duplicate
    existing = (
        db.query(Paper)
        .filter_by(
            external_id = data.external_id,
            source      = data.source,
            owner_id    = current_user.id,
        )
        .first()
    )

    if existing:
        paper = existing
    else:
        paper = Paper(
            external_id    = data.external_id,
            source         = data.source,
            title          = data.title,
            authors        = json.dumps(data.authors or []),
            abstract       = data.abstract,
            published_date = data.published_date,
            url            = data.url,
            pdf_url        = data.pdf_url,
            journal        = data.journal,
            venue          = data.venue,
            doi            = data.doi,
            citations      = data.citations or 0,
            tags           = json.dumps(data.tags or []),
            owner_id       = current_user.id,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        # Generate embedding (non-blocking failure)
        try:
            create_embedding(db, paper)
        except Exception as e:
            logger.warning(f"Embedding failed for paper {paper.id}: {e}")

    # Link to workspace if provided
    if data.workspace_id:
        _link_to_workspace(db, paper.id, data.workspace_id, current_user.id)

    return paper


# ── 3. LIST ───────────────────────────────────────────────────
@router.get("/", response_model=List[PaperOut])
def list_papers(
    workspace_id: Optional[int] = Query(None),
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    if workspace_id:
        papers = (
            db.query(Paper)
            .join(WorkspacePaper, WorkspacePaper.paper_id == Paper.id)
            .filter(
                WorkspacePaper.workspace_id == workspace_id,
                Paper.owner_id == current_user.id,
            )
            .all()
        )
    else:
        papers = db.query(Paper).filter_by(owner_id=current_user.id).all()
    return papers


# ── 4. SEMANTIC SEARCH ────────────────────────────────────────
@router.get("/semantic-search", response_model=List[SemanticSearchResult])
def semantic_search_endpoint(
    query:        str     = Query(..., min_length=2),
    top_k:        int     = Query(5, ge=1, le=20),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Vector similarity search over the user's imported paper library.
    Returns papers ranked by conceptual similarity, not keyword match.
    """
    ranked = semantic_search(db, query=query, owner_id=current_user.id, top_k=top_k)
    return [
        SemanticSearchResult(paper=paper, similarity=round(score, 4))
        for paper, score in ranked
    ]


# ── 5. RELATED PAPERS ─────────────────────────────────────────
@router.get("/{paper_id}/related", response_model=List[SemanticSearchResult])
def related_papers(
    paper_id:     int,
    top_k:        int     = Query(5, ge=1, le=10),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    ranked = get_related_papers(db, paper_id=paper_id, owner_id=current_user.id, top_k=top_k)
    return [
        SemanticSearchResult(paper=paper, similarity=round(score, 4))
        for paper, score in ranked
    ]


# ── 6. DELETE ─────────────────────────────────────────────────
@router.delete("/{paper_id}", status_code=204)
def delete_paper(
    paper_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    paper = db.query(Paper).filter_by(id=paper_id, owner_id=current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    db.delete(paper)
    db.commit()


# ── 7. AI TOOLS ───────────────────────────────────────────────
@router.post("/ai-tools", response_model=AIToolResponse)
def ai_tools(
    req:          AIToolRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Powers the AI Tools section in the Workspaces page.
    tool_type: 'summarize' | 'insights' | 'literature_review'
    """
    papers = db.query(Paper).filter(
        Paper.id.in_(req.paper_ids),
        Paper.owner_id == current_user.id,
    ).all()

    if not papers:
        raise HTTPException(status_code=404, detail="No matching papers found.")

    paper_dicts = [
        {
            "title":    p.title,
            "authors":  _parse_json_field(p.authors),
            "abstract": p.abstract or "",
            "published_date": p.published_date or "",
        }
        for p in papers
    ]

    tool_map = {
        "summarize":         generate_summaries,
        "insights":          extract_key_insights,
        "literature_review": generate_literature_review,
    }

    fn = tool_map.get(req.tool_type)
    if not fn:
        raise HTTPException(status_code=400, detail=f"Unknown tool_type: {req.tool_type}")

    try:
        result = fn(paper_dicts)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return AIToolResponse(
        tool_type = req.tool_type,
        result    = result,
        model     = "llama-3.3-70b-versatile",
    )


# ── Helpers ───────────────────────────────────────────────────
def _link_to_workspace(db: Session, paper_id: int, workspace_id: int, owner_id: int):
    ws = db.query(Workspace).filter_by(id=workspace_id, owner_id=owner_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    exists = db.query(WorkspacePaper).filter_by(
        workspace_id=workspace_id, paper_id=paper_id
    ).first()
    if not exists:
        db.add(WorkspacePaper(workspace_id=workspace_id, paper_id=paper_id))
        db.commit()


def _parse_json_field(value: Optional[str]) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return [value]
