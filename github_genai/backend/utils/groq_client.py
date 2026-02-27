# backend/utils/groq_client.py
"""
Groq API wrapper powering:
  • Workspace chatbot (AI Assistant page)
  • AI Summaries, Key Insights, Literature Review (AI Tools)
  • PDF auto-summary (Upload PDF page)
"""

import os
import logging
from typing import List, Dict, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

# ── Client & model config ─────────────────────────────────────
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_CONFIG = {
    "model":       "llama-3.3-70b-versatile",
    "temperature": 0.3,
    "max_tokens":  2000,
    "top_p":       0.9,
}


# ═════════════════════════════════════════════════════════════
# CHATBOT  –  used by AI Assistant page
# ═════════════════════════════════════════════════════════════

def chat_with_context(
    user_message:     str,
    workspace_papers: List[Dict],
    conversation_history: List[Dict],
) -> str:
    """
    Answer a researcher's question using the papers in their workspace.

    workspace_papers: list of dicts with keys title, authors, abstract
    conversation_history: list of {"role": "user"|"assistant", "content": str}
    """
    # Build research context from papers
    context_parts = []
    for p in workspace_papers:
        authors = p.get("authors", "Unknown")
        if isinstance(authors, list):
            authors = ", ".join(authors)
        context_parts.append(
            f"Paper: {p.get('title', 'Untitled')}\n"
            f"Authors: {authors}\n"
            f"Abstract: {p.get('abstract', 'No abstract')}"
        )
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No papers loaded in this workspace."

    system_prompt = (
        "You are ResearchHub AI, an expert research assistant. "
        "You have access to the following research papers in the user's workspace:\n\n"
        f"{context}\n\n"
        "Answer questions thoroughly, cite specific papers when relevant, "
        "and provide actionable research insights. Use markdown formatting."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Include recent conversation history (last 10 turns)
    for turn in conversation_history[-10:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = _client.chat.completions.create(messages=messages, **MODEL_CONFIG)
        return response.choices[0].message.content
    except Exception as exc:
        logger.error(f"Groq chat error: {exc}")
        raise RuntimeError(f"AI service error: {exc}")


# ═════════════════════════════════════════════════════════════
# AI TOOLS  –  used by Workspaces AI Tools tab
# ═════════════════════════════════════════════════════════════

def generate_summaries(papers: List[Dict]) -> str:
    """Generate a concise AI summary for each selected paper."""
    if not papers:
        return "No papers selected."

    paper_list = "\n\n".join(
        f"**{i+1}. {p.get('title', 'Untitled')}**\n"
        f"Authors: {p.get('authors', 'Unknown')}\n"
        f"Abstract: {p.get('abstract', 'No abstract available')}"
        for i, p in enumerate(papers)
    )

    prompt = (
        "Generate a concise, informative summary (3-5 sentences) for each of the "
        "following research papers. Format each summary with the paper title as a header.\n\n"
        + paper_list
    )

    return _call_groq(prompt)


def extract_key_insights(papers: List[Dict]) -> str:
    """Extract key insights, trends, and findings across selected papers."""
    if not papers:
        return "No papers selected."

    paper_list = "\n\n".join(
        f"Paper {i+1}: {p.get('title', 'Untitled')}\n{p.get('abstract', '')}"
        for i, p in enumerate(papers)
    )

    prompt = (
        "Analyze the following research papers and extract:\n"
        "1. **Key Insights** – the most important findings\n"
        "2. **Common Themes** – recurring concepts across papers\n"
        "3. **Research Gaps** – open problems identified\n"
        "4. **Trends** – directions the field is moving\n\n"
        "Use markdown with clear headers and bullet points.\n\n"
        + paper_list
    )

    return _call_groq(prompt)


def generate_literature_review(papers: List[Dict]) -> str:
    """Generate a structured academic literature review."""
    if not papers:
        return "No papers selected."

    paper_list = "\n\n".join(
        f"[{i+1}] {p.get('title', 'Untitled')} — {p.get('authors', 'Unknown')} ({p.get('published_date', 'n.d.')})\n"
        f"Abstract: {p.get('abstract', '')}"
        for i, p in enumerate(papers)
    )

    prompt = (
        "Write a comprehensive academic literature review for the following papers. "
        "Structure it with these sections:\n"
        "## 1. Overview\n"
        "## 2. Key Findings\n"
        "## 3. Methodological Approaches\n"
        "## 4. Comparative Analysis\n"
        "## 5. Research Gaps & Future Directions\n"
        "## 6. Conclusion\n\n"
        "Cite papers as [1], [2], etc. Use formal academic language.\n\n"
        + paper_list
    )

    return _call_groq(prompt, max_tokens=3000)


def summarize_pdf_text(text: str, title: str = "document") -> str:
    """Generate an AI summary from raw PDF text (Upload PDF page)."""
    # Truncate very long documents to fit context window
    truncated = text[:6000] + ("…[truncated]" if len(text) > 6000 else "")

    prompt = (
        f"Summarize the following research paper titled '{title}' in 7 bullet points. "
        "Cover: main topic, research question, methodology, key findings, "
        "conclusions, limitations, and implications.\n\n"
        + truncated
    )

    return _call_groq(prompt)


# ═════════════════════════════════════════════════════════════
# INTERNAL HELPER
# ═════════════════════════════════════════════════════════════

def _call_groq(prompt: str, max_tokens: int = 2000) -> str:
    config = {**MODEL_CONFIG, "max_tokens": max_tokens}
    try:
        response = _client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **config,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error(f"Groq API error: {exc}")
        raise RuntimeError(f"AI service error: {exc}")
