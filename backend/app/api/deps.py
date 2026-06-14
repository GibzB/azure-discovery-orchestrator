"""
FastAPI dependency providers

Provides singleton instances of services that are initialised once
at app startup and shared across all requests.
"""

from app.services.conversation_service import ConversationService

# Populated by app lifespan in main.py
_conversation_service: ConversationService | None = None


def set_conversation_service(svc: ConversationService) -> None:
    global _conversation_service
    _conversation_service = svc


def get_conversation_service() -> ConversationService:
    if _conversation_service is None:
        raise RuntimeError("ConversationService not initialised — app startup incomplete.")
    return _conversation_service
