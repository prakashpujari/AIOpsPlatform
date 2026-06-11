"""Chat domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class KnowledgeSource(BaseModel):
    id: str
    title: str
    content: str
    score: float
    document_id: str
    chunk_index: int
    metadata: dict[str, str] = {}


class ChatMessageMetadata(BaseModel):
    model: str | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None
    confidence: float | None = None


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    agent_trace_id: str | None = None
    sources: list[KnowledgeSource] = []
    metadata: ChatMessageMetadata | None = None


class ChatSession(BaseModel):
    id: uuid.UUID
    user_id: str
    title: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SendMessageCommand(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


class SearchQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    sources: list[KnowledgeSource]
    answer: str
    query_time: float
    rerank_score: float | None = None
