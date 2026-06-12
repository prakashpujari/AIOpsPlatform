"""PagerDuty client – thin wrapper around the PagerDuty REST API.

Only the ``create_incident`` method is required for Phase 9. The client uses the
``pagerduty_api_token`` and ``pagerduty_service_id`` settings. In a production
environment the token must be a secret (e.g., stored in Vault), but for local
development a dummy value is acceptable.
"""

from __future__ import annotations

import httpx
import logging
from typing import Any, Dict

from ..core.config import settings

logger = logging.getLogger(__name__)


class PagerDutyClient:
    """Minimal PagerDuty client for incident creation.

    The client expects ``settings.pagerduty_api_token`` to be a valid API token
    and ``settings.pagerduty_service_id`` to reference an existing service.
    """

    def __init__(self) -> None:
        self.base_url = "https://api.pagerduty.com"
        self.headers = {
            "Authorization": f"Token token={settings.pagerduty_api_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
        }
        self.service_id = settings.pagerduty_service_id

    async def create_incident(self, title: str, details: str | None = None) -> Dict[str, Any]:
        """Create a PagerDuty incident.

        Args:
            title: Short incident title.
            details: Optional longer description.

        Returns:
            The parsed JSON response from PagerDuty.
        """
        payload: Dict[str, Any] = {
            "incident": {
                "type": "incident",
                "title": title,
                "service": {"id": self.service_id, "type": "service_reference"},
                "body": {"type": "incident_body", "details": details or ""},
            }
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self.base_url}/incidents", json=payload, headers=self.headers)
            resp.raise_for_status()
            logger.info("Created PagerDuty incident: %s", resp.json().get("incident", {}).get("id"))
            return resp.json()


# Singleton instance used by the gateway
pagerduty_client = PagerDutyClient()
