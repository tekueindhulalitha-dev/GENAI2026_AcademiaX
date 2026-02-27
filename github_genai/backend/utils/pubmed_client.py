# backend/utils/pubmed_client.py
"""
External Layer – NCBI Entrez E-utilities for PubMed.
Two-step: esearch (IDs) → efetch (full records).
Set NCBI_API_KEY in .env for 10 req/s instead of 3 req/s.
"""

from __future__ import annotations

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import httpx

from models.schemas import PaperSearchResult

logger       = logging.getLogger(__name__)
ESEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
TIMEOUT      = 20


async def search_pubmed(query: str, max_results: int = 10) -> List[PaperSearchResult]:
    pmids = await _esearch(query, max_results)
    if not pmids:
        return []
    return await _efetch(pmids)


async def get_pubmed_paper(pmid: str) -> Optional[PaperSearchResult]:
    papers = await _efetch([pmid])
    return papers[0] if papers else None


async def _esearch(query: str, max_results: int) -> List[str]:
    params: Dict = {"db": "pubmed", "term": query, "retmax": max_results,
                    "retmode": "json", "sort": "relevance"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(ESEARCH_URL, params=params)
            r.raise_for_status()
            return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PubMed esearch error: {e}")
        return []


async def _efetch(pmids: List[str]) -> List[PaperSearchResult]:
    params: Dict = {"db": "pubmed", "id": ",".join(pmids),
                    "retmode": "xml", "rettype": "abstract"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(EFETCH_URL, params=params)
            r.raise_for_status()
            return _parse_xml(r.text)
    except Exception as e:
        logger.error(f"PubMed efetch error: {e}")
        return []


def _parse_xml(xml_text: str) -> List[PaperSearchResult]:
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results

    for article in root.findall(".//PubmedArticle"):
        try:
            r = _parse_article(article)
            if r:
                results.append(r)
        except Exception as e:
            logger.warning(f"Skipping article: {e}")

    logger.info(f"PubMed: {len(results)} results")
    return results


def _parse_article(article: ET.Element) -> Optional[PaperSearchResult]:
    pmid_el = article.find(".//PMID")
    pmid    = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else None
    if not pmid:
        return None

    title_el = article.find(".//ArticleTitle")
    title    = _inner_text(title_el) if title_el is not None else "Untitled"

    abstract = " ".join(
        (_inner_text(ab) or "")
        for ab in article.findall(".//AbstractText")
    )

    authors = []
    for auth in article.findall(".//Author"):
        last  = auth.findtext("LastName",  "")
        first = auth.findtext("ForeName",  "")
        col   = auth.findtext("CollectiveName", "")
        name  = f"{first} {last}".strip() or col
        if name:
            authors.append(name)

    journal = (article.findtext(".//Journal/Title") or
               article.findtext(".//Journal/ISOAbbreviation") or "")

    pub_date = _pubmed_date(article)

    doi = None
    for id_el in article.findall(".//ArticleId"):
        if id_el.attrib.get("IdType") == "doi":
            doi = (id_el.text or "").strip() or None
            break

    tags = _auto_tags(title)

    return PaperSearchResult(
        external_id    = pmid,
        source         = "pubmed",
        title          = _clean(title),
        authors        = authors,
        abstract       = _clean(abstract),
        published_date = pub_date,
        url            = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        pdf_url        = f"https://doi.org/{doi}" if doi else None,
        journal        = _clean(journal) or None,
        venue          = _clean(journal) or None,
        doi            = doi,
        citations      = 0,
        tags           = tags,
    )


def _pubmed_date(article: ET.Element) -> str:
    for path in [".//PubDate", ".//ArticleDate",
                 ".//PubMedPubDate[@PubStatus='pubmed']"]:
        d = article.find(path)
        if d is not None:
            year  = d.findtext("Year", "")
            month = d.findtext("Month", "01")
            day   = d.findtext("Day",   "01")
            if year:
                m_map = {"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06",
                         "Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}
                return f"{year}-{m_map.get(month, month).zfill(2)}-{day.zfill(2)}"
    return ""


def _inner_text(el: Optional[ET.Element]) -> str:
    return "".join(el.itertext()) if el is not None else ""


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _auto_tags(title: str) -> List[str]:
    keywords = {
        "cancer": "Oncology", "covid": "Infectious Disease", "mri": "Medical Imaging",
        "gene": "Genomics", "protein": "Proteomics", "drug": "Pharmacology",
        "neural": "Neuroscience", "clinical": "Clinical Research",
        "deep learning": "Deep Learning", "machine learning": "ML",
    }
    low = title.lower()
    return list({v for k, v in keywords.items() if k in low})[:3]
