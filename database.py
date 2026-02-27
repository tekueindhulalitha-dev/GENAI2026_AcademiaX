# backend/models/database.py
"""
PostgreSQL schema via SQLAlchemy ORM.

Tables
──────
users               – registered researcher accounts
workspaces          – project containers per user
papers              – imported research papers
workspace_papers    – many-to-many: workspace ↔ paper
vector_embeddings   – 384-dim sentence-transformer vectors
conversation_history– chatbot Q&A history per workspace
documents           – uploaded PDFs / generated reports (Doc Space)
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://researchuser:password@localhost/researchhub",
)

engine       = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


# ── Dependency ────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═════════════════════════════════════════════════════════════
# MODELS
# ═════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255))
    plan            = Column(String(50), default="free")   # free | pro | enterprise
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    workspaces    = relationship("Workspace",           back_populates="owner",  cascade="all, delete")
    papers        = relationship("Paper",               back_populates="owner",  cascade="all, delete")
    documents     = relationship("Document",            back_populates="owner",  cascade="all, delete")


class Workspace(Base):
    __tablename__ = "workspaces"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    icon        = Column(String(10),  default="📁")
    color       = Column(String(20),  default="#6c63ff")
    owner_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner         = relationship("User",                back_populates="workspaces")
    papers        = relationship("WorkspacePaper",      back_populates="workspace", cascade="all, delete")
    conversations = relationship("ConversationHistory", back_populates="workspace", cascade="all, delete")


class Paper(Base):
    __tablename__ = "papers"

    id              = Column(Integer, primary_key=True, index=True)
    external_id     = Column(String(255))          # arXiv ID or PubMed PMID
    source          = Column(String(50))           # arxiv | pubmed | upload
    title           = Column(Text, nullable=False)
    authors         = Column(Text)                 # JSON-encoded list
    abstract        = Column(Text)
    published_date  = Column(String(50))
    url             = Column(Text)
    pdf_url         = Column(Text)
    journal         = Column(String(255))
    venue           = Column(String(255))
    doi             = Column(String(255))
    citations       = Column(Integer, default=0)
    tags            = Column(Text)                 # JSON-encoded list
    full_text       = Column(Text)                 # extracted PDF text
    ai_summary      = Column(Text)                 # Groq-generated summary
    owner_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    owner       = relationship("User",            back_populates="papers")
    workspaces  = relationship("WorkspacePaper",  back_populates="paper",  cascade="all, delete")
    embedding   = relationship("VectorEmbedding", back_populates="paper",  uselist=False, cascade="all, delete")


class WorkspacePaper(Base):
    __tablename__ = "workspace_papers"

    id           = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    paper_id     = Column(Integer, ForeignKey("papers.id"),     nullable=False)
    notes        = Column(Text)
    added_at     = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="papers")
    paper     = relationship("Paper",     back_populates="workspaces")


class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"

    id         = Column(Integer, primary_key=True, index=True)
    paper_id   = Column(Integer, ForeignKey("papers.id"), unique=True, nullable=False)
    vector     = Column(Text, nullable=False)      # CSV of 384 floats
    model_name = Column(String(100), default="all-MiniLM-L6-v2")
    created_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="embedding")


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id           = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    role         = Column(String(20), nullable=False)   # user | assistant
    content      = Column(Text, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="conversations")


class Document(Base):
    """Doc Space – stores uploaded PDFs and AI-generated reports."""
    __tablename__ = "documents"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(255), nullable=False)
    doc_type     = Column(String(50), default="pdf")   # pdf | note | report
    content      = Column(Text)                        # extracted text or note body
    size_bytes   = Column(Integer, default=0)
    page_count   = Column(Integer, default=0)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    owner_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")


# ── Create all tables ─────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
