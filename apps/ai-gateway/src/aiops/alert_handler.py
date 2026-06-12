"""AIOps alert handling – receives alerts and runs agents.

This module provides a FastAPI router that accepts Alertmanager webhook payloads,
stores them (in‑memory for now), and triggers the configured LangGraph agents.
The result of each agent is returned to the caller. In a production system the
alerts would be persisted to a database and additional pipelines would be added.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..core.config import settings
from ..agents.risk_assessment_agent.src.agent import RiskAssessmentAgent
from ..agents.ticket_creation_agent.src.agent import TicketCreationAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aiops", tags=["aiops"])

# Simple in‑memory store for received alerts – replace with DB later
_alert_store: List[Dict[str, Any]] = []

@router.post("/alert")
async def receive_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Endpoint for Alertmanager webhook payloads.

    The payload is stored and then processed by the configured agents. The response
    contains the original alert information plus any agent‑generated data.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Empty alert payload")

    alert = {
        "received_at": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }
    _alert_store.append(alert)
    logger.info("Received alert: %s", payload.get("labels", {}))

    # Prepare agents – for now we run risk assessment and ticket creation
    description = payload.get("annotations", {}).get("description", "Alert received")
    risk_agent = RiskAssessmentAgent(gateway_url=f"http://{settings.env}-gateway:8001" if settings.env != "development" else "http://localhost:8001")
    ticket_agent = TicketCreationAgent(service_name=payload.get("labels", {}).get("service", "unknown"))

    # Run agents concurrently
    risk_result, ticket_result = await risk_agent.run(description), await ticket_agent.run(description)

    result = {
        "alert": alert,
        "risk_assessment": risk_result,
        "ticket": ticket_result,
    }
    return result
