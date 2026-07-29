"""Shared LLM client provider with OpenAI-compatible and Anthropic API support."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable, Generator, Optional

from openai import OpenAI

from ..llm.config import LLMConfig, LLMProviderType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LLMCancelled(Exception):
    """Raised when a ``cancel_checker`` reports cancellation mid-call.

    Deliberately independent of the API layer's ``TaskCancelled`` (this
    module must not depend on ``api.task_manager``); executors catch this
    and translate it into their own cancellation status.
    """


class LLMProvider:
    """Centralised LLM client for AI workflows.

    Supports OpenAI-compatible chat completions and Anthropic Messages API.
    """

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 1.5  # seconds, multiplied exponentially

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        *,
        provider: Optional[LLMProviderType] = None,
        config: Optional[LLMConfig] = None,
    ):
        if config is not None:
            self._config = config
        else:
            from ..config import settings
            from ..llm.config import resolve_llm_config

            resolved = resolve_llm_config(app_settings=settings)
            self._config = LLMConfig(
                provider=provider or resolved.provider,
                api_key=api_key or resolved.api_key,
                base_url=base_url or resolved.base_url,
                model=model or resolved.model,
            )

        self._openai_client: Optional[OpenAI] = None
        self._anthropic_client = None

    @property
    def config(self) -> LLMConfig:
        return self._config

    @property
    def api_key(self) -> str:
        return self._config.api_key

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def provider_type(self) -> LLMProviderType:
        return self._config.provider

    @property
    def enabled(self) -> bool:
        return self._config.is_configured() and bool(self.model)

    @property
    def client(self) -> OpenAI:
        if self._config.provider != "openai":
            raise RuntimeError("OpenAI client requested but provider is anthropic")
        if self._openai_client is None:
            self._openai_client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )
        return self._openai_client

    def _anthropic_client_instance(self):
        if self._anthropic_client is None:
            from anthropic import Anthropic

            self._anthropic_client = Anthropic(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )
        return self._anthropic_client

    @staticmethod
    def _split_messages(messages: list[dict]) -> tuple[Optional[str], list[dict]]:
        system_parts: list[str] = []
        conversation: list[dict] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "system":
                if content:
                    system_parts.append(str(content))
            else:
                conversation.append({"role": role, "content": content})
        system = "\n\n".join(system_parts) if system_parts else None
        return system, conversation

    def chat_completion(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Call the configured provider with retry on transient failures.

        Args:
            cancel_checker: If given, the call is executed as a stream
                internally (regardless of the caller's needs) so that
                cancellation can take effect mid-generation instead of only
                before/after the whole (potentially slow) completion.
                Raises ``LLMCancelled`` as soon as ``cancel_checker()``
                returns True, aborting the underlying HTTP stream rather
                than waiting for it to finish.
        """
        if cancel_checker is not None:
            chunks: list[str] = []
            for chunk in self.chat_completion_stream(
                messages,
                temperature=temperature,
                model=model,
                max_tokens=max_tokens,
                cancel_checker=cancel_checker,
            ):
                chunks.append(chunk)
            return "".join(chunks).strip()

        last_exc: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return self._chat_once(
                    messages,
                    temperature=temperature,
                    model=model,
                    max_tokens=max_tokens,
                )
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

    def _chat_once(
        self,
        messages: list[dict],
        *,
        temperature: float,
        model: Optional[str],
        max_tokens: Optional[int],
    ) -> str:
        use_model = model or self._config.model
        if not use_model:
            raise ValueError("未配置 LLM 模型名称，请在设置中填写模型")

        if self._config.provider == "anthropic":
            return self._anthropic_chat(
                messages,
                model=use_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        response = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            **({"max_tokens": max_tokens} if max_tokens is not None else {}),
        )
        return (response.choices[0].message.content or "").strip()

    def _anthropic_chat(
        self,
        messages: list[dict],
        *,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
        system, conversation = self._split_messages(messages)
        client = self._anthropic_client_instance()
        kwargs: dict = {
            "model": model,
            "messages": conversation,
            "max_tokens": max_tokens if max_tokens is not None else 8192,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts).strip()

    def chat_completion_stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> Generator[str, None, None]:
        """Streaming variant; no retry (would duplicate tokens).

        Args:
            cancel_checker: If given, checked between chunks; raises
                ``LLMCancelled`` and actively closes the underlying HTTP
                stream as soon as it returns True, instead of reading the
                response to completion.
        """
        use_model = model or self._config.model
        if not use_model:
            raise ValueError("未配置 LLM 模型名称，请在设置中填写模型")

        if self._config.provider == "anthropic":
            yield from self._anthropic_chat_stream(
                messages,
                model=use_model,
                temperature=temperature,
                max_tokens=max_tokens,
                cancel_checker=cancel_checker,
            )
            return

        response = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **({"max_tokens": max_tokens} if max_tokens is not None else {}),
        )
        try:
            for chunk in response:
                if cancel_checker is not None and cancel_checker():
                    raise LLMCancelled()
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except LLMCancelled:
            self._close_stream(response)
            raise

    @staticmethod
    def _close_stream(response) -> None:
        """Best-effort close of an OpenAI SDK streaming response's HTTP connection."""
        try:
            response.close()
        except Exception:
            pass

    def _anthropic_chat_stream(
        self,
        messages: list[dict],
        *,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> Generator[str, None, None]:
        system, conversation = self._split_messages(messages)
        client = self._anthropic_client_instance()
        kwargs: dict = {
            "model": model,
            "messages": conversation,
            "max_tokens": max_tokens if max_tokens is not None else 8192,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                if cancel_checker is not None and cancel_checker():
                    # Exiting the `with` block (via the raise below) closes
                    # the underlying connection for us.
                    raise LLMCancelled()
                if text:
                    yield text
