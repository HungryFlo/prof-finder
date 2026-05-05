"""AI-adjacent helpers for paper summarization from various source types.

These functions wrap the pure summarise_paper workflow for specific input formats
(Scholar publications, PDF/ArXiv source inputs). They are DB-free.
"""

from __future__ import annotations

from typing import Optional

from ..ai_workflows.provider import LLMProvider
from ..ai_workflows.workflows import summarize_paper
from ..llm.paper_summarizer import PaperSummarizer


def build_paper_summary_from_scholar_publication(
    pub: dict,
    provider: LLMProvider | None = None,
    language: str = "en",
) -> dict:
    """Build a paper_summaries record from a Google Scholar publication dict.

    Args:
        pub: Dict with 'title', 'abstract', optionally 'author_pub_id'.
        provider: Optional LLM provider.
        language: Output language.

    Returns:
        Dict with source_type, title, summary, keywords, and optionally scholar_author_pub_id.
    """
    title = (pub.get("title") or "").strip() or "Untitled Paper"
    abstract = (pub.get("abstract") or "").strip()
    author_pub_id = pub.get("author_pub_id")

    result = summarize_paper(
        source_type="scholar_pub",
        title=title,
        content=abstract,
        language=language,
        provider=provider,
    )
    rec: dict = {
        "source_type": "scholar_pub",
        "title": title,
        "summary": result.summary,
        "keywords": result.keywords[:12],
    }
    if author_pub_id:
        rec["scholar_author_pub_id"] = author_pub_id
    return rec


def build_paper_summary_from_source(
    source_input: dict,
    provider: LLMProvider | None = None,
    language: str = "zh",
) -> Optional[dict]:
    """Build a structured paper summary record from one source input.

    Args:
        source_input: Dict with source_type, title, abstract, extracted_markdown, etc.
        provider: Optional LLM provider.
        language: Output language.

    Returns:
        Dict with source_input_id, source_type, title, summary, keywords, or None.
    """
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

    raw_content = ""
    if source_type == "arxiv":
        raw_content = source_input.get("abstract") or ""
    else:
        raw_content = source_input.get("extracted_markdown") or source_input.get("extracted_text") or ""

    result = summarize_paper(
        source_type=source_type,
        title=title,
        content=raw_content,
        language=language,
        provider=provider,
    )
    return {
        "source_input_id": source_input.get("id"),
        "source_type": source_type,
        "title": title,
        "summary": result.summary,
        "keywords": result.keywords[:12],
    }
