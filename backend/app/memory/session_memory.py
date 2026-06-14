"""
Session Memory - maintains conversation state across agent turns
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class SessionMemory:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_openai_format(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def clear(self) -> None:
        self.messages.clear()
