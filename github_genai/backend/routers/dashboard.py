# backend/routers/dashboard.py
"""
Dashboard endpoint – powers the Dashboard page KPI cards and charts.

GET /dashboard/stats  – aggregated stats for the current user
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.database import (
    ConversationHistory, Paper, User, Workspace, WorkspacePaper, get_db,
)
from models.schemas  import DashboardStats, PaperOut, WorkspaceOut
from utils.security  import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Returns everything the Dashboard page needs in a single request:
    • 4 KPI cards (papers, workspaces, AI queries today, citations)
    • Recent papers (last 5)
    • Active workspaces (top 3 by paper count)
    """
    uid = current_user.id

    # KPI 1: Total papers
    total_papers = db.query(func.count(Paper.id)).filter_by(owner_id=uid).scalar() or 0

    # KPI 2: Total workspaces
    total_workspaces = db.query(func.count(Workspace.id)).filter_by(owner_id=uid).scalar() or 0

    # KPI 3: AI queries today
    today_start    = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ai_queries_today = (
        db.query(func.count(ConversationHistory.id))
        .join(Workspace, ConversationHistory.workspace_id == Workspace.id)
        .filter(
            Workspace.owner_id == uid,
            ConversationHistory.role == "user",
            ConversationHistory.created_at >= today_start,
        )
        .scalar() or 0
    )

    # KPI 4: Total citations across all papers
    total_citations = (
        db.query(func.sum(Paper.citations))
        .filter_by(owner_id=uid)
        .scalar() or 0
    )

    # Recent papers (last 5 imported)
    recent_papers = (
        db.query(Paper)
        .filter_by(owner_id=uid)
        .order_by(Paper.created_at.desc())
        .limit(5)
        .all()
    )

    # Active workspaces – top 3 by paper count
    workspaces = db.query(Workspace).filter_by(owner_id=uid).all()
    ws_with_count = []
    for ws in workspaces:
        count = db.query(WorkspacePaper).filter_by(workspace_id=ws.id).count()
        out   = WorkspaceOut.model_validate(ws)
        out.paper_count = count
        ws_with_count.append((count, out))
    ws_with_count.sort(key=lambda x: x[0], reverse=True)
    active_workspaces = [ws for _, ws in ws_with_count[:3]]

    return DashboardStats(
        total_papers      = total_papers,
        total_workspaces  = total_workspaces,
        ai_queries_today  = ai_queries_today,
        total_citations   = int(total_citations),
        recent_papers     = recent_papers,
        active_workspaces = active_workspaces,
    )
