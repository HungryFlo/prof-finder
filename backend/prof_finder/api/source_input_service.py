"""Shared helpers for SourceInput ingestion (PDF + ArXiv)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests


ARXIV_API_URL = "https://export.arxiv.org/api/query"


def extract_markdown_from_pdf(pdf_path: Path) -> str:
    """Extract markdown text from PDF using pymupdf4llm."""
    try:
        import pymupdf4llm  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/runtime issue
        raise RuntimeError("pymupdf4llm not available") from exc

    markdown = pymupdf4llm.to_markdown(str(pdf_path))
    if not isinstance(markdown, str):
        raise RuntimeError("PDF markdown extraction returned invalid data")
    return markdown


def normalize_arxiv_id(url: str) -> str:
    """Normalize ArXiv URL/ID into canonical id (drop version suffix)."""
    raw = url.strip()
    if not raw:
        raise ValueError("ArXiv 链接不能为空")

    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", raw):
        arxiv_id = raw
    else:
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if "arxiv.org" not in host:
            raise ValueError("请输入有效的 ArXiv 链接")

        path = parsed.path.strip("/")
        if path.startswith("abs/"):
            arxiv_id = path[4:]
        elif path.startswith("pdf/"):
            arxiv_id = path[4:]
            if arxiv_id.endswith(".pdf"):
                arxiv_id = arxiv_id[:-4]
        else:
            raise ValueError("不支持的 ArXiv 链接格式")

    arxiv_id = arxiv_id.split("v", 1)[0]
    if not re.match(r"^\d{4}\.\d{4,5}$", arxiv_id):
        raise ValueError("无法识别 ArXiv ID")
    return arxiv_id


def fetch_arxiv_metadata(canonical_id: str, timeout: int = 15) -> Dict[str, Optional[str]]:
    """Fetch metadata from ArXiv official API."""
    response = requests.get(
        ARXIV_API_URL,
        params={"id_list": canonical_id},
        timeout=timeout,
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ValueError("ArXiv 未返回有效条目")

    title = _text_or_none(entry.find("atom:title", ns))
    abstract = _text_or_none(entry.find("atom:summary", ns))
    pdf_url = None
    for link in entry.findall("atom:link", ns):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href")
            break

    return {
        "title": title,
        "abstract": abstract,
        "pdf_url": pdf_url,
    }


def download_to_temp_file(url: str, suffix: str = ".pdf", timeout: int = 30) -> Path:
    """Download URL content to a temporary file and return path."""
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # Close leaked file descriptor
    Path(temp_path).unlink(missing_ok=True)
    target = Path(temp_path)
    response = requests.get(url, timeout=timeout, stream=True)
    response.raise_for_status()
    with open(target, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return target


def safe_delete_file(path: Optional[str]) -> None:
    """Best-effort temporary file cleanup."""
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        # Cleanup failures are non-fatal by design.
        return


def _text_or_none(node: Optional[ET.Element]) -> Optional[str]:
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def keep_paper_summaries_excluding(
    items: Optional[list],
    exclude: Optional[set[str]] = None,
) -> list:
    """Drop summaries whose source_type is in ``exclude``."""
    excluded = exclude if exclude is not None else {"scholar_pub"}
    out: list = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if item.get("source_type") in excluded:
            continue
        out.append(item)
    return out


def keep_non_scholar_paper_summaries(items: Optional[list]) -> list:
    """Drop auto-generated Scholar publication summaries; keep PDF/ArXiv and other entries."""
    return keep_paper_summaries_excluding(items, {"scholar_pub"})


def build_paper_summary_from_scholar_publication(
    pub: dict, summarizer=None, language: str = "en"
) -> dict:
    """Build a paper_summaries record from a Google Scholar publication dict."""
    if summarizer is None:
        from ..llm.paper_summarizer import PaperSummarizer

        summarizer = PaperSummarizer()

    title = (pub.get("title") or "").strip() or "Untitled Paper"
    abstract = (pub.get("abstract") or "").strip()
    author_pub_id = pub.get("author_pub_id")

    result = summarizer.summarize_with_fallback(
        source_type="scholar_pub", title=title, content=abstract, language=language
    )
    rec: dict = {
        "source_type": "scholar_pub",
        "title": title,
        "summary": result.get("summary") or "",
        "keywords": (result.get("keywords") or [])[:12],
    }
    if author_pub_id:
        rec["scholar_author_pub_id"] = author_pub_id
    return rec


def build_paper_summary_from_source(source_input: dict, summarizer=None, language: str = "zh") -> Optional[dict]:
    """Build a structured paper summary record from one source input."""
    source_type = source_input.get("source_type")
    if source_type not in {"pdf", "arxiv"}:
        return None

    title = (source_input.get("title") or "").strip()
    if not title:
        title = (source_input.get("original_name") or "").strip()
    if not title and source_input.get("canonical_id"):
        title = f"arXiv:{source_input.get('canonical_id')}"
    if not title:
        title = "Untitled Paper"

    summary = ""
    keywords: list[str] = []
    raw_content = ""
    if source_type == "arxiv":
        raw_content = source_input.get("abstract") or ""
    else:
        raw_content = source_input.get("extracted_markdown") or source_input.get("extracted_text") or ""

    if summarizer is not None:
        llm_result = summarizer.summarize_with_fallback(
            source_type=source_type,
            title=title,
            content=raw_content,
            language=language,
        )
        summary = llm_result.get("summary") or ""
        keywords = llm_result.get("keywords") or []
    else:
        summary = _summarize_text(raw_content, max_chars=500)
        keywords = _extract_keywords(raw_content)

    return {
        "source_input_id": source_input.get("id"),
        "source_type": source_type,
        "title": title,
        "summary": summary,
        "keywords": keywords[:12],
    }


def _summarize_text(text: str, max_chars: int = 500) -> str:
    """Heuristic summary: keep non-empty lines and truncate."""
    cleaned_lines = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("#").strip()
        if not line:
            continue
        if line.startswith("![]("):
            continue
        cleaned_lines.append(line)

    joined = " ".join(cleaned_lines)
    if len(joined) <= max_chars:
        return joined
    return joined[: max_chars - 1].rstrip() + "…"


def _extract_keywords(text: str) -> list[str]:
    """Extract lightweight keyword set from technical text."""
    tech_terms = [
        "machine learning",
        "deep learning",
        "nlp",
        "natural language",
        "computer vision",
        "language model",
        "llm",
        "transformer",
        "bert",
        "gpt",
        "recommendation",
        "knowledge graph",
        "data mining",
        "optimization",
        "security",
        "robotics",
        "reinforcement learning",
    ]
    lower = text.lower()
    found = []
    for term in tech_terms:
        if term in lower:
            found.append(term)
    return found
