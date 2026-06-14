"""
Base Agent interface
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        """Execute the agent's primary task and return a response."""
        ...
