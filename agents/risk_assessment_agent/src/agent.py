"""Risk Assessment Agent – example LangGraph agent.

This agent receives a textual incident description, calls the AI Gateway's `/chat/complete`
endpoint to obtain a root‑cause analysis, and returns a structured result.

In production the agent would store the result in the database, but for now we keep the
implementation lightweight and side‑effect‑free for unit testing.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from ..base_agent import BaseAgent


class RiskAssessmentAgent(BaseAgent):
    """Agent that asks the AI gateway to analyse an incident description.

    Args:
        gateway_url: Base URL of the AI Gateway (e.g. ``http://localhost:8001``).
    """

    def __init__(self, gateway_url: str = "http://localhost:8001") -> None:
        super().__init__(name="risk_assessment")
        self.gateway_url = gateway_url.rstrip("/")

    async def run(self, description: str) -> Dict[str, Any]:
        """Perform risk assessment.

        Sends a minimal ``ChatRequest`` to the gateway and extracts the content.
        Returns a dictionary with the original description and the AI answer.
        """
        payload = {
            "messages": [{"role": "user", "content": f"Analyse the following incident and give a concise root‑cause assessment:\n\n{description}"}],
            "model": None,
            "strategy": "intent",
            "temperature": 0.0,
            "max_tokens": 512,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.gateway_url}/v1/chat/complete", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return {
            "description": description,
            "assessment": data.get("content", ""),
            "model_used": data.get("model_used"),
            "strategy_used": data.get("strategy_used"),
        }
