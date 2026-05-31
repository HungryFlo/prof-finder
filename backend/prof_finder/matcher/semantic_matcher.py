"""Semantic matching using Qwen3-Embedding-0.6B sentence-transformer embeddings."""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..runtime import model_dir

# Singleton — loaded once, reused across all match tasks in the process lifetime.
_model = None


_MODELSCOPE_ID = "Qwen/Qwen3-Embedding-0.6B"


def _download_from_modelscope(progress_callbacks=None) -> None:
    """Download model from ModelScope to the configured model directory.

    Args:
        progress_callbacks: Optional list of ProgressCallback classes for download progress.

    Raises RuntimeError if download fails (network error, model not found, etc.).
    """
    local_path = model_dir()
    try:
        from modelscope import snapshot_download

        kwargs = {"local_dir": str(local_path)}
        if progress_callbacks is not None:
            kwargs["progress_callbacks"] = progress_callbacks
        snapshot_download(_MODELSCOPE_ID, **kwargs)
    except Exception as e:
        raise RuntimeError(
            f"无法从 ModelScope 下载模型 {_MODELSCOPE_ID}，请检查网络连接后重试: {e}"
        ) from e


def _detect_device() -> str:
    """Pick the best available compute device."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _get_model(progress_callbacks=None):
    """Lazily load the Qwen3-Embedding-0.6B model, preferring local disk cache.

    Args:
        progress_callbacks: Optional list of ProgressCallback classes passed to download.

    Raises RuntimeError if the model cannot be loaded or downloaded.
    """
    global _model
    if _model is not None:
        return _model

    from sentence_transformers import SentenceTransformer

    local_path = model_dir()
    device = _detect_device()
    if local_path.exists():
        _model = SentenceTransformer(str(local_path), local_files_only=True, device=device)
    else:
        _download_from_modelscope(progress_callbacks=progress_callbacks)
        _model = SentenceTransformer(str(local_path), local_files_only=True, device=device)
    return _model


# ---------------------------------------------------------------------------
# Text builders
# ---------------------------------------------------------------------------

def build_professor_text(professor: dict) -> str:
    """Serialise professor data to a string for encoding.

    Prioritises high-signal fields (research profile, paper summaries) and drops
    redundant ones (raw publication titles are already covered by summaries).
    """
    research_profile = (professor.get("research_profile") or "").strip()
    research_profile_analysis = professor.get("research_profile_analysis") or {}

    if research_profile:
        analysis_parts: list[str] = []
        if isinstance(research_profile_analysis, dict):
            positioning = research_profile_analysis.get("research_positioning")
            if positioning:
                analysis_parts.append(str(positioning))
            themes = research_profile_analysis.get("research_themes") or []
            if isinstance(themes, list):
                for item in themes:
                    if isinstance(item, dict):
                        theme = item.get("theme")
                        if theme:
                            analysis_parts.append(str(theme))
        heading = ". ".join(p for p in
                            ([research_profile[:1500]] + analysis_parts)
                            if p)
    else:
        heading = "; ".join(professor.get("research_interests") or [])

    paper_summaries = professor.get("paper_summaries") or []
    summary_text = ". ".join(
        f"{item.get('title', '')}: {item.get('summary', '')[:200]}".strip()
        for item in paper_summaries[:5]
    )

    parts = [p for p in [heading, summary_text] if p]
    return ". ".join(parts)


def build_profile_text(profile: dict) -> str:
    """Serialise user profile to a focused query string for encoding."""
    academic_profile = (profile.get("academic_profile") or "").strip()
    analysis = profile.get("profile_analysis") or {}
    analysis_parts: list[str] = []
    if isinstance(analysis, dict):
        positioning = analysis.get("academic_positioning")
        if positioning:
            analysis_parts.append(str(positioning))
        for key in ("research_interests", "target_directions", "methods_and_skills"):
            values = analysis.get(key) or []
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        text = item.get("topic") or item.get("direction") or item.get("name")
                        if text:
                            analysis_parts.append(str(text))
                    elif item:
                        analysis_parts.append(str(item))

    skills = "; ".join(profile.get("skills") or [])

    experiences = profile.get("research_experience") or []
    exp_parts = [
        f"{e.get('title', '')} {e.get('description', '')[:200]}".strip()
        for e in experiences
    ]
    exp_text = ". ".join(p for p in exp_parts if p)

    projects = profile.get("projects") or []
    proj_parts = [
        f"{p.get('name', '')} {p.get('description', '')[:200]}".strip()
        for p in projects
    ]
    proj_text = ". ".join(p for p in proj_parts if p)

    generated_text = ". ".join(p for p in [academic_profile, *analysis_parts] if p)
    body_parts = [p for p in [generated_text, exp_text, proj_text] if p]
    body = ". ".join(body_parts)
    return f"{skills}. {body}" if body else skills


# ---------------------------------------------------------------------------
# Batch encoding helpers (used by task_manager)
# ---------------------------------------------------------------------------

_MAX_ENCODE_CHARS = 4000
_ENCODE_BATCH_SIZE = 2


def _truncate_texts(texts: list[str]) -> list[str]:
    """Truncate texts to avoid OOM on MPS/GPU with long sequences."""
    return [t[:_MAX_ENCODE_CHARS] for t in texts]


def encode_texts(texts: list[str]) -> np.ndarray:
    """Encode documents into L2-normalised embedding vectors.

    Returns:
        ndarray of shape (N, 1024), float32, L2-normalised.
    """
    model = _get_model()
    return model.encode(
        _truncate_texts(texts), batch_size=_ENCODE_BATCH_SIZE,
        normalize_embeddings=True, show_progress_bar=False,
    )


def encode_query_texts(texts: list[str]) -> np.ndarray:
    """Encode queries (e.g. user profiles) with the query prompt for asymmetric retrieval.

    Returns:
        ndarray of shape (N, 1024), float32, L2-normalised.
    """
    model = _get_model()
    return model.encode(
        _truncate_texts(texts), prompt_name="query", batch_size=_ENCODE_BATCH_SIZE,
        normalize_embeddings=True, show_progress_bar=False,
    )


def encode_text(text: str) -> list[float]:
    """Encode a single document, returning a plain Python list for JSON storage."""
    return encode_texts([text])[0].tolist()


def encode_query_text(text: str) -> list[float]:
    """Encode a single query with the query prompt, returning a plain Python list."""
    return encode_query_texts([text])[0].tolist()


# ---------------------------------------------------------------------------
# SemanticMatcher
# ---------------------------------------------------------------------------

class SemanticMatcher:
    """Match a user profile against a professor using cosine similarity."""

    def match(
        self,
        profile: dict,
        professor: dict,
        professor_embedding: Optional[list[float]] = None,
        profile_embedding: Optional[list[float]] = None,
        language: str = "zh",
    ) -> tuple[float, list[str]]:
        """Compute semantic match score.

        Args:
            profile: User profile dict (skills, research_experience, projects, …).
            professor: Professor dict (research_interests, publications, affiliation, …).
            professor_embedding: Pre-computed L2-normalised professor vector. If None,
                the professor text is encoded on the fly (slow — prefer caching).
            profile_embedding: Pre-computed L2-normalised profile vector. If None,
                the profile text is encoded on the fly. Pass this when matching one
                profile against many professors to avoid re-encoding each time.
            language: "zh" or "en"; controls wording of match_reasons only.

        Returns:
            (score in [0, 100], human-readable reasons).
        """
        if profile_embedding is not None:
            profile_vec = np.array(profile_embedding, dtype=np.float32)
        else:
            profile_vec = np.array(encode_query_text(build_profile_text(profile)), dtype=np.float32)

        if professor_embedding is not None:
            prof_vec = np.array(professor_embedding, dtype=np.float32)
        else:
            prof_vec = np.array(encode_text(build_professor_text(professor)), dtype=np.float32)

        # Both vectors are L2-normalised, so dot product == cosine similarity.
        similarity = float(np.dot(profile_vec, prof_vec))
        score = (similarity + 1.0) / 2.0 * 100.0
        score = max(0.0, min(100.0, round(score, 2)))

        reasons = self._build_reasons(similarity, professor, language=language)
        return score, reasons

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reasons(
        similarity: float, professor: dict, *, language: str = "zh"
    ) -> list[str]:
        interests = professor.get("research_interests") or []
        lang = language if language in ("zh", "en") else "zh"
        reasons: list[str] = []
        if lang == "en":
            if similarity > 0.6:
                prefix = "Strong semantic match"
            elif similarity > 0.3:
                prefix = "Moderate semantic match"
            else:
                prefix = "Weak semantic match"
            if interests:
                top = ", ".join(interests[:3])
                reasons.append(f"{prefix}: {top}")
            reasons.append(f"Semantic similarity: {similarity:.2f}")
            return reasons

        if similarity > 0.6:
            level = "高度"
        elif similarity > 0.3:
            level = "较好"
        else:
            level = "一般"
        if interests:
            top = ", ".join(interests[:3])
            reasons.append(f"语义{level}匹配: {top}")
        reasons.append(f"语义相似度: {similarity:.2f}")
        return reasons
