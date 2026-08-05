from pathlib import Path

from app.core.config import Settings
from app.services.orchestration.asset_delivery import PublicAssetResolver


def test_public_asset_resolver_maps_output_path_to_public_url(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    render_path = output_root / "renders" / "video.mp4"
    render_path.parent.mkdir(parents=True, exist_ok=True)
    render_path.write_bytes(b"video")

    settings = Settings(
        OUTPUT_ROOT=str(output_root),
        PUBLIC_ASSET_BASE_URL="https://cdn.example.com/reels",
    )

    resolver = PublicAssetResolver(settings)
    public_url = resolver.resolve_public_url(str(render_path))

    assert public_url == "https://cdn.example.com/reels/renders/video.mp4"
