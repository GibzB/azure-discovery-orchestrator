"""
Sessions route - CRUD for discovery sessions
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{session_id}")
async def get_session(session_id: str):
    # TODO: fetch from CosmosService
    return {"session_id": session_id}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    # TODO: delete from CosmosService
    return {"deleted": session_id}
