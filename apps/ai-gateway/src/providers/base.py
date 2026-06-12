"""Abstract base for model provider adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class BaseProvider(ABC):
    """Adapts a model-serving backend to a common interface."""

    @abstractmethod
    async def chat_complete(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict:
        """Non-streaming chat completion — returns an OpenAI-compatible response dict."""

    @abstractmethod
    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Streaming chat completion — yields SSE delta strings."""
