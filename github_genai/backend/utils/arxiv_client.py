# backend/utils/arxiv_client.py
"""
External Layer – arXiv Atom/XML feed.
No API key required. Returns PaperSearchResult objects.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional

import httpx

from models.schemas import PaperSearchResult

logger          = logging.getLogger(__name__)
ARXIV_BASE      = "http://export.arxiv.org/api/query"
ATOM_NS         = "http://www.w3.org/2005/Atom"
TIMEOUT         = 20


async def search_arxiv(query: str, max_results: int = 10) -> List[PaperSearchResult]:
    params = {
        "search_query": f"all:{query}",
        "start":        0,
        "max_results":  max_results,
        "sortBy":       "relevance",
        "sortOrder":    "descending",
    }
    url = f"{ARXIV_BASE}?{urllib.parse.urlencode(params)}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(url)
            r.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"arXiv error: {e}")
        return []
    return _parse(r.text)


async def get_arxiv_paper(arxiv_id: str) -> Optional[PaperSearchResult]:
    clean = re.sub(r"https?://arxiv\.org/abs/", "", arxiv_id).strip()
    params = {"id_list": clean, "max_results": 1}
    url = f"{ARXIV_BASE}?{urllib.parse.urlencode(params)}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(url)
            r.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"arXiv single fetch error: {e}")
        return None
    results = _parse(r.text)
    return results[0] if results else None


def _parse(xml_text: str) -> List[PaperSearchResult]:
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results

    ns = {"a": ATOM_NS, "ax": "http://arxiv.org/schemas/atom"}

    for entry in root.findall("a:entry", ns):
        id_el  = entry.find("a:id",       ns)
        ttl_el = entry.find("a:title",    ns)
        abs_el = entry.find("a:summary",  ns)
        pub_el = entry.find("a:published",ns)

        arxiv_url = (id_el.text  or "").strip() if id_el  else ""
        arxiv_id  = re.sub(r"https?://arxiv\.org/abs/", "", arxiv_url).strip()
        title     = _clean(ttl_el.text if ttl_el else "Untitled")
        abstract  = _clean(abs_el.text if abs_el else "")
        pub_date  = (pub_el.text or "")[:10] if pub_el else ""

        authors = [
            _clean(n.text)
            for auth in entry.findall("a:author", ns)
            if (n := auth.find("a:name", ns)) is not None
        ]

        pdf_url = None
        for link in entry.findall("a:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href", "").replace("http://", "https://")
                break

        doi_el  = entry.find("ax:doi", ns)
        doi     = doi_el.text.strip() if doi_el is not None and doi_el.text else None
        jrnl_el = entry.find("ax:journal_ref", ns)
        journal = jrnl_el.text.strip() if jrnl_el is not None and jrnl_el.text else None

        # Auto-generate topic tags from title keywords
        tags = _auto_tags(title)

        if not arxiv_id:
            continue

        results.append(PaperSearchResult(
            external_id    = arxiv_id,
            source         = "arxiv",
            title          = title,
            authors        = authors,
            abstract       = abstract,
            published_date = pub_date,
            url            = arxiv_url or f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url        = pdf_url   or f"https://arxiv.org/pdf/{arxiv_id}",
            journal        = journal,
            venue          = journal,
            doi            = doi,
            citations      = 0,
            tags           = tags,
        ))

    logger.info(f"arXiv: {len(results)} results")
    return results


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _auto_tags(title: str) -> List[str]:
    """Generate simple tags from title keywords."""
    keywords = {
        "transformer": "Transformers", "attention": "Attention",
        "bert": "BERT", "gpt": "GPT", "llm": "LLM",
        "diffusion": "Diffusion", "gan": "GANs",
        "reinforcement": "RL", "vision": "Computer Vision",
        "image": "Computer Vision", "medical": "Medical AI",
        "neural": "Deep Learning", "language": "NLP",
        "agent": "Agents", "graph": "Graph Neural Networks",
    }
    low = title.lower()
    return list({v for k, v in keywords.items() if k in low})[:3]
