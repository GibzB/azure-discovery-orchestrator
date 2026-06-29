"""
Reports route — generate and retrieve discovery reports.

POST /{session_id}/generate
    Fetches the session's conversation history from Cosmos DB,
    runs ReportAgent to generate a Markdown report, stores it in
    Blob Storage, and returns the Markdown text.

GET  /{session_id}/download
    Returns the pre-generated Markdown report from Blob Storage,
    or triggers generation on-demand if not yet produced.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.agents.report_agent import ReportAgent
from app.core.config import settings
from app.services.cosmos_service import CosmosService

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton — one instance per worker process
_report_agent = ReportAgent()


def _get_cosmos() -> CosmosService:
    return CosmosService()


def _format_history(session: dict) -> str:
    """Convert stored history list into a readable transcript string."""
    history: list[dict] = session.get("history", [])
    if not history:
        return session.get("transcript", "No transcript available.")
    lines = []
    for msg in history:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n\n".join(lines)


@router.post(
    "/{session_id}/generate",
    response_class=PlainTextResponse,
    summary="Generate a discovery report from the completed session",
)
async def generate_report(session_id: str) -> str:
    """
    Generates and persists a Markdown discovery report for the given session.
    Returns the report as plain text (Markdown).
    """
    cosmos = _get_cosmos()
    session = await cosmos.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Complete a discovery session first.",
        )

    transcript = _format_history(session)
    report_md = await _report_agent.run(
        user_input=transcript,
        context={"session_id": session_id},
    )

    if not report_md:
        raise HTTPException(status_code=500, detail="Report generation returned empty content.")

    # Store report reference back on the session document
    session["report_generated"] = True
    try:
        await cosmos.upsert_session(session)
    except Exception as exc:
        logger.warning("Could not update session with report flag: %s", exc)

    return report_md


@router.get(
    "/{session_id}/download",
    response_class=PlainTextResponse,
    summary="Download the generated Markdown report",
    responses={
        200: {"content": {"text/markdown": {}}},
    },
)
async def download_report(session_id: str) -> PlainTextResponse:
    """
    Returns the report from Blob Storage if available, or generates it on demand.
    Content-Disposition header is set so browsers prompt a file save.
    """
    blob_name = f"{session_id}/report.md"

    # Try to fetch from blob first
    if settings.STORAGE_CONNECTION_STRING:
        try:
            from azure.storage.blob.aio import BlobServiceClient

            async with BlobServiceClient.from_connection_string(
                settings.STORAGE_CONNECTION_STRING
            ) as blob_svc:
                container = blob_svc.get_container_client(settings.STORAGE_REPORTS_CONTAINER)
                downloader = await container.download_blob(blob_name)
                content = await downloader.readall()
                report_md = content.decode("utf-8")

            return PlainTextResponse(
                content=report_md,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f'attachment; filename="discovery-report-{session_id[:8]}.md"'
                },
            )
        except Exception as exc:
            # Blob not found — fall through to on-demand generation
            logger.info("Blob not found for session %s, generating on demand: %s", session_id, exc)

    # Generate on demand
    cosmos = _get_cosmos()
    session = await cosmos.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    transcript = _format_history(session)
    report_md = await _report_agent.run(
        user_input=transcript,
        context={"session_id": session_id},
    )

    if not report_md:
        raise HTTPException(status_code=500, detail="Report generation failed.")

    return PlainTextResponse(
        content=report_md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="discovery-report-{session_id[:8]}.md"'
        },
    )
