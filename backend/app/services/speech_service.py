"""
Speech-to-Speech Service

Pipeline:
    Microphone / audio bytes
        ↓  Azure Speech SDK  (STT)
    Transcript text
        ↓  Azure OpenAI  (GPT-4o via OrchestratorAgent)
    Response text
        ↓  Azure Speech SDK  (TTS)
    Audio bytes → speaker / stream

Usage:
    service = SpeechService()

    # One-shot from a WAV file
    audio_out = await service.speech_to_speech(audio_input_path="input.wav")

    # Stream from microphone (blocking, for CLI / testing)
    service.speech_to_speech_stream(on_response=lambda text: print(text))
"""

import asyncio
import logging
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpeechService:
    # ── Azure Neural voices ───────────────────────────────────────────────────
    # Full list: https://learn.microsoft.com/azure/ai-services/speech-service/language-support
    DEFAULT_VOICE = "en-US-AvaMultilingualNeural"

    def __init__(self) -> None:
        self._speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
        )
        self._speech_config.speech_synthesis_voice_name = self.DEFAULT_VOICE
        # Request compressed audio to reduce bandwidth (MP3 24kHz)
        self._speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3
        )

    # ── Speech-to-Text ────────────────────────────────────────────────────────

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe a WAV/MP3 file to text. Returns empty string on failure."""
        audio_config = speechsdk.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self._speech_config,
            audio_config=audio_config,
        )
        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info("STT recognised: %s", result.text)
            return result.text

        if result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("STT no match: %s", result.no_match_details)
        elif result.reason == speechsdk.ResultReason.Canceled:
            details = result.cancellation_details
            logger.error("STT cancelled: %s — %s", details.reason, details.error_details)

        return ""

    def transcribe_microphone(self) -> str:
        """
        Transcribe a single microphone utterance (push-to-talk style).
        Blocks until the utterance is complete or times out.
        """
        recognizer = speechsdk.SpeechRecognizer(speech_config=self._speech_config)
        logger.info("Listening on microphone…")
        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return ""

    # ── Text-to-Speech ────────────────────────────────────────────────────────

    def synthesise_to_file(self, text: str, output_path: str) -> bool:
        """Synthesise text to an MP3 file. Returns True on success."""
        audio_config = speechsdk.AudioConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._speech_config,
            audio_config=audio_config,
        )
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info("TTS saved to %s", output_path)
            return True

        details = result.cancellation_details
        logger.error("TTS failed: %s — %s", details.reason, details.error_details)
        return False

    def synthesise_to_bytes(self, text: str) -> bytes:
        """Synthesise text and return raw audio bytes (MP3). Returns b'' on failure."""
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._speech_config,
            audio_config=None,  # capture to memory
        )
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return bytes(result.audio_data)

        details = result.cancellation_details
        logger.error("TTS failed: %s — %s", details.reason, details.error_details)
        return b""

    # ── Full Speech-to-Speech ─────────────────────────────────────────────────

    async def speech_to_speech(
        self,
        llm_fn,                     # async callable: (str) -> str  (your OrchestratorAgent)
        audio_input_path: str,
        audio_output_path: str | None = None,
    ) -> bytes:
        """
        Full pipeline: audio file → STT → LLM → TTS → audio bytes.

        Args:
            llm_fn:             Async function that takes a transcript and returns
                                the assistant reply text.
            audio_input_path:   Path to input WAV/MP3 file.
            audio_output_path:  Optional path to save the TTS output MP3.

        Returns:
            Raw MP3 audio bytes of the assistant's spoken response.
        """
        # 1. STT
        transcript = self.transcribe_file(audio_input_path)
        if not transcript:
            logger.warning("STT returned empty transcript for %s", audio_input_path)
            return b""

        # 2. LLM
        response_text: str = await llm_fn(transcript)
        if not response_text:
            logger.warning("LLM returned empty response for transcript: %s", transcript)
            return b""

        # 3. TTS
        if audio_output_path:
            self.synthesise_to_file(response_text, audio_output_path)

        return self.synthesise_to_bytes(response_text)

    def speech_to_speech_microphone(self, llm_fn_sync) -> bytes:
        """
        Convenience method for CLI / testing: microphone → STT → LLM (sync) → TTS → bytes.
        llm_fn_sync must be a synchronous callable: (str) -> str.
        """
        transcript = self.transcribe_microphone()
        if not transcript:
            return b""
        response_text: str = llm_fn_sync(transcript)
        return self.synthesise_to_bytes(response_text)
