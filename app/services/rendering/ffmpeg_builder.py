"""FFmpeg command builder for Instagram reel exports."""

from pathlib import Path

from app.core.config import Settings
from app.domain.schemas.rendering import RenderRequest
from app.services.rendering.template_engine import escape_drawtext_text


class FFmpegCommandBuilder:
    """Build FFmpeg commands from normalized render requests."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(self, request: RenderRequest) -> list[str]:
        filter_parts = [
            (
                f"[0:v]scale={request.target_width}:{request.target_height}:force_original_aspect_ratio=increase,"
                f"crop={request.target_width}:{request.target_height},setsar=1,"
                f"drawtext=text='{escape_drawtext_text(request.hook_text)}':"
                "fontcolor=white:fontsize=64:x=(w-text_w)/2:y=h*0.12:"
                "box=1:boxcolor=black@0.35:boxborderw=24[v0]"
            )
        ]

        input_index = 1
        audio_sources: list[str] = []

        if request.subtitle_path:
            subtitle_path = self._escape_filter_path(request.subtitle_path)
            filter_parts[0] = (
                filter_parts[0].replace("[v0]", f",subtitles='{subtitle_path}'[v0]")
            )

        if request.logo_path:
            filter_parts.append(
                f"[v0][{input_index}:v]overlay=W-w-40:40[v1]"
            )
            current_video_label = "[v1]"
            input_index += 1
        else:
            current_video_label = "[v0]"

        command = [
            self.settings.ffmpeg_binary,
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            request.background_video_path,
        ]

        if request.logo_path:
            command.extend(["-i", request.logo_path])
        if request.voiceover_audio_path:
            command.extend(["-i", request.voiceover_audio_path])
            audio_sources.append(f"[{input_index}:a]volume=1.0[a0]")
            input_index += 1
        if request.background_music_path:
            command.extend(["-stream_loop", "-1", "-i", request.background_music_path])
            audio_label = f"a{len(audio_sources)}"
            audio_sources.append(f"[{input_index}:a]volume=0.18[{audio_label}]")
            input_index += 1

        filter_complex = list(filter_parts)
        final_video_label = current_video_label

        if audio_sources:
            filter_complex.extend(audio_sources)
            if len(audio_sources) == 1:
                final_audio_label = "[a0]"
            else:
                inputs = "".join(f"[a{i}]" for i in range(len(audio_sources)))
                filter_complex.append(
                    f"{inputs}amix=inputs={len(audio_sources)}:duration=longest[aout]"
                )
                final_audio_label = "[aout]"
        else:
            final_audio_label = None

        command.extend(
            [
                "-filter_complex",
                ";".join(filter_complex),
                "-map",
                final_video_label,
            ]
        )

        if final_audio_label:
            command.extend(["-map", final_audio_label])

        command.extend(
            [
                "-t",
                str(request.target_duration_seconds),
                "-r",
                "30",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                request.output_video_path,
            ]
        )
        return command

    @staticmethod
    def _escape_filter_path(value: str) -> str:
        return value.replace("\\", "/").replace(":", "\\:")
