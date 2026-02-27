# backend/routers/workspaces.py
"""
Workspace endpoints matching the Workspaces page.

GET    /workspaces/           – list all user workspaces
POST   /workspaces/           – create new workspace
GET    /workspaces/{id}       – get single workspace
PATCH  /workspaces/{id}       – update workspace
DELETE /workspaces/{id}       – delete workspace
GET    /workspaces/{id}/papers – list papers in workspace
POST   /workspaces/{id}/papers/{paper_id} – add paper to workspace
DELETE /workspaces/{id}/papers/{paper_id} – remove paper from workspace
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import (
    Paper, User, Workspace, WorkspacePaper, get_db,
)
from models.schemas  import (
    PaperOut, WorkspaceCreate, WorkspaceOut, WorkspaceUpdate,
)
from utils.security  import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# ── List ──────────────────────────────────────────────────────
@router.get("/", response_model=List[WorkspaceOut])
def list_workspaces(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    workspaces = db.query(Workspace).filter_by(owner_id=current_user.id).all()
    result = []
    for ws in workspaces:
        count = db.query(WorkspacePaper).filter_by(workspace_id=ws.id).count()
        out   = WorkspaceOut.model_validate(ws)
        out.paper_count = count
        result.append(out)
    return result


# ── Create ────────────────────────────────────────────────────
@router.post("/", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(
    data:         WorkspaceCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    ws = Workspace(
        name        = data.name,
        description = data.description,
        icon        = data.icon  or "📁",
        color       = data.color or "#6c63ff",
        owner_id    = current_user.id,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    out = WorkspaceOut.model_validate(ws)
    out.paper_count = 0
    return out


# ── Get one ───────────────────────────────────────────────────
@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(
    workspace_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    ws = _get_or_404(db, workspace_id, current_user.id)
    out = WorkspaceOut.model_validate(ws)
    out.paper_count = db.query(WorkspacePaper).filter_by(workspace_id=ws.id).count()
    return out


# ── Update ────────────────────────────────────────────────────
@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(
    workspace_id: int,
    data:         WorkspaceUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    ws = _get_or_404(db, workspace_id, current_user.id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ws, field, value)
    db.commit()
    db.refresh(ws)
    out = WorkspaceOut.model_validate(ws)
    out.paper_count = db.query(WorkspacePaper).filter_by(workspace_id=ws.id).count()
    return out


# ── Delete ────────────────────────────────────────────────────
@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    ws = _get_or_404(db, workspace_id, current_user.id)
    db.delete(ws)
    db.commit()


# ── Papers in workspace ───────────────────────────────────────
@router.get("/{workspace_id}/papers", response_model=List[PaperOut])
def list_workspace_papers(
    workspace_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    _get_or_404(db, workspace_id, current_user.id)
    papers = (
        db.query(Paper)
        .join(WorkspacePaper, WorkspacePaper.paper_id == Paper.id)
        .filter(WorkspacePaper.workspace_id == workspace_id)
        .all()
    )
    return papers


@router.post("/{workspace_id}/papers/{paper_id}", status_code=status.HTTP_201_CREATED)
def add_paper_to_workspace(
    workspace_id: int,
    paper_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    _get_or_404(db, workspace_id, current_user.id)
    paper = db.query(Paper).filter_by(id=paper_id, owner_id=current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    exists = db.query(WorkspacePaper).filter_by(
        workspace_id=workspace_id, paper_id=paper_id
    ).first()
    if not exists:
        link = WorkspacePaper(workspace_id=workspace_id, paper_id=paper_id)
        db.add(link)
        db.commit()
    return {"message": "Paper added to workspace."}


@router.delete("/{workspace_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_paper_from_workspace(
    workspace_id: int,
    paper_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    _get_or_404(db, workspace_id, current_user.id)
    link = db.query(WorkspacePaper).filter_by(
        workspace_id=workspace_id, paper_id=paper_id
    ).first()
    if link:
        db.delete(link)
        db.commit()


# ── Helper ────────────────────────────────────────────────────
def _get_or_404(db: Session, workspace_id: int, owner_id: int) -> Workspace:
    ws = db.query(Workspace).filter_by(id=workspace_id, owner_id=owner_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws
