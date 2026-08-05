"""Higher-level Instagram publishing service."""

from app.domain.schemas.publishing import InstagramPublishRequest, InstagramPublishResult
from app.services.instagram.graph_client import InstagramGraphClient


class InstagramPublisher:
    """Publish rendered reels using the Instagram Graph API."""

    def __init__(self, graph_client: InstagramGraphClient) -> None:
        self.graph_client = graph_client

    def publish_reel(self, request: InstagramPublishRequest) -> InstagramPublishResult:
        container_id = self.graph_client.create_reel_container(
            media_url=str(request.media_url),
            caption_text=request.caption_text,
        )
        media_id = self.graph_client.publish_container(container_id)
        status_payload = self.graph_client.get_media_status(media_id)

        return InstagramPublishResult(
            media_container_id=container_id,
            media_id=media_id,
            status=status_payload.get("status_code", "published"),
            instagram_url=status_payload.get("permalink"),
        )
