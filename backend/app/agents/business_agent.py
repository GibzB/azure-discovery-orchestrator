"""
Business Agent - Gathers business requirements and constraints
"""
from typing import Any

from app.agents.base import BaseAgent


class BusinessAgent(BaseAgent):
    """
    Elicits business requirements: budget, compliance, scale,
    regional presence, SLA targets, and growth plans.
    """

    name = "business"

    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError
