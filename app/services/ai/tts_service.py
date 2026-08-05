"""Text-to-speech services."""

import logging
from pathlib import Path

from openai import OpenAI

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.domain.schemas.audio import VoiceoverArtifact

logger = logging.getLogger(__name__)


class OpenAITTSService:
    """Generate voiceover audio using OpenAI TTS."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required.")
        if not settings.openai_tts_model:
            raise ConfigurationError("OPENAI_TTS_MODEL is required.")
        if not settings.openai_tts_voice:
            raise ConfigurationError("OPENAI_TTS_VOICE is required.")

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_tts_model
        self.voice_name = settings.openai_tts_voice
        self.output_root = settings.output_root / "audio"

    def synthesize(self, text: str, file_stem: str) -> VoiceoverArtifact:
        self.output_root.mkdir(parents=True, exist_ok=True)
        output_path = self.output_root / f"{file_stem}.mp3"

        try:
            response = self.client.audio.speech.create(
                model=self.model_name,
                voice=self.voice_name,
                input=text,
            )
            response.write_to_file(output_path)
            return VoiceoverArtifact(
                provider="openai",
                audio_path=str(output_path),
            )
        except Exception as exc:  # pragma: no cover - provider/network dependent
            logger.exception("OpenAI TTS generation failed.")
            raise ExternalServiceError("Failed to generate voiceover audio.") from exc


def build_tts_service(settings: Settings) -> OpenAITTSService:
    """Build the configured TTS provider service."""

    provider = settings.tts_provider.lower()
    if provider == "openai":
        return OpenAITTSService(settings)

    raise ConfigurationError(f"Unsupported TTS provider: {settings.tts_provider}")
