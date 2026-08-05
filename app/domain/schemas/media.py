"""Schemas for media asset selection."""

from pydantic import BaseModel


class SelectedVideoAsset(BaseModel):
    """Selected background video information."""

    resolved_country: str
    source_folder: str
    video_path: str
