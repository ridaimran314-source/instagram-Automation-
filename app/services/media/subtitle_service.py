"""Subtitle generation helpers."""

import re
from pathlib import Path

from app.domain.schemas.audio import SubtitleSegment

DEFAULT_WORDS_PER_SECOND = 2.6


class SubtitleService:
    """Create sentence-based subtitle timings and SRT files."""

    @staticmethod
    def build_segments(
        text: str,
        total_duration_seconds: float | None = None,
    ) -> list[SubtitleSegment]:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text.strip()) if segment.strip()]
        if not sentences:
            return []

        duration = total_duration_seconds or SubtitleService.estimate_duration_seconds(text)
        word_counts = [max(1, len(sentence.split())) for sentence in sentences]
        total_words = sum(word_counts)

        current_start = 0.0
        segments: list[SubtitleSegment] = []

        for index, (sentence, word_count) in enumerate(zip(sentences, word_counts), start=1):
            share = duration * (word_count / total_words)
            end_seconds = current_start + share
            segments.append(
                SubtitleSegment(
                    index=index,
                    start_seconds=round(current_start, 3),
                    end_seconds=round(end_seconds, 3),
                    text=sentence,
                )
            )
            current_start = end_seconds

        if segments:
            segments[-1].end_seconds = round(duration, 3)
        return segments

    @staticmethod
    def write_srt(segments: list[SubtitleSegment], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n\n".join(
            [
                f"{segment.index}\n"
                f"{SubtitleService._format_timestamp(segment.start_seconds)} --> "
                f"{SubtitleService._format_timestamp(segment.end_seconds)}\n"
                f"{segment.text}"
                for segment in segments
            ]
        )
        output_path.write_text(body, encoding="utf-8")
        return output_path

    @staticmethod
    def estimate_duration_seconds(text: str) -> float:
        words = max(1, len(text.split()))
        return round(words / DEFAULT_WORDS_PER_SECOND, 2)

    @staticmethod
    def _format_timestamp(total_seconds: float) -> str:
        total_milliseconds = int(round(total_seconds * 1000))
        hours = total_milliseconds // 3_600_000
        minutes = (total_milliseconds % 3_600_000) // 60_000
        seconds = (total_milliseconds % 60_000) // 1000
        milliseconds = total_milliseconds % 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
