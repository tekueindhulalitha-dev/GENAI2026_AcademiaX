# backend/utils/vector_db.py
"""
Vector Database layer.

Converts paper text → 384-dim sentence-transformer embeddings,
stores them in PostgreSQL, and performs cosine-similarity search.

Production upgrade path: swap numpy store for pgvector extension.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from models.database import Paper, VectorEmbedding, WorkspacePaper

logger     = logging.getLogger(__name__)
MODEL_NAME = "all-MiniLM-L6-v2"    # 384-dim, ~80 MB, fast inference
_model: Optional[SentenceTransformer] = None


# ── Load model (singleton) ────────────────────────────────────
def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading sentence-transformer: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


# ═════════════════════════════════════════════════════════════
# EMBEDDING HELPERS
# ═════════════════════════════════════════════════════════════

def embed_text(text: str) -> np.ndarray:
    """Return a normalised L2 embedding vector for the given text."""
    vec = _get_model().encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype(np.float32)


def _paper_to_text(paper: Paper) -> str:
    parts = [paper.title or ""]
    if paper.abstract:
        parts.append(paper.abstract)
    if paper.authors:
        try:
            authors = json.loads(paper.authors)
            parts.append("Authors: " + ", ".join(authors))
        except Exception:
            parts.append(paper.authors)
    return " ".join(parts)


def _vec_to_str(v: np.ndarray) -> str:
    return ",".join(str(x) for x in v.tolist())


def _str_to_vec(s: str) -> np.ndarray:
    return np.array(s.split(","), dtype=np.float32)


# ═════════════════════════════════════════════════════════════
# CREATE / REFRESH EMBEDDING
# ═════════════════════════════════════════════════════════════

def create_embedding(db: Session, paper: Paper) -> VectorEmbedding:
    """
    Generate and persist a vector embedding for a paper.
    If one already exists it is refreshed (re-embedded).
    """
    vector   = embed_text(_paper_to_text(paper))
    existing = db.query(VectorEmbedding).filter_by(paper_id=paper.id).first()

    if existing:
        existing.vector     = _vec_to_str(vector)
        existing.model_name = MODEL_NAME
        db.commit()
        db.refresh(existing)
        return existing

    emb = VectorEmbedding(
        paper_id   = paper.id,
        vector     = _vec_to_str(vector),
        model_name = MODEL_NAME,
    )
    db.add(emb)
    db.commit()
    db.refresh(emb)
    logger.info(f"Embedding created for paper_id={paper.id}")
    return emb


# ═════════════════════════════════════════════════════════════
# SEARCH FUNCTIONS
# ═════════════════════════════════════════════════════════════

def semantic_search(
    db:        Session,
    query:     str,
    owner_id:  int,
    top_k:     int   = 10,
    threshold: float = 0.0,
) -> List[Tuple[Paper, float]]:
    """
    Cosine-similarity search over ALL papers owned by a user.
    Returns list of (Paper, similarity_score) sorted descending.
    """
    q_vec = embed_text(query)

    rows = (
        db.query(VectorEmbedding, Paper)
        .join(Paper, VectorEmbedding.paper_id == Paper.id)
        .filter(Paper.owner_id == owner_id)
        .all()
    )
    if not rows:
        return []

    matrix = np.stack([_str_to_vec(r.VectorEmbedding.vector) for r in rows])
    papers = [r.Paper for r in rows]
    scores = matrix @ q_vec                  # cosine (vectors normalised)
    ranked = np.argsort(scores)[::-1]

    return [
        (papers[i], float(scores[i]))
        for i in ranked[:top_k]
        if float(scores[i]) >= threshold
    ]


def workspace_semantic_search(
    db:           Session,
    query:        str,
    workspace_id: int,
    owner_id:     int,
    top_k:        int = 5,
) -> List[Tuple[Paper, float]]:
    """
    Semantic search scoped to a single workspace.
    Used by the AI chatbot to fetch relevant paper context.
    """
    q_vec = embed_text(query)

    rows = (
        db.query(VectorEmbedding, Paper)
        .join(Paper,          VectorEmbedding.paper_id == Paper.id)
        .join(WorkspacePaper, WorkspacePaper.paper_id  == Paper.id)
        .filter(
            WorkspacePaper.workspace_id == workspace_id,
            Paper.owner_id == owner_id,
        )
        .all()
    )
    if not rows:
        return []

    matrix = np.stack([_str_to_vec(r.VectorEmbedding.vector) for r in rows])
    papers = [r.Paper for r in rows]
    scores = matrix @ q_vec
    ranked = np.argsort(scores)[::-1]

    return [(papers[i], float(scores[i])) for i in ranked[:top_k]]


def get_related_papers(
    db:       Session,
    paper_id: int,
    owner_id: int,
    top_k:    int = 5,
) -> List[Tuple[Paper, float]]:
    """Find papers most similar to a given paper (Related Papers feature)."""
    src = db.query(VectorEmbedding).filter_by(paper_id=paper_id).first()
    if not src:
        return []

    src_vec = _str_to_vec(src.vector)

    rows = (
        db.query(VectorEmbedding, Paper)
        .join(Paper, VectorEmbedding.paper_id == Paper.id)
        .filter(Paper.owner_id == owner_id, VectorEmbedding.paper_id != paper_id)
        .all()
    )
    if not rows:
        return []

    matrix = np.stack([_str_to_vec(r.VectorEmbedding.vector) for r in rows])
    papers = [r.Paper for r in rows]
    scores = matrix @ src_vec
    ranked = np.argsort(scores)[::-1]

    return [(papers[i], float(scores[i])) for i in ranked[:top_k]]
