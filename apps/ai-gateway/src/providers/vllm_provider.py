"""vLLM provider — OpenAI-compatible /v1/chat/completions endpoint."""

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


class VLLMProvider(BaseProvider):
    """Calls vLLM's OpenAI-compatible API."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.vllm_base_url).rstrip("/")

    async def chat_complete(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict:
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.routing_timeout_seconds) as client:
                resp = await client.post(
                    f"{self._base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(f"vLLM timeout for model {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"vLLM returned {exc.response.status_code}: {exc.response.text}") from exc

    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.routing_timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(f"vLLM stream timeout for model {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"vLLM stream error {exc.response.status_code}") from exc


# Singleton
vllm_provider = VLLMProvider()
