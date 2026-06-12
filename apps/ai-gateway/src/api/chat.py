"""Chat streaming endpoint — the primary gateway API."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from ..core.config import settings
from ..core.exceptions import GatewayError
from ..cost.cost_engine import cost_engine, estimate_tokens
from ..fallback.fallback_engine import fallback_engine
from ..policy.policy_engine import policy_engine
from ..providers.ollama_provider import ollama_provider
from ..providers.vllm_provider import vllm_provider
from ..registry.schemas import ModelProvider, RoutingDecision
from ..router.routing_engine import RoutingEngine, RoutingStrategy, routing_engine
from .schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_STRATEGY_MAP: dict[str, RoutingStrategy] = {
    "intent": RoutingStrategy.INTENT,
    "cost": RoutingStrategy.COST,
    "latency": RoutingStrategy.LATENCY,
    "quality": RoutingStrategy.QUALITY,
}


def _get_provider(model):  # type: ignore[no-untyped-def]
    if model.provider == ModelProvider.OLLAMA:
        return ollama_provider
    if model.provider == ModelProvider.TGI:
        from ..providers.tgi_provider import tgi_provider
        return tgi_provider
    if model.provider == ModelProvider.GROQ:
        from ..providers.groq_provider import groq_provider
        return groq_provider
    return vllm_provider


async def _sse_generator(
    request: ChatRequest,
    decision: RoutingDecision,
    sanitized_messages: list[dict],
    pii_detected: bool,
    request_id: str,
) -> AsyncIterator[str]:
    provider = _get_provider(decision.selected_model)

    async def stream_fn(model):
        return provider.chat_stream(
            model_id=model.id,
            messages=sanitized_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    stream, model_used = await fallback_engine.stream_with_fallback(decision, stream_fn)

    completion_tokens = 0
    async for chunk in stream:
        completion_tokens += estimate_tokens(chunk)
        payload = json.dumps({"type": "content", "content": chunk})
        yield f"data: {payload}\n\n"

    # ── Record cost after streaming completes ────────────────────────────────
    prompt_tokens = sum(estimate_tokens(m.get("content", "")) for m in sanitized_messages)
    record = cost_engine.record(
        model=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        request_id=request_id,
    )

    metadata_payload = json.dumps({
        "type": "metadata",
        "metadata": {
            "model_used": model_used.id,
            "strategy_used": decision.strategy_used,
            "routing_reason": decision.routing_reason,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": record.cost_usd,
            "pii_detected": pii_detected,
            "request_id": request_id,
        },
    })
    yield f"data: {metadata_payload}\n\n"
    yield "data: {\"type\": \"done\"}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    x_api_key: str = Header(default=""),
) -> StreamingResponse:
    if x_api_key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid API key")

    request_id = request.request_id or str(uuid.uuid4())
    messages_raw = [m.model_dump() for m in request.messages]

    # ── Policy ────────────────────────────────────────────────────────────────
    policy_result = await policy_engine.apply(messages_raw)

    # ── Budget pre-check ─────────────────────────────────────────────────────
    strategy = _STRATEGY_MAP.get(request.strategy, RoutingStrategy.INTENT)
    decision = await routing_engine.route(
        messages=policy_result.sanitized_messages,
        strategy=strategy,
        preferred_model=request.model,
    )
    estimated_cost = cost_engine.estimate_prompt_cost(policy_result.sanitized_messages, decision.selected_model)
    cost_engine.check_budget(estimated_cost)

    # ── Stream ────────────────────────────────────────────────────────────────
    generator = _sse_generator(
        request=request,
        decision=decision,
        sanitized_messages=policy_result.sanitized_messages,
        pii_detected=policy_result.pii_detected,
        request_id=request_id,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
        },
    )


@router.post("/complete", response_model=ChatResponse)
async def chat_complete(
    request: ChatRequest,
    x_api_key: str = Header(default=""),
) -> ChatResponse:
    """Non-streaming completion endpoint for batch/test use."""
    if x_api_key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid API key")

    request_id = request.request_id or str(uuid.uuid4())
    messages_raw = [m.model_dump() for m in request.messages]
    policy_result = await policy_engine.apply(messages_raw)

    strategy = _STRATEGY_MAP.get(request.strategy, RoutingStrategy.INTENT)
    decision = await routing_engine.route(
        messages=policy_result.sanitized_messages,
        strategy=strategy,
        preferred_model=request.model,
    )
    cost_engine.check_budget(
        cost_engine.estimate_prompt_cost(policy_result.sanitized_messages, decision.selected_model)
    )

    provider = _get_provider(decision.selected_model)

    async def call_fn(model):
        return await provider.chat_complete(
            model_id=model.id,
            messages=policy_result.sanitized_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    resp_data, model_used = await fallback_engine.execute_with_fallback(decision, call_fn)
    content = resp_data["choices"][0]["message"]["content"]
    usage = resp_data.get("usage", {})

    record = cost_engine.record(
        model=model_used,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        request_id=request_id,
    )
    return ChatResponse(
        content=content,
        model_used=model_used.id,
        strategy_used=decision.strategy_used,
        routing_reason=decision.routing_reason,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        cost_usd=record.cost_usd,
        pii_detected=policy_result.pii_detected,
        request_id=request_id,
    )
