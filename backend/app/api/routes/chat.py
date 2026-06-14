"""
Chat route - handles conversational turns
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # TODO: route through OrchestratorAgent
    return ChatResponse(session_id=request.session_id, response="Not implemented yet")
