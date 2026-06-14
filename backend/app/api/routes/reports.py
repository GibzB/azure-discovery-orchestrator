"""
Reports route - generate and retrieve discovery reports
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.post("/{session_id}/generate")
async def generate_report(session_id: str):
    # TODO: invoke ReportAgent
    return {"status": "queued", "session_id": session_id}


@router.get("/{session_id}/download")
async def download_report(session_id: str):
    # TODO: return generated PDF from blob storage
    return {"session_id": session_id, "url": ""}
