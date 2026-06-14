"""
Conversation Service — Seamless Speech-to-Speech Engine

Manages the full lifecycle of a voice discovery session:

    Orchestrator speaks opening question
        ↓  (client hears it)
    Client speaks answer
        ↓  Azure Speech STT
    Transcript
        ↓  OrchestratorAgent (GPT-4o + MCP tools)
    Next question text
        ↓  Azure Speech TTS
    Audio bytes → streamed back to client
        ↓  (loop continues automatically)

The service is stateful per session_id, maintaining:
  - conversation history (for GPT-4o context)
  - turn counter
  - session status (active / completed / error)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator

from app.agents.orchestrator import OrchestratorAgent
from app.mcp.client import MCPClientManager
from app.services.speech_service import SpeechService

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationSession:
    session_id: str
    history: list[dict] = field(default_factory=list)
    turn: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    max_turns: int = 20


class ConversationService:
    """
    Central service wiring speech ↔ LLM ↔ MCP for all active sessions.
    Instantiated once at app startup and injected via FastAPI dependency.
    """

    def __init__(self, mcp: MCPClientManager | None = None) -> None:
        self._speech = SpeechService()
        self._agent = OrchestratorAgent(mcp=mcp)
        self._sessions: dict[str, ConversationSession] = {}

    # ── Session management ────────────────────────────────────────────────────

    def get_or_create_session(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(session_id=session_id)
        return self._sessions[session_id]

    def end_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].status = SessionStatus.COMPLETED

    # ── Opening turn (no audio input — orchestrator speaks first) ─────────────

    async def start_session(self, session_id: str) -> bytes:
        """
        Kick off a new discovery session.
        Returns MP3 audio of the orchestrator's opening greeting + first question.
        """
        session = self.get_or_create_session(session_id)
        text = await self._agent.opening_message()
        audio = self._speech.synthesise_to_bytes(text)
        session.history.append({"role": "assistant", "content": text})
        session.turn = 1
        logger.info("[%s] Session started. Turn 1: %s", session_id, text[:80])
        return audio

    # ── Regular turn (audio in → audio out) ───────────────────────────────────

    async def process_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        audio_suffix: str = ".wav",
    ) -> tuple[bytes, str, bool]:
        """
        Process one voice turn.

        Args:
            session_id:   Active session identifier.
            audio_bytes:  Raw audio from the client's microphone.
            audio_suffix: File extension (.wav, .webm, .mp3).

        Returns:
            (mp3_audio_bytes, response_text, is_final)
            is_final = True when the session should end after this turn.
        """
        import tempfile
        from pathlib import Path

        session = self.get_or_create_session(session_id)

        if session.status != SessionStatus.ACTIVE:
            return b"", "", True

        # 1. Save audio to temp file for Speech SDK
        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # 2. STT — transcribe client's speech
            transcript = self._speech.transcribe_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if not transcript:
            # Silence or STT failure — ask the client to repeat
            fallback = "I'm sorry, I didn't catch that. Could you please repeat your answer?"
            audio = self._speech.synthesise_to_bytes(fallback)
            return audio, fallback, False

        logger.info("[%s] Turn %d STT: %s", session_id, session.turn, transcript)
        session.history.append({"role": "user", "content": transcript})

        # 3. LLM + MCP tools — generate next question or recommendation
        response_text = await self._agent.run(
            user_input=transcript,
            history=session.history,
        )

        session.turn += 1
        logger.info("[%s] Turn %d response: %s", session_id, session.turn, response_text[:80])

        # 4. Check if session should end
        is_final = (
            session.turn >= session.max_turns
            or "thank you for your time" in response_text.lower()
            or "discovery report" in response_text.lower()
        )
        if is_final:
            session.status = SessionStatus.COMPLETED

        # 5. TTS — synthesise response
        audio = self._speech.synthesise_to_bytes(response_text)

        return audio, response_text, is_final

    # ── Streaming variant (for WebSocket) ─────────────────────────────────────

    async def stream_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        audio_suffix: str = ".wav",
    ) -> AsyncGenerator[bytes, None]:
        """
        Streaming version: yields sentence-level TTS audio chunks as they are
        synthesised, reducing perceived latency.
        """
        import tempfile
        import re
        from pathlib import Path

        session = self.get_or_create_session(session_id)
        if session.status != SessionStatus.ACTIVE:
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            transcript = self._speech.transcribe_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if not transcript:
            fallback = "I'm sorry, I didn't catch that. Could you please repeat?"
            audio = self._speech.synthesise_to_bytes(fallback)
            yield audio
            return

        session.history.append({"role": "user", "content": transcript})
        response_text = await self._agent.run(
            user_input=transcript,
            history=session.history,
        )
        session.turn += 1

        # Split into sentences and yield each as audio
        sentences = re.split(r'(?<=[.?!])\s+', response_text.strip())
        for sentence in sentences:
            if sentence:
                chunk = self._speech.synthesise_to_bytes(sentence)
                if chunk:
                    yield chunk
                    await asyncio.sleep(0)  # let the event loop breathe

        is_final = (
            session.turn >= session.max_turns
            or "thank you for your time" in response_text.lower()
        )
        if is_final:
            session.status = SessionStatus.COMPLETED
