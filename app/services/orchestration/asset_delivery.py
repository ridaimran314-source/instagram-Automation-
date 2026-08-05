"""Helpers for resolving public media URLs for rendered assets."""

from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import ConfigurationError


class PublicAssetResolver:
    """Resolve publicly accessible URLs for locally rendered output assets."""

    def __init__(self, settings: Settings) -> None:
        if not settings.public_asset_base_url:
            raise ConfigurationError("PUBLIC_ASSET_BASE_URL is required for Instagram publishing.")
        self.settings = settings

    def resolve_public_url(self, local_path: str) -> str:
        output_root = self.settings.output_root.resolve()
        asset_path = Path(local_path).resolve()
        relative_path = asset_path.relative_to(output_root)
        return f"{self.settings.public_asset_base_url.rstrip('/')}/{relative_path.as_posix()}"
