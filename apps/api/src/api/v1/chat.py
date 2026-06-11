"""Chat API — sessions, streaming, search."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import CurrentUser
from ...domain.chat.models import SearchQuery, SendMessageCommand
from ...infrastructure.database.session import get_db
from ...services.chat_service import ChatService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post("/sessions", status_code=201)
async def create_session(
    user: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> dict:
    session = await svc.create_session(user.sub)
    return session.model_dump(mode="json")


@router.get("/sessions")
async def list_sessions(
    user: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> list[dict]:
    sessions = await svc.get_sessions(user.sub)
    return [s.model_dump(mode="json") for s in sessions]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> dict:
    session = await svc.get_session(session_id, user.sub)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump(mode="json")


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> None:
    await svc.delete_session(session_id, user.sub)


@router.post("/sessions/{session_id}/stream")
async def stream_message(
    session_id: uuid.UUID,
    command: SendMessageCommand,
    user: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> StreamingResponse:
    async def event_generator():
        try:
            async for chunk in svc.stream_message(session_id, command, user.sub):
                yield chunk
        except Exception as exc:
            logger.error("chat.stream_error", error=str(exc))
            yield f"data: {{'error': '{exc}'}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/search" , tags=["Search"])
async def search_knowledge(
    query: SearchQuery,
    _: CurrentUser,
    svc: ChatService = Depends(_get_service),
) -> dict:
    result = await svc.search(query)
    return result.model_dump(mode="json")
