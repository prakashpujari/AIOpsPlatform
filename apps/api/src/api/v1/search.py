"""Search API — delegates to AI Gateway for hybrid BM25+semantic search."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import CurrentUser
from ...domain.chat.models import SearchQuery
from ...infrastructure.database.session import get_db
from ...services.chat_service import ChatService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


@router.post("")
async def search(
    query: SearchQuery,
    _: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ChatService(db)
    result = await svc.search(query)
    return result.model_dump(mode="json")
