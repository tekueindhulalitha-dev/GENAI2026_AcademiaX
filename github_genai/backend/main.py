# backend/main.py
"""
ResearchHub AI  –  FastAPI Application Entry Point
===================================================
Starts the server, initialises the database, configures CORS,
and registers all routers.

Run:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Interactive API docs:
    http://localhost:8000/docs   ← Swagger UI
    http://localhost:8000/redoc  ← ReDoc
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import init_db
from routers.auth        import router as auth_router
from routers.chat        import router as chat_router
from routers.dashboard   import router as dashboard_router
from routers.papers      import router as papers_router
from routers.upload      import router as upload_router
from routers.workspaces  import router as workspaces_router

load_dotenv()

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title       = "ResearchHub AI API",
    description = "Intelligent Research Paper Management powered by Agentic AI",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS  (allows Streamlit frontend on port 8501) ────────────
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://localhost:3000")
origins     = [o.strip() for o in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Database init ─────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(workspaces_router)
app.include_router(papers_router)
app.include_router(chat_router)
app.include_router(upload_router)


# ── Health check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"message": "ResearchHub AI API is running ✅", "version": "2.0.0"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
