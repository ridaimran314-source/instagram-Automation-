"""Background video selection service."""

import random
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import DataMappingError
from app.domain.schemas.media import SelectedVideoAsset
from app.services.media.country_resolver import normalize_country_name

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


class VideoSelector:
    """Select a background video based on scholarship country."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def select_for_country(self, country: str | None) -> SelectedVideoAsset:
        if not country:
            return self._select_from_default_folder("Unknown")

        resolved_country = normalize_country_name(country)
        country_folder = self.settings.videos_root / resolved_country

        if country_folder.exists():
            candidates = self._list_video_files(country_folder)
            if candidates:
                selected = random.choice(candidates)
                return SelectedVideoAsset(
                    resolved_country=resolved_country,
                    source_folder=country_folder.name,
                    video_path=str(selected),
                )

        return self._select_from_default_folder(resolved_country)

    def _select_from_default_folder(self, resolved_country: str) -> SelectedVideoAsset:
        default_folder = self.settings.videos_root / self.settings.default_video_folder
        candidates = self._list_video_files(default_folder)
        if not candidates:
            raise DataMappingError(
                f"No matching video folder found for '{resolved_country}', and default folder is empty."
            )

        selected = random.choice(candidates)
        return SelectedVideoAsset(
            resolved_country=resolved_country,
            source_folder=default_folder.name,
            video_path=str(selected),
        )

    @staticmethod
    def _list_video_files(folder: Path) -> list[Path]:
        if not folder.exists() or not folder.is_dir():
            return []

        return sorted(
            path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        )
