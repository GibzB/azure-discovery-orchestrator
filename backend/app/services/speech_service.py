"""
Azure Speech Services wrapper (STT / TTS)
"""
import azure.cognitiveservices.speech as speechsdk

from app.core.config import settings


class SpeechService:
    def __init__(self) -> None:
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
        )

    def speech_to_text(self, audio_file_path: str) -> str:
        audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        result = recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return ""

    def text_to_speech(self, text: str, output_path: str) -> None:
        audio_config = speechsdk.AudioConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        synthesizer.speak_text_async(text).get()
