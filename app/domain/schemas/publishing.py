"""Schemas for Instagram publishing."""

from pydantic import BaseModel, HttpUrl


class InstagramPublishRequest(BaseModel):
    """Normalized publish request for one reel."""

    media_url: HttpUrl
    caption_text: str


class InstagramPublishResult(BaseModel):
    """Publish result returned by the Instagram service."""

    media_container_id: str
    media_id: str
    status: str
    instagram_url: str | None = None
