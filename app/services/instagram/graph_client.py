"""Instagram Graph API client."""

import logging

import httpx

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)


class InstagramGraphClient:
    """Thin wrapper around the Instagram Graph API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.instagram_access_token:
            raise ConfigurationError("INSTAGRAM_ACCESS_TOKEN is required.")
        if not settings.instagram_ig_user_id:
            raise ConfigurationError("INSTAGRAM_IG_USER_ID is required.")

        self.access_token = settings.instagram_access_token
        self.ig_user_id = settings.instagram_ig_user_id
        self.base_url = "https://graph.facebook.com/v20.0"

    def create_reel_container(self, media_url: str, caption_text: str) -> str:
        url = f"{self.base_url}/{self.ig_user_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": media_url,
            "caption": caption_text,
            "share_to_feed": "true",
            "access_token": self.access_token,
        }
        response = self._post(url, payload)
        container_id = response.get("id")
        if not container_id:
            raise ExternalServiceError("Instagram did not return a media container ID.")
        return container_id

    def publish_container(self, creation_id: str) -> str:
        url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        payload = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }
        response = self._post(url, payload)
        media_id = response.get("id")
        if not media_id:
            raise ExternalServiceError("Instagram did not return a media ID.")
        return media_id

    def get_media_status(self, media_id: str) -> dict:
        url = f"{self.base_url}/{media_id}"
        params = {
            "fields": "id,media_product_type,status,status_code,permalink",
            "access_token": self.access_token,
        }
        return self._get(url, params)

    def _post(self, url: str, payload: dict) -> dict:
        try:
            response = httpx.post(url, data=payload, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Instagram Graph POST request failed.")
            raise ExternalServiceError("Instagram Graph API request failed.") from exc

    def _get(self, url: str, params: dict) -> dict:
        try:
            response = httpx.get(url, params=params, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Instagram Graph GET request failed.")
            raise ExternalServiceError("Instagram Graph API request failed.") from exc
