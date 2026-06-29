"""
Sessions route — CRUD for discovery sessions backed by Cosmos DB.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException

from app.services.cosmos_service import CosmosService

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_cosmos() -> CosmosService:
    return CosmosService()


@router.get("/{session_id}", summary="Get a session by ID")
async def get_session(session_id: str) -> dict:
    """Return the session document from Cosmos DB."""
    cosmos = _get_cosmos()
    session = await cosmos.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    # Strip Cosmos internal fields before returning
    for key in ("_rid", "_self", "_etag", "_attachments", "_ts"):
        session.pop(key, None)
    return session


@router.delete("/{session_id}", summary="Delete a session")
async def delete_session(session_id: str) -> dict:
    """Delete a session document from Cosmos DB."""
    cosmos = _get_cosmos()
    try:
        db = cosmos.client.get_database_client(cosmos.database_name)
        container = db.get_container_client(cosmos.container_name)
        await container.delete_item(item=session_id, partition_key=session_id)
        logger.info("Deleted session: %s", session_id)
        return {"deleted": session_id}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or already deleted: {exc}")


@router.get("/", summary="List recent sessions (up to 50)")
async def list_sessions() -> list[dict]:
    """List the 50 most recent sessions ordered by most recently updated."""
    cosmos = _get_cosmos()
    try:
        db = cosmos.client.get_database_client(cosmos.database_name)
        container = db.get_container_client(cosmos.container_name)
        query = "SELECT c.id, c.sessionId, c.status, c.turn, c._ts FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 50"
        items = []
        async with container.query_items(query=query, enable_cross_partition_query=True) as results:
            async for item in results:
                items.append(item)
        return items
    except Exception as exc:
        logger.error("Failed to list sessions: %s", exc)
        return []
