"""Ollama provider — native /api/chat endpoint with streaming support."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..core.config import settings
from ..core.exceptions import ModelTimeoutError, RoutingError
from .base import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Calls Ollama's native /api/chat endpoint."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")

    def _build_payload(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        stream: bool,
        kwargs: dict,
    ) -> dict:
        return {
            "model": model_id,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {}),
            },
        }

    async def chat_complete(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict:
        payload = self._build_payload(model_id, messages, temperature, max_tokens, False, kwargs)
        try:
            async with httpx.AsyncClient(timeout=settings.routing_timeout_seconds) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                # Normalise to OpenAI-compatible shape
                return {
                    "id": data.get("model", model_id),
                    "model": model_id,
                    "choices": [{
                        "index": 0,
                        "message": data.get("message", {"role": "assistant", "content": ""}),
                        "finish_reason": "stop",
                    }],
                    "usage": {
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                }
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(f"Ollama timeout for model {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"Ollama returned {exc.response.status_code}") from exc

    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        payload = self._build_payload(model_id, messages, temperature, max_tokens, True, kwargs)
        try:
            async with httpx.AsyncClient(timeout=settings.routing_timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(f"Ollama stream timeout for {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"Ollama stream error {exc.response.status_code}") from exc


# Singleton
ollama_provider = OllamaProvider()
