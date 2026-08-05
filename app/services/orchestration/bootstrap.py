"""Application startup helpers."""

from pathlib import Path

from app.core.config import Settings


def ensure_runtime_directories(settings: Settings) -> None:
    """Create runtime directories required by the application."""

    required_dirs: tuple[Path, ...] = (
        settings.videos_root,
        settings.assets_root,
        settings.output_root,
        settings.temp_root,
    )
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
