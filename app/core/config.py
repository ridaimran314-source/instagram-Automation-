"""Typed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import PROJECT_ROOT


class Settings(BaseSettings):
    """Centralized application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Insta Reel Automation", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_timezone: str = Field(default="UTC", alias="SCHEDULER_TIMEZONE")
    scheduler_poll_cron: str = Field(default="*/15 * * * *", alias="SCHEDULER_POLL_CRON")
    videos_root: Path = Field(default=PROJECT_ROOT / "videos", alias="VIDEOS_ROOT")
    assets_root: Path = Field(default=PROJECT_ROOT / "assets", alias="ASSETS_ROOT")
    output_root: Path = Field(default=PROJECT_ROOT / "output", alias="OUTPUT_ROOT")
    temp_root: Path = Field(default=PROJECT_ROOT / "assets" / "temp", alias="TEMP_ROOT")
    default_video_folder: str = Field(default="Default", alias="DEFAULT_VIDEO_FOLDER")
    ffmpeg_binary: str = Field(default="ffmpeg", alias="FFMPEG_BINARY")
    ffprobe_binary: str = Field(default="ffprobe", alias="FFPROBE_BINARY")
    google_application_credentials: str | None = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS",
    )
    google_sheet_id: str | None = Field(default=None, alias="GOOGLE_SHEET_ID")
    google_sheet_worksheet_name: str | None = Field(
        default=None,
        alias="GOOGLE_SHEET_WORKSHEET_NAME",
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_text: str | None = Field(default=None, alias="OPENAI_MODEL_TEXT")
    tts_provider: str = Field(default="openai", alias="TTS_PROVIDER")
    openai_tts_model: str | None = Field(default=None, alias="OPENAI_TTS_MODEL")
    openai_tts_voice: str | None = Field(default=None, alias="OPENAI_TTS_VOICE")
    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str | None = Field(default=None, alias="ELEVENLABS_VOICE_ID")
    instagram_app_id: str | None = Field(default=None, alias="INSTAGRAM_APP_ID")
    instagram_app_secret: str | None = Field(default=None, alias="INSTAGRAM_APP_SECRET")
    instagram_access_token: str | None = Field(default=None, alias="INSTAGRAM_ACCESS_TOKEN")
    instagram_refresh_token: str | None = Field(default=None, alias="INSTAGRAM_REFRESH_TOKEN")
    instagram_ig_user_id: str | None = Field(default=None, alias="INSTAGRAM_IG_USER_ID")
    instagram_facebook_page_id: str | None = Field(
        default=None,
        alias="INSTAGRAM_FACEBOOK_PAGE_ID",
    )
    public_asset_base_url: str | None = Field(default=None, alias="PUBLIC_ASSET_BASE_URL")

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
