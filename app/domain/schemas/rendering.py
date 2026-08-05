"""Schemas for video rendering."""

from pydantic import BaseModel


class RenderRequest(BaseModel):
    """Input payload for reel rendering."""

    background_video_path: str
    output_video_path: str
    hook_text: str
    subtitle_path: str | None = None
    voiceover_audio_path: str | None = None
    background_music_path: str | None = None
    logo_path: str | None = None
    target_width: int = 1080
    target_height: int = 1920
    target_duration_seconds: int = 20


class RenderResult(BaseModel):
    """Result of a rendering run."""

    output_video_path: str
    command: list[str]
