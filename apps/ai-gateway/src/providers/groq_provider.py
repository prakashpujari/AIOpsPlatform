'''Groq provider — OpenAI‑compatible endpoint at https://api.groq.com/openai/v1.'''

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


class GroqProvider(BaseProvider):
    """Calls Groq's OpenAI‑compatible API.

    The base URL is fixed to ``https://api.groq.com/openai/v1``. The API key
    is taken from ``settings.groq_api_key`` and sent as a ``Bearer`` token.
    """

    def __init__(self, base_url: str | None = None) -> None:
        # Allow an explicit base URL for testing, otherwise use Groq's public endpoint.
        self._base_url = (base_url or "https://api.groq.com/openai/v1").rstrip("/")
        self._auth_header = {
            "Authorization": f"Bearer {settings.groq_api_key.get_secret_value()}"
        }

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
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json", **self._auth_header},
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(f"Groq timeout for model {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"Groq returned {exc.response.status_code}: {exc.response.text}") from exc

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
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json", **self._auth_header},
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
            raise ModelTimeoutError(f"Groq stream timeout for model {model_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise RoutingError(f"Groq stream error {exc.response.status_code}: {exc.response.text}") from exc


# Singleton instance used by the gateway
groq_provider = GroqProvider()
