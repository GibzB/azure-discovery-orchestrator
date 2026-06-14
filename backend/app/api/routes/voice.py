"""
Voice routes

REST:
  POST /api/v1/voice/start/{session_id}
      → Returns MP3 of opening greeting (no audio input needed)

  POST /api/v1/voice/turn/{session_id}
      → Accepts audio upload, returns MP3 of next response

  GET  /api/v1/voice/status/{session_id}
      → Returns session status and turn count

WebSocket:
  WS   /api/v1/voice/ws/{session_id}
      → Binary frames: client sends raw audio, server sends back MP3 chunks
      → JSON control frames: {"type": "end"} to close gracefully

The WebSocket path is the primary production interface — it enables the seamless
continuous conversation loop where the client auto-listens after each response.
"""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.api.deps import get_conversation_service
from app.services.conversation_service import ConversationService

router = APIRouter()
logger = logging.getLogger(__name__)


# ── REST: start session ───────────────────────────────────────────────────────

@router.post(
    "/start/{session_id}",
    response_class=Response,
    responses={200: {"content": {"audio/mpeg": {}}}},
    summary="Start a discovery session — returns opening greeting as MP3",
)
async def start_session(
    session_id: str,
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Response:
    audio = await svc.start_session(session_id)
    if not audio:
        raise HTTPException(500, "TTS returned no audio for opening message.")
    return Response(content=audio, media_type="audio/mpeg")


# ── REST: single turn ─────────────────────────────────────────────────────────

@router.post(
    "/turn/{session_id}",
    response_class=Response,
    responses={200: {"content": {"audio/mpeg": {}}}},
    summary="Submit audio for one turn — returns next question as MP3",
)
async def voice_turn(
    session_id: str,
    audio: UploadFile,
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Response:
    allowed = {"audio/wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/webm", "audio/ogg"}
    if audio.content_type not in allowed:
        raise HTTPException(415, f"Unsupported audio format: {audio.content_type}")

    audio_bytes = await audio.read()
    from pathlib import Path
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"

    mp3_bytes, _text, is_final = await svc.process_turn(session_id, audio_bytes, suffix)

    if not mp3_bytes:
        raise HTTPException(500, "Voice pipeline returned no audio.")

    headers = {"X-Session-Final": "true" if is_final else "false"}
    return Response(content=mp3_bytes, media_type="audio/mpeg", headers=headers)


# ── REST: session status ──────────────────────────────────────────────────────

@router.get("/status/{session_id}", summary="Get session status")
async def session_status(
    session_id: str,
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> dict:
    session = svc.get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "status": session.status,
        "turn": session.turn,
        "max_turns": session.max_turns,
    }


# ── WebSocket: seamless continuous conversation ───────────────────────────────

@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> None:
    """
    WebSocket voice conversation protocol:

    Client → Server:
      Binary frame:  raw audio bytes (WebM/WAV/MP3)
      JSON text:     {"type": "start"}   — request opening greeting
                     {"type": "end"}     — gracefully close session

    Server → Client:
      Binary frame:  MP3 audio chunk(s) for the current response
      JSON text:     {"type": "turn_end", "is_final": bool, "turn": int}
                     {"type": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info("[WS %s] Connected", session_id)

    try:
        while True:
            # Receive next message (binary audio or JSON control)
            message = await websocket.receive()

            # ── Control frame ─────────────────────────────────────────────
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                    continue

                if data.get("type") == "start":
                    # Kick off session — send opening greeting
                    audio = await svc.start_session(session_id)
                    if audio:
                        await websocket.send_bytes(audio)
                    session = svc.get_or_create_session(session_id)
                    await websocket.send_text(json.dumps({
                        "type": "turn_end",
                        "is_final": False,
                        "turn": session.turn,
                    }))

                elif data.get("type") == "end":
                    svc.end_session(session_id)
                    await websocket.send_text(json.dumps({"type": "session_ended"}))
                    break

            # ── Audio frame ───────────────────────────────────────────────
            elif "bytes" in message:
                audio_bytes: bytes = message["bytes"]
                if not audio_bytes:
                    continue

                session = svc.get_or_create_session(session_id)

                # Stream sentence-by-sentence for lower latency
                async for chunk in svc.stream_turn(session_id, audio_bytes, ".webm"):
                    await websocket.send_bytes(chunk)

                session = svc.get_or_create_session(session_id)
                is_final = session.status.value == "completed"

                await websocket.send_text(json.dumps({
                    "type": "turn_end",
                    "is_final": is_final,
                    "turn": session.turn,
                }))

                if is_final:
                    break

    except WebSocketDisconnect:
        logger.info("[WS %s] Client disconnected", session_id)
    except Exception as exc:
        logger.error("[WS %s] Error: %s", session_id, exc, exc_info=True)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass
    finally:
        logger.info("[WS %s] Session closed at turn %d",
                    session_id, svc.get_or_create_session(session_id).turn)
