"""Schemas for audio and subtitle generation."""

from pydantic import BaseModel


class VoiceoverArtifact(BaseModel):
    """Information about a generated voiceover audio file."""

    provider: str
    audio_path: str
    duration_seconds: float | None = None


class SubtitleSegment(BaseModel):
    """Timed subtitle segment."""

    index: int
    start_seconds: float
    end_seconds: float
    text: str
