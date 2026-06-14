"""
Voice route — speech-to-speech endpoint

POST /api/v1/voice/turn
    Accepts:  multipart/form-data  { session_id: str, audio: UploadFile (WAV/MP3) }
    Returns:  audio/mpeg  (MP3 of the assistant's spoken response)

The pipeline inside:
    uploaded audio → STT → OrchestratorAgent → TTS → MP3 bytes
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.agents.orchestrator import OrchestratorAgent
from app.services.speech_service import SpeechService

router = APIRouter()

_speech = SpeechService()
_agent = OrchestratorAgent()


@router.post(
    "/turn",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "MP3 audio of the assistant's spoken response",
        }
    },
)
async def voice_turn(
    session_id: str = Form(...),
    audio: UploadFile = Form(...),
) -> Response:
    """
    Accepts an audio file (WAV or MP3), runs the full speech-to-speech
    pipeline, and returns MP3 audio bytes.
    """
    # Validate mime type loosely
    if audio.content_type not in ("audio/wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/webm"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {audio.content_type}. Send audio/wav or audio/mpeg.",
        )

    # Save upload to a temp file for the Speech SDK
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    async def llm_fn(transcript: str) -> str:
        return await _agent.run(user_input=transcript, context={"session_id": session_id})

    audio_bytes = await _speech.speech_to_speech(
        llm_fn=llm_fn,
        audio_input_path=tmp_path,
    )

    # Clean up temp file
    Path(tmp_path).unlink(missing_ok=True)

    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Speech pipeline returned no audio.")

    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/voices")
async def list_voices() -> dict:
    """Return available TTS voices (static list for now)."""
    return {
        "voices": [
            {"name": "en-US-AvaMultilingualNeural", "language": "en-US", "default": True},
            {"name": "en-US-AndrewMultilingualNeural", "language": "en-US"},
            {"name": "en-GB-SoniaNeural", "language": "en-GB"},
            {"name": "en-AU-NatashaNeural", "language": "en-AU"},
        ]
    }
