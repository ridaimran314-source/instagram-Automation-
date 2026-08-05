"""Helpers for assembling render template components."""


def escape_drawtext_text(value: str) -> str:
    """Escape text for use in FFmpeg drawtext filters."""

    return (
        value.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )
