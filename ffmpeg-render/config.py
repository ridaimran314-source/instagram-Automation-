"""Settings for the FFmpeg render API."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/lora/Lora-Bold.ttf",
    "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arial.ttf",
)


def resolve_font_path(configured: str) -> str:
    if configured and Path(configured).exists():
        return configured
    for candidate in _FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return configured or _FONT_CANDIDATES[0]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ffmpeg_binary: str = "ffmpeg"
    public_base_url: str = "http://127.0.0.1:8080"
    api_key: str = ""
    output_dir: Path = Path("/tmp/ffmpeg-renders")
    default_duration_seconds: int = 15
    font_path: str = ""
    max_download_mb: int = 200
    keep_renders: int = 40

    def resolved_font(self) -> Path:
        return Path(resolve_font_path(self.font_path))


settings = Settings()
