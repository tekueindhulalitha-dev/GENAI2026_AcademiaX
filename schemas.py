# backend/models/schemas.py
"""
Pydantic v2 schemas – one schema per API request/response pair.
Structured to exactly match what the Streamlit frontend sends and expects.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator


# ═════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class UserOut(BaseModel):
    id:         int
    email:      str
    full_name:  Optional[str]
    plan:       str
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None


# ═════════════════════════════════════════════════════════════
# WORKSPACE
# ═════════════════════════════════════════════════════════════

class WorkspaceCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    icon:        Optional[str] = "📁"
    color:       Optional[str] = "#6c63ff"

class WorkspaceOut(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    icon:        str
    color:       str
    owner_id:    int
    created_at:  datetime
    paper_count: int = 0
    model_config = {"from_attributes": True}

class WorkspaceUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    icon:        Optional[str] = None
    color:       Optional[str] = None


# ═════════════════════════════════════════════════════════════
# PAPER
# ═════════════════════════════════════════════════════════════

class PaperSearchResult(BaseModel):
    """Returned by arXiv / PubMed search – not yet stored in DB."""
    external_id:    str
    source:         str
    title:          str
    authors:        List[str]
    abstract:       str
    published_date: str
    url:            str
    pdf_url:        Optional[str] = None
    journal:        Optional[str] = None
    venue:          Optional[str] = None
    doi:            Optional[str] = None
    citations:      int = 0
    tags:           List[str] = []

class PaperImport(BaseModel):
    external_id:    Optional[str] = None
    source:         Optional[str] = "arxiv"
    title:          str
    authors:        Optional[List[str]] = []
    abstract:       Optional[str] = None
    published_date: Optional[str] = None
    url:            Optional[str] = None
    pdf_url:        Optional[str] = None
    journal:        Optional[str] = None
    venue:          Optional[str] = None
    doi:            Optional[str] = None
    citations:      Optional[int] = 0
    tags:           Optional[List[str]] = []
    workspace_id:   Optional[int] = None

class PaperOut(BaseModel):
    id:             int
    external_id:    Optional[str]
    source:         Optional[str]
    title:          str
    authors:        Optional[str]   # raw JSON string
    abstract:       Optional[str]
    published_date: Optional[str]
    url:            Optional[str]
    pdf_url:        Optional[str]
    journal:        Optional[str]
    venue:          Optional[str]
    doi:            Optional[str]
    citations:      int
    tags:           Optional[str]   # raw JSON string
    ai_summary:     Optional[str]
    owner_id:       int
    created_at:     datetime
    model_config = {"from_attributes": True}

class SemanticSearchResult(BaseModel):
    paper:      PaperOut
    similarity: float


# ═════════════════════════════════════════════════════════════
# CHAT / AI
# ═════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    content:      str
    workspace_id: int

class ChatResponse(BaseModel):
    response:     str
    workspace_id: int
    model:        str

class ConversationOut(BaseModel):
    id:           int
    workspace_id: int
    role:         str
    content:      str
    created_at:   datetime
    model_config = {"from_attributes": True}


# ═════════════════════════════════════════════════════════════
# AI TOOLS  (AI Summaries, Key Insights, Literature Review)
# ═════════════════════════════════════════════════════════════

class AIToolRequest(BaseModel):
    paper_ids:    List[int]
    tool_type:    str    # summarize | insights | literature_review

class AIToolResponse(BaseModel):
    tool_type: str
    result:    str
    model:     str


# ═════════════════════════════════════════════════════════════
# UPLOAD / DOC SPACE
# ═════════════════════════════════════════════════════════════

class DocumentOut(BaseModel):
    id:           int
    name:         str
    doc_type:     str
    size_bytes:   int
    page_count:   int
    workspace_id: Optional[int]
    created_at:   datetime
    model_config = {"from_attributes": True}

class NoteCreate(BaseModel):
    name:         str
    content:      str
    workspace_id: Optional[int] = None

class UploadResponse(BaseModel):
    document_id:  int
    name:         str
    pages:        int
    size_bytes:   int
    ai_summary:   Optional[str]
    workspace:    Optional[str]


# ═════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═════════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_papers:     int
    total_workspaces: int
    ai_queries_today: int
    total_citations:  int
    recent_papers:    List[PaperOut]
    active_workspaces: List[WorkspaceOut]
