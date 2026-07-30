"""Helpers for experience pools and story formatting."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models.schema import (
    ExperienceCluster,
    ExperiencePool,
    ExperienceSeed,
    ExperienceStory,
)

STORY_FIELDS = (
    "origin",
    "process",
    "outcome",
    "problems",
    "setbacks",
    "knowledge",
    "insights",
    "freeform",
)

STORY_FIELD_LABELS_ZH = {
    "origin": "起因",
    "process": "经过",
    "outcome": "结果",
    "problems": "遇到的问题",
    "setbacks": "波折",
    "knowledge": "用到的知识",
    "insights": "灵机一动 / 收获",
    "freeform": "其它",
}

STORY_FIELD_LABELS_EN = {
    "origin": "Origin",
    "process": "Process",
    "outcome": "Outcome",
    "problems": "Problems",
    "setbacks": "Setbacks",
    "knowledge": "Knowledge used",
    "insights": "Insights",
    "freeform": "Other notes",
}


def story_completion(story: ExperienceStory) -> str:
    """Return empty|partial|complete based on filled narrative fields."""
    values = [getattr(story, f) or "" for f in STORY_FIELDS]
    filled = sum(1 for v in values if str(v).strip())
    if filled == 0:
        return "empty"
    if filled >= 4:
        return "complete"
    return "partial"


def format_story_text(
    story: ExperienceStory,
    seed_content: str = "",
    language: str = "zh",
) -> str:
    """Format one story as readable text for LLM prompts."""
    labels = STORY_FIELD_LABELS_ZH if language == "zh" else STORY_FIELD_LABELS_EN
    lines: list[str] = []
    title = (seed_content or "").strip()
    if title:
        lines.append(f"## {title}")
    for field in STORY_FIELDS:
        value = (getattr(story, field) or "").strip()
        if value:
            lines.append(f"**{labels[field]}**: {value}")
    return "\n".join(lines).strip()


def get_pool_for_user(
    session: Session, pool_id: int, user_id: int
) -> Optional[ExperiencePool]:
    return (
        session.query(ExperiencePool)
        .filter(ExperiencePool.id == pool_id, ExperiencePool.user_id == user_id)
        .first()
    )


def list_detail_seeds(session: Session, pool_id: int) -> list[ExperienceSeed]:
    """Active seeds that are clustered or marked standalone."""
    return (
        session.query(ExperienceSeed)
        .filter(
            ExperienceSeed.pool_id == pool_id,
            ExperienceSeed.status == "active",
        )
        .filter(
            (ExperienceSeed.cluster_id.isnot(None)) | (ExperienceSeed.standalone.is_(True))
        )
        .order_by(ExperienceSeed.sort_order.asc(), ExperienceSeed.id.asc())
        .all()
    )


def ensure_story_for_seed(session: Session, seed: ExperienceSeed) -> ExperienceStory:
    if seed.story is not None:
        return seed.story
    story = ExperienceStory(seed_id=seed.id)
    session.add(story)
    session.flush()
    session.refresh(story)
    return story


def load_detailed_stories_for_pool(
    session: Session, pool_id: int
) -> list[tuple[ExperienceSeed, ExperienceStory]]:
    """Return (seed, story) pairs for detail-eligible seeds that have any story content."""
    seeds = list_detail_seeds(session, pool_id)
    pairs: list[tuple[ExperienceSeed, ExperienceStory]] = []
    for seed in seeds:
        story = ensure_story_for_seed(session, seed)
        if story_completion(story) != "empty":
            pairs.append((seed, story))
    return pairs


def format_pool_stories_material(
    session: Session,
    pool_id: int,
    language: str = "zh",
    max_stories: int = 40,
) -> Optional[dict]:
    """Build a synthetic profile material from detailed stories, or None if empty."""
    pairs = load_detailed_stories_for_pool(session, pool_id)[:max_stories]
    if not pairs:
        return None
    blocks = [
        format_story_text(story, seed.content or "", language=language)
        for seed, story in pairs
    ]
    header = "经历信息池细化素材" if language == "zh" else "Experience pool detailed stories"
    content = f"{header}\n\n" + "\n\n---\n\n".join(b for b in blocks if b)
    return {
        "source_type": "experience_pool",
        "filename": "experience_pool_stories.md",
        "extension": ".md",
        "content": content,
    }


def format_pool_stories_summary(
    session: Session,
    pool_id: int,
    language: str = "zh",
    max_stories: int = 40,
    max_chars: int = 4000,
) -> str:
    """Compact summary for letter generation."""
    material = format_pool_stories_material(
        session, pool_id, language=language, max_stories=max_stories
    )
    if not material:
        return ""
    text = material["content"]
    if len(text) > max_chars:
        return text[: max_chars - 1] + "…"
    return text


def count_pool_stats(session: Session, pool: ExperiencePool) -> tuple[int, int]:
    seed_count = (
        session.query(ExperienceSeed)
        .filter(ExperienceSeed.pool_id == pool.id, ExperienceSeed.status == "active")
        .count()
    )
    story_count = 0
    for seed in list_detail_seeds(session, pool.id):
        story = seed.story
        if story is not None and story_completion(story) != "empty":
            story_count += 1
    return seed_count, story_count


def get_cluster_for_pool(
    session: Session, cluster_id: int, pool_id: int
) -> Optional[ExperienceCluster]:
    return (
        session.query(ExperienceCluster)
        .filter(
            ExperienceCluster.id == cluster_id,
            ExperienceCluster.pool_id == pool_id,
        )
        .first()
    )
