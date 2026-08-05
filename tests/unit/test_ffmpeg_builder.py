from app.core.config import Settings
from app.domain.schemas.rendering import RenderRequest
from app.services.rendering.ffmpeg_builder import FFmpegCommandBuilder


def test_ffmpeg_builder_creates_instagram_ready_command() -> None:
    settings = Settings(FFMPEG_BINARY="ffmpeg")
    builder = FFmpegCommandBuilder(settings)
    request = RenderRequest(
        background_video_path="videos/Germany/germany_city.mp4",
        output_video_path="output/renders/test.mp4",
        hook_text="Fully Funded Master's Scholarship in Germany",
        subtitle_path="output/subtitles/test.srt",
        voiceover_audio_path="output/audio/test.mp3",
        background_music_path="assets/music/bg.mp3",
        logo_path="assets/logo/logo.png",
        target_duration_seconds=20,
    )

    command = builder.build(request)
    command_text = " ".join(command)

    assert command[0] == "ffmpeg"
    assert "libx264" in command
    assert "aac" in command
    assert "1080:1920" in command_text
    assert "drawtext" in command_text
    assert "subtitles=" in command_text
    assert "overlay=" in command_text
    assert "amix=inputs=2" in command_text
