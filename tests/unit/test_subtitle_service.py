from pathlib import Path

from app.services.media.subtitle_service import SubtitleService


def test_build_segments_splits_sentences_and_assigns_duration() -> None:
    text = "Applications are open now. Study in Germany with funding."

    segments = SubtitleService.build_segments(text, total_duration_seconds=6.0)

    assert len(segments) == 2
    assert segments[0].start_seconds == 0.0
    assert segments[-1].end_seconds == 6.0
    assert segments[0].text == "Applications are open now."


def test_write_srt_outputs_valid_blocks(tmp_path: Path) -> None:
    segments = SubtitleService.build_segments(
        "Applications are open now. Apply before the deadline.",
        total_duration_seconds=5.0,
    )

    output_path = SubtitleService.write_srt(segments, tmp_path / "sample.srt")

    contents = output_path.read_text(encoding="utf-8")
    assert "1" in contents
    assert "-->" in contents
    assert "Applications are open now." in contents
