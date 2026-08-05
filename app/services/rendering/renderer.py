"""FFmpeg renderer wrapper."""

import logging
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.domain.schemas.rendering import RenderRequest, RenderResult
from app.services.rendering.ffmpeg_builder import FFmpegCommandBuilder

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """Run FFmpeg renders from normalized requests."""

    def __init__(self, settings: Settings) -> None:
        self.command_builder = FFmpegCommandBuilder(settings)

    def render(self, request: RenderRequest) -> RenderResult:
        output_path = Path(request.output_video_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = self.command_builder.build(request)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            logger.exception("FFmpeg render failed.")
            raise ExternalServiceError(exc.stderr or "FFmpeg render failed.") from exc

        return RenderResult(
            output_video_path=request.output_video_path,
            command=command,
        )
