"""Shared LLM client provider with centralised config and retry logic."""

from __future__ import annotations

import logging
import time
from typing import Optional

from openai import OpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Centralised OpenAI-compatible client provider for AI workflows.

    Handles API key resolution, client lifecycle, and network-level retries
    so individual generators don't duplicate this plumbing.
    """

    DEFAULT_MODEL = "deepseek-v4-flash"
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 1.5  # seconds, multiplied exponentially

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = base_url or settings.deepseek_base_url
        self.model = model or self.DEFAULT_MODEL
        self._client: Optional[OpenAI] = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.api_key not in {"test_key", "your_api_key_here"})

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def chat_completion(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call the chat completions endpoint with retry on transient failures.

        Returns the message content string (never None).
        """
        last_exc: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model or self.model,
                    messages=messages,
                    temperature=temperature,
                    **({"max_tokens": max_tokens} if max_tokens is not None else {}),
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    wait = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "LLM call failed (attempt %s/%s), retrying in %.1fs: %s",
                        attempt + 1,
                        self.MAX_RETRIES,
                        wait,
                        exc,
                    )
                    time.sleep(wait)
        raise last_exc  # type: ignore[misc]
