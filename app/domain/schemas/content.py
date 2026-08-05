"""Schemas for generated reel content."""

from pydantic import BaseModel, Field


class GeneratedReelContent(BaseModel):
    """Structured content used for reel rendering and publishing."""

    hook_text: str = Field(min_length=1, max_length=120)
    script_text: str = Field(min_length=1, max_length=500)
    voiceover_text: str = Field(min_length=1, max_length=700)
    caption_text: str = Field(min_length=1, max_length=2200)
    hashtags_text: str = Field(min_length=1, max_length=500)
