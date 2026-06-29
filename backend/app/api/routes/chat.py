"""
Chat route — handles text-based conversational turns via the OrchestratorAgent.

This is the text-mode complement to the voice/WebSocket pipeline.
It persists each turn to Cosmos DB so the conversation history survives
across requests and can later be used by the ReportAgent.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_conversation_service
from app.services.conversation_service import ConversationService
from app.services.cosmos_service import CosmosService

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    turn: int
    is_final: bool


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ChatResponse:
    """
    Process a single text turn in the discovery conversation.

    - Creates a new session if session_id is not yet known.
    - Runs the OrchestratorAgent with the full conversation history.
    - Persists the updated history to Cosmos DB.
    - Returns the assistant's reply and session metadata.
    """
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    session = svc.get_or_create_session(request.session_id)

    # Run through the OrchestratorAgent (re-using the same agent the voice pipeline uses)
    response_text = await svc._agent.run(
        user_input=request.message,
        history=session.history,
    )

    session.turn += 1

    # Determine if session is complete
    is_final = (
        session.turn >= session.max_turns
        or "thank you for your time" in response_text.lower()
        or "discovery report" in response_text.lower()
    )
    if is_final:
        from app.services.conversation_service import SessionStatus
        session.status = SessionStatus.COMPLETED

    # Persist history to Cosmos DB (non-fatal if it fails)
    try:
        cosmos = CosmosService()
        await cosmos.upsert_session(
            {
                "id": request.session_id,
                "sessionId": request.session_id,
                "history": session.history,
                "turn": session.turn,
                "status": session.status.value,
            }
        )
    except Exception as exc:
        logger.warning("Failed to persist chat session to Cosmos: %s", exc)

    return ChatResponse(
        session_id=request.session_id,
        response=response_text,
        turn=session.turn,
        is_final=is_final,
    )
