"""Ticket Creation Agent – placeholder implementation.

In a full system this agent would call an external incident management service
(e.g., PagerDuty) to create a ticket. For now it simply returns a mock payload
so that the dispatcher and tests can exercise the full flow without external
dependencies.
"""

from __future__ import annotations

from typing import Any, Dict

from ..base_agent import BaseAgent


class TicketCreationAgent(BaseAgent):
    """Agent that pretends to create an incident ticket.

    Args:
        service_name: Name of the service/component the ticket is for.
    """

    def __init__(self, service_name: str = "default-service") -> None:
        super().__init__(name="ticket_creation")
        self.service_name = service_name

    async def run(self, description: str) -> Dict[str, Any]:
        """Return a mock ticket payload.

        In production this would POST to PagerDuty (or similar) and return the
        created ticket ID and URL. Here we generate a deterministic fake ID.
        """
        # Deterministic fake ticket ID based on description hash
        ticket_id = f"TCKT-{abs(hash(description)) % 100000}"
        return {
            "service": self.service_name,
            "description": description,
            "ticket_id": ticket_id,
            "status": "created",
        }
