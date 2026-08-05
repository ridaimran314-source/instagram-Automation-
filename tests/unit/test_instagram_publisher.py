from app.domain.schemas.publishing import InstagramPublishRequest
from app.services.instagram.publisher import InstagramPublisher


class FakeInstagramGraphClient:
    def create_reel_container(self, media_url: str, caption_text: str) -> str:
        assert media_url == "https://example.com/video.mp4"
        assert "Scholarship" in caption_text
        return "container-123"

    def publish_container(self, creation_id: str) -> str:
        assert creation_id == "container-123"
        return "media-456"

    def get_media_status(self, media_id: str) -> dict:
        assert media_id == "media-456"
        return {
            "status_code": "FINISHED",
            "permalink": "https://instagram.com/reel/abc123",
        }


def test_instagram_publisher_returns_publish_result() -> None:
    publisher = InstagramPublisher(FakeInstagramGraphClient())

    result = publisher.publish_reel(
        InstagramPublishRequest(
            media_url="https://example.com/video.mp4",
            caption_text="Scholarship opportunity now open.",
        )
    )

    assert result.media_container_id == "container-123"
    assert result.media_id == "media-456"
    assert result.status == "FINISHED"
    assert result.instagram_url == "https://instagram.com/reel/abc123"
