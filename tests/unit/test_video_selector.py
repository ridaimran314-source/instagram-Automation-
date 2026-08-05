from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import DataMappingError
from app.services.media.video_selector import VideoSelector


def build_settings(tmp_path: Path) -> Settings:
    videos_root = tmp_path / "videos"
    videos_root.mkdir(parents=True, exist_ok=True)
    return Settings(
        VIDEOS_ROOT=str(videos_root),
        DEFAULT_VIDEO_FOLDER="Default",
    )


def test_video_selector_uses_country_folder_when_available(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    country_folder = settings.videos_root / "Germany"
    country_folder.mkdir(parents=True, exist_ok=True)
    (country_folder / "germany_city.mp4").write_bytes(b"video")

    selector = VideoSelector(settings)

    asset = selector.select_for_country("Germany")

    assert asset.source_folder == "Germany"
    assert asset.video_path.endswith("germany_city.mp4")


def test_video_selector_falls_back_to_default_folder(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    default_folder = settings.videos_root / "Default"
    default_folder.mkdir(parents=True, exist_ok=True)
    (default_folder / "fallback.mp4").write_bytes(b"video")

    selector = VideoSelector(settings)

    asset = selector.select_for_country("Spain")

    assert asset.source_folder == "Default"
    assert asset.video_path.endswith("fallback.mp4")


def test_video_selector_raises_when_no_assets_exist(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    selector = VideoSelector(settings)

    with pytest.raises(DataMappingError):
        selector.select_for_country("Spain")
