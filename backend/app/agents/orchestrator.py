"""
Orchestrator Agent - Routes discovery requests to specialist agents
"""
from typing import Any

from app.agents.base import BaseAgent


class OrchestratorAgent(BaseAgent):
    """
    Top-level agent that interprets user intent and delegates
    to business, architect, security, or report agents.
    """

    name = "orchestrator"

    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError
