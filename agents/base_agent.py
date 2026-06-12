"""Base class for LangGraph agents used in the AI Gateway.

Agents are small async components that perform a specific task (e.g., root‑cause analysis,
incident ticket creation) by optionally calling other services such as the AI Gateway.
Each agent should implement an ``async run`` method that returns a serialisable result.
"""

from __future__ import annotations

import abc
from typing import Any, Dict


class BaseAgent(abc.ABC):
    """Abstract base for all agents.

    Sub‑classes must implement ``async def run(self, *args, **kwargs) -> Dict[str, Any]``.
    The result is expected to be JSON‑serialisable so it can be stored in the database
    or returned to callers.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the agent logic.

        Returns:
            A dictionary representing the agent's outcome.
        """
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Agent {self.__class__.__name__} name={self.name}>"
