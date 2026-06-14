"""
Security Agent - Reviews recommendations against security baselines
"""
from typing import Any

from app.agents.base import BaseAgent


class SecurityAgent(BaseAgent):
    """
    Evaluates architecture designs for compliance, identity,
    network security, and data protection requirements.
    """

    name = "security"

    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError
