"""Structured API errors with stable machine-readable codes."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Mapping, NoReturn, Optional


class ErrorCode(StrEnum):
    """Stable error codes returned in API error payloads."""

    # Generic
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    NOT_FOUND = "NOT_FOUND"

    # Auth / users
    AUTH_REQUIRED = "AUTH_REQUIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_MALFORMED = "TOKEN_MALFORMED"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    USERNAME_RESERVED = "USERNAME_RESERVED"
    USERNAME_EXISTS = "USERNAME_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    REFRESH_TOKEN_INVALID = "REFRESH_TOKEN_INVALID"
    CURRENT_PASSWORD_WRONG = "CURRENT_PASSWORD_WRONG"

    # Setup
    SETUP_REQUIRED = "SETUP_REQUIRED"
    SETUP_PACKAGED_ONLY = "SETUP_PACKAGED_ONLY"
    SETUP_ALREADY_COMPLETED = "SETUP_ALREADY_COMPLETED"
    FOLDER_PICKER_UNAVAILABLE = "FOLDER_PICKER_UNAVAILABLE"
    NO_DIRECTORY_SELECTED = "NO_DIRECTORY_SELECTED"
    SETUP_FAILED = "SETUP_FAILED"

    # LLM / profiles
    LLM_NOT_CONFIGURED = "LLM_NOT_CONFIGURED"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    EXPERIENCE_POOL_NOT_FOUND = "EXPERIENCE_POOL_NOT_FOUND"
    EXPERIENCE_SEED_NOT_FOUND = "EXPERIENCE_SEED_NOT_FOUND"
    EXPERIENCE_CLUSTER_NOT_FOUND = "EXPERIENCE_CLUSTER_NOT_FOUND"
    EXPERIENCE_STORY_NOT_FOUND = "EXPERIENCE_STORY_NOT_FOUND"
    POOL_COMPOSITION_NOT_FOUND = "POOL_COMPOSITION_NOT_FOUND"
    PROFILE_MATERIAL_REQUIRED = "PROFILE_MATERIAL_REQUIRED"
    PROFILE_FILE_TYPE_UNSUPPORTED = "PROFILE_FILE_TYPE_UNSUPPORTED"
    PROFILE_FILE_ENCODING_ERROR = "PROFILE_FILE_ENCODING_ERROR"
    PROFILE_FILE_EMPTY = "PROFILE_FILE_EMPTY"
    PROFILE_MATERIAL_TOO_LONG = "PROFILE_MATERIAL_TOO_LONG"
    PROFILE_CHAT_REQUIRED = "PROFILE_CHAT_REQUIRED"
    PROFILE_OPERATION_FAILED = "PROFILE_OPERATION_FAILED"
    RESUME_REQUIRED = "RESUME_REQUIRED"
    PROFILE_REQUIRED = "PROFILE_REQUIRED"

    # Professors / crawl
    PROFESSOR_NOT_FOUND = "PROFESSOR_NOT_FOUND"
    PROFESSORS_REQUIRED = "PROFESSORS_REQUIRED"
    INVALID_PROFESSOR_IDS = "INVALID_PROFESSOR_IDS"
    INVALID_SOURCE_INPUT_IDS = "INVALID_SOURCE_INPUT_IDS"
    SOURCE_INPUT_REQUIRED = "SOURCE_INPUT_REQUIRED"
    SOURCE_INPUT_NOT_FOUND = "SOURCE_INPUT_NOT_FOUND"
    SOURCES_ALREADY_SUMMARIZED = "SOURCES_ALREADY_SUMMARIZED"
    HOMEPAGE_URL_REQUIRED = "HOMEPAGE_URL_REQUIRED"
    NO_PAPERS_TO_FETCH = "NO_PAPERS_TO_FETCH"
    CRAWLER_CONFIG_NOT_FOUND = "CRAWLER_CONFIG_NOT_FOUND"
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
    UNIVERSITY_UNSUPPORTED = "UNIVERSITY_UNSUPPORTED"
    SCHOLAR_ID_MISSING = "SCHOLAR_ID_MISSING"
    SCHOLAR_ID_EXTRACT_FAILED = "SCHOLAR_ID_EXTRACT_FAILED"
    SCHOLAR_NOT_FOUND = "SCHOLAR_NOT_FOUND"
    DBLP_ALREADY_LINKED = "DBLP_ALREADY_LINKED"
    DBLP_PID_MISSING = "DBLP_PID_MISSING"
    DBLP_PID_EXTRACT_FAILED = "DBLP_PID_EXTRACT_FAILED"
    DBLP_SCHOLAR_NOT_FOUND = "DBLP_SCHOLAR_NOT_FOUND"
    UNIVERSITY_AFFILIATION_REQUIRED = "UNIVERSITY_AFFILIATION_REQUIRED"
    CRAWL_FAILED = "CRAWL_FAILED"
    DBLP_SEARCH_FAILED = "DBLP_SEARCH_FAILED"
    DBLP_REFRESH_FAILED = "DBLP_REFRESH_FAILED"
    SCHOLAR_URL_REQUIRED = "SCHOLAR_URL_REQUIRED"
    DBLP_URL_REQUIRED = "DBLP_URL_REQUIRED"
    BAD_REQUEST = "BAD_REQUEST"
    ARXIV_FETCH_FAILED = "ARXIV_FETCH_FAILED"

    # Match / letters
    MODEL_NOT_DOWNLOADED = "MODEL_NOT_DOWNLOADED"
    MODEL_ALREADY_EXISTS = "MODEL_ALREADY_EXISTS"
    MATCH_NOT_FOUND = "MATCH_NOT_FOUND"
    LETTER_TARGETS_REQUIRED = "LETTER_TARGETS_REQUIRED"
    LETTER_PROFESSORS_NOT_FOUND = "LETTER_PROFESSORS_NOT_FOUND"

    # Universities
    UNIVERSITY_EXISTS = "UNIVERSITY_EXISTS"
    UNIVERSITY_NOT_FOUND = "UNIVERSITY_NOT_FOUND"
    UNIVERSITY_IN_USE = "UNIVERSITY_IN_USE"

    # Tasks
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ACCESS_DENIED = "TASK_ACCESS_DENIED"
    TASK_CANCEL_DENIED = "TASK_CANCEL_DENIED"
    TASK_RETRY_DENIED = "TASK_RETRY_DENIED"
    TASK_ALREADY_FINISHED = "TASK_ALREADY_FINISHED"
    TASK_RESUME_INVALID_STATUS = "TASK_RESUME_INVALID_STATUS"
    TASK_MISSING_REPLAY_ARGS = "TASK_MISSING_REPLAY_ARGS"
    TASK_RETRY_INVALID_STATUS = "TASK_RETRY_INVALID_STATUS"


class ApiError(Exception):
    """Application error that serializes to ``{code, detail}``."""

    def __init__(
        self,
        status_code: int,
        code: str | ErrorCode,
        detail: Optional[str] = None,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.code = str(code)
        self.detail = detail if detail is not None else self.code
        self.headers = dict(headers) if headers else None
        super().__init__(self.detail)


def raise_api_error(
    status_code: int,
    code: str | ErrorCode,
    detail: Optional[str] = None,
    *,
    headers: Optional[Mapping[str, str]] = None,
) -> NoReturn:
    """Raise an :class:`ApiError`. Never returns."""
    raise ApiError(status_code, code, detail, headers=headers)


def error_body(code: str | ErrorCode, detail: str) -> dict[str, str]:
    return {"code": str(code), "detail": detail}


def format_validation_errors(errors: list[Any]) -> str:
    """Format FastAPI/Pydantic validation errors into a readable string."""
    parts: list[str] = []
    for err in errors:
        loc = err.get("loc") or ()
        loc_str = ".".join(str(x) for x in loc if x != "body")
        msg = err.get("msg") or "invalid"
        if loc_str:
            parts.append(f"{loc_str}: {msg}")
        else:
            parts.append(str(msg))
    return "; ".join(parts) if parts else "Validation failed"
