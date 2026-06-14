"""
Architect Agent - Produces Azure architecture recommendations
"""
from typing import Any

from app.agents.base import BaseAgent


class ArchitectAgent(BaseAgent):
    """
    Maps business requirements to Azure services and landing zone patterns,
    drawing on CAF/WAF knowledge from the RAG knowledge base.
    """

    name = "architect"

    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError
