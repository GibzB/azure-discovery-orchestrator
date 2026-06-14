"""
Report Agent - Generates structured discovery reports
"""
from typing import Any

from app.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    """
    Consolidates outputs from all specialist agents into a
    structured PDF/Markdown discovery report.
    """

    name = "report"

    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError
