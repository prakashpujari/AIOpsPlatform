"""Chat application service — session management + AI Gateway delegation."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..core.exceptions import AIGatewayError
from ..domain.chat.models import (
    ChatMessage,
    ChatMessageMetadata,
    ChatSession,
    KnowledgeSource,
    SearchQuery,
    SearchResult,
    SendMessageCommand,
)
from ..infrastructure.database.models import ChatSessionORM
from sqlalchemy import select

logger = structlog.get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create_session(self, user_id: str) -> ChatSession:
        orm = ChatSessionORM(user_id=user_id, title="New Chat", messages=[])
        self._db.add(orm)
        await self._db.flush()
        return self._orm_to_domain(orm)

    async def get_sessions(self, user_id: str) -> list[ChatSession]:
        result = await self._db.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.user_id == user_id)
            .order_by(ChatSessionORM.updated_at.desc())
            .limit(50)
        )
        return [self._orm_to_domain(r) for r in result.scalars().all()]

    async def get_session(self, session_id: uuid.UUID, user_id: str) -> ChatSession | None:
        orm = await self._db.get(ChatSessionORM, session_id)
        if not orm or orm.user_id != user_id:
            return None
        return self._orm_to_domain(orm)

    async def delete_session(self, session_id: uuid.UUID, user_id: str) -> None:
        orm = await self._db.get(ChatSessionORM, session_id)
        if orm and orm.user_id == user_id:
            await self._db.delete(orm)

    async def stream_message(
        self,
        session_id: uuid.UUID,
        command: SendMessageCommand,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        orm = await self._db.get(ChatSessionORM, session_id)
        if not orm or orm.user_id != user_id:
            raise ValueError("Session not found")

        user_msg = ChatMessage(
            role="user",
            content=command.message,
            timestamp=datetime.now(timezone.utc),
        )
        messages = list(orm.messages or [])
        messages.append(user_msg.model_dump(mode="json"))
        orm.messages = messages

        async for chunk in self._call_ai_gateway_stream(command.message, messages):
            yield chunk

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def _call_ai_gateway_stream(
        self, message: str, history: list[dict]
    ) -> AsyncGenerator[str, None]:
        url = f"{settings.ai_gateway_url}/v1/chat/stream"
        headers = {
            "Authorization": f"Bearer {settings.ai_gateway_api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "X-API-Key": settings.ai_gateway_api_key.get_secret_value(),
        }
        payload = {
            "messages": history + [{"role": "user", "content": message}],
            "strategy": "intent",
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=settings.ai_gateway_timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    raise AIGatewayError(f"Gateway returned {response.status_code}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n"

    async def search(self, query: SearchQuery) -> SearchResult:
        start = time.monotonic()
        url = f"{settings.ai_gateway_url}/v1/search"
        headers = {
            "Authorization": f"Bearer {settings.ai_gateway_api_key.get_secret_value()}",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=query.model_dump(), headers=headers)
            resp.raise_for_status()
            data = resp.json()

        elapsed = (time.monotonic() - start) * 1000
        return SearchResult(
            sources=[KnowledgeSource(**s) for s in data.get("sources", [])],
            answer=data.get("answer", ""),
            query_time=elapsed,
        )

    @staticmethod
    def _orm_to_domain(orm: ChatSessionORM) -> ChatSession:
        messages = [ChatMessage.model_validate(m) for m in (orm.messages or [])]
        return ChatSession(
            id=orm.id,
            user_id=orm.user_id,
            title=orm.title,
            messages=messages,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
