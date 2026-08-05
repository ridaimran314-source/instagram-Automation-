"""Download assets and render a 1080x1920 Reel with FFmpeg."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import httpx

from config import settings

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920
SAFE_MARGIN = 70
MAX_TEXT_WIDTH = WIDTH - (SAFE_MARGIN * 2)

try:
    from PIL import ImageFont as _ImageFont
except Exception:  # pragma: no cover - Pillow missing, fall back to estimates
    _ImageFont = None

_font_cache: dict[int, object] = {}


def _pil_font(size: int):
    if _ImageFont is None:
        return None
    if size not in _font_cache:
        try:
            _font_cache[size] = _ImageFont.truetype(str(settings.resolved_font()), size)
        except Exception:
            _font_cache[size] = None
    return _font_cache[size]


def text_width_px(text: str, size: int) -> float:
    """Measured width of one line at a given font size."""
    font = _pil_font(size)
    if font is None:
        # Rough fallback: bold serif averages ~0.55em per character
        return len(text) * size * 0.55
    try:
        return float(font.getlength(text))
    except Exception:
        return len(text) * size * 0.55


def wrap_to_width(text: str, size: int, max_width: float) -> list[str]:
    """Greedy word wrap using measured pixel width; honours existing newlines."""
    lines: list[str] = []
    for paragraph in [p.strip() for p in text.split("\n") if p.strip()]:
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if current and text_width_px(candidate, size) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines or [text.strip()]


def fit_text_lines(
    text: str,
    base_size: int,
    max_width: float = MAX_TEXT_WIDTH,
    max_lines: int = 3,
    min_size: int = 40,
) -> tuple[list[str], int]:
    """Shrink the font until every line fits the safe area within max_lines."""
    size = base_size
    while size >= min_size:
        lines = wrap_to_width(text, size, max_width)
        if len(lines) <= max_lines and all(
            text_width_px(line, size) <= max_width for line in lines
        ):
            return lines, size
        size -= 3

    lines = wrap_to_width(text, min_size, max_width)[:max_lines]
    # Last resort: a single unbreakable word wider than the frame
    fixed: list[str] = []
    for line in lines:
        while line and text_width_px(line, min_size) > max_width:
            line = line[:-1]
        fixed.append(line)
    return fixed, min_size

_DANGLING = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "with", "from",
}


def _trim_complete(text: str, max_len: int) -> str:
    """Cut on word boundaries and never end on 'in/the/for...'."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) > max_len:
        cut = text[: max_len + 1]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        text = cut
    words = text.split()
    while words and words[-1].lower().strip(".,!?") in _DANGLING:
        words.pop()
    return " ".join(words).strip() or "Scholarship Update"


def _clean_ascii(value: str) -> str:
    text = (value or "").replace("\r", "\n")
    # Keep apostrophes (Master's), commas, and exclamation marks
    text = (
        text.replace("'", "'")
        .replace("'", "'")
        .replace(""", '"')
        .replace(""", '"')
        .replace("`", "'")
    )
    # Allow letters, digits, space, newline, and common punctuation: , ! ? . ' & - ( )
    allowed = set("\n ,!?.'&-()/:#+")
    text = "".join(
        ch for ch in text
        if ch in allowed or ch.isalnum() or ch == " "
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text).strip()
    return text


def wrap_overlay_lines(text: str, max_chars_per_line: int = 30, max_lines: int = 3) -> str:
    """Wrap words; never leave a dangling last word like 'in'/'the'."""
    words = text.split()
    if not words:
        return "Scholarship Update"
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars_per_line:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if len(lines) >= max_lines:
            # Prefer keeping final short country token on last line
            if word.upper() in {"UK", "USA", "UAE", "EU"} or (len(word) <= 8 and word[0].isupper()):
                merged = f"{lines[-1]} {word}".strip()
                if len(merged) <= max_chars_per_line + 6:
                    lines[-1] = merged
            break
        current = word if len(word) <= max_chars_per_line else word[:max_chars_per_line]
    if current and len(lines) < max_lines:
        lines.append(current)
    elif current and lines:
        # merge leftover into last line if possible
        merged = f"{lines[-1]} {current}".strip()
        if len(merged) <= max_chars_per_line + 8:
            lines[-1] = merged

    # Strip dangling endings after wrap (fixes "Scholarships in")
    while lines:
        last_words = lines[-1].split()
        if last_words and last_words[-1].lower().strip(".,!?") in _DANGLING:
            last_words.pop()
            if last_words:
                lines[-1] = " ".join(last_words)
            else:
                lines.pop()
            continue
        break

    return "\n".join(lines[:max_lines]) or "Scholarship Update"


def sanitize_overlay_text(value: str, max_len: int = 72) -> str:
    """Make text safe for on-video overlays (complete phrases only)."""
    raw = _clean_ascii(value)
    text = re.sub(r"\s+", " ", raw.replace("\n", " ")).strip()

    # Force ONE slide with complete phrase — never end a line on "in"
    m = re.match(
        r"^(Fully Funded(?: Scholarships)?)\s+in\s+(.+)$",
        text,
        flags=re.I,
    )
    if m:
        left = m.group(1).strip()
        country = m.group(2).strip()
        if country and country.lower() not in _DANGLING:
            return _balance_brackets(f"{left}\nin {country}")

    if "\n" in raw:
        parts = [p.replace("\n", " ").strip() for p in raw.split("\n") if p.strip()]
        parts = [_balance_brackets(_trim_complete(p, 40)) for p in parts if p]
        parts = [p for p in parts if p]
        if not parts:
            return "Scholarship Update"
        return "\n".join(parts[:3])

    text = _trim_complete(text, max_len) or "Scholarship Update"
    if re.search(r"\bin(?:\s+the)?\s*$", text, flags=re.I):
        m2 = re.search(r"\bin\s+((?:the\s+)?[A-Za-z][A-Za-z .'-]{0,30})$", raw, flags=re.I)
        if m2:
            base = re.sub(r"\s+in(?:\s+the)?\s*$", "", text, flags=re.I).strip()
            return _balance_brackets(f"{base}\nin {m2.group(1).strip()}")
        text = re.sub(r"\s+in(?:\s+the)?\s*$", "", text, flags=re.I).strip() or text

    # No character-based wrapping here: the renderer wraps by measured pixel width
    return _balance_brackets(text)


def _balance_brackets(text: str) -> str:
    """Remove cut-off parentheticals like 'Arts (School of Music limited'."""
    raw = (text or "").strip()
    # Balance each line separately; collapsing first would destroy line breaks
    if "\n" in raw:
        return "\n".join(
            _balance_brackets(line) for line in raw.split("\n") if line.strip()
        )
    t = re.sub(r"[ \t]+", " ", raw)
    if not t:
        return t

    opens = t.count("(")
    closes = t.count(")")
    if opens > closes:
        idx = t.find("(")
        if idx > 0:
            before = t[:idx].rstrip(" ,-–—:")
            if len(before) >= 3:
                return before
        t = re.sub(r"\([^)]*$", "", t).strip()
        if opens - closes == 1 and len(t) <= 42 and "(" in (text or ""):
            # rare: keep and close if almost complete
            original = re.sub(r"\s+", " ", (text or "").strip())
            if original.count("(") == 1 and len(original) <= 36:
                return original + ")"
        return t.rstrip(" ,-–—:")
    if closes > opens:
        while t.count(")") > t.count("("):
            t = re.sub(r"\)(?=[^)]*$)", "", t, count=1)
    return t.strip()


def sanitize_hook_parts(value: str) -> tuple[str, str]:
    """Split hook into pill line + optional subtitle (complete phrases)."""
    raw = _clean_ascii(value)
    parts = [p.strip() for p in raw.split("\n") if p.strip()]
    if not parts:
        return "Fully Funded Opportunity", ""
    pill = wrap_overlay_lines(
        _trim_complete(parts[0], 40),
        max_chars_per_line=24,
        max_lines=2,
    )
    under = ""
    if len(parts) > 1:
        under = wrap_overlay_lines(
            _trim_complete(" ".join(parts[1:]), 40),
            max_chars_per_line=22,
            max_lines=2,
        )
    return pill, under


def fontsize_for(text: str, base: int) -> int:
    lines = [ln for ln in text.split("\n") if ln.strip()]
    longest = max((len(line) for line in lines), default=1)
    line_count = max(1, len(lines))
    size = base
    if longest >= 28 or line_count >= 3:
        size = max(48, int(base * 0.78))
    elif longest >= 22 or line_count >= 2:
        size = max(54, int(base * 0.88))
    elif longest >= 16:
        size = max(58, int(base * 0.94))
    return size


def escape_filter_path(path: Path) -> str:
    text = path.resolve().as_posix()
    return text.replace("\\", "/").replace(":", "\\:").replace("'", r"\'")


def _guess_suffix(url: str, content_type: str | None, fallback: str) -> str:
    lower = url.lower().split("?", 1)[0]
    for ext in (".mp4", ".mov", ".webm", ".m4v", ".mp3", ".m4a", ".wav", ".aac"):
        if lower.endswith(ext):
            return ext
    if content_type:
        ct = content_type.lower()
        if "mp4" in ct or "quicktime" in ct:
            return ".mp4"
        if "mpeg" in ct or "mp3" in ct:
            return ".mp3"
        if "wav" in ct:
            return ".wav"
        if "aac" in ct:
            return ".m4a"
    return fallback


def extract_google_drive_id(url: str) -> str | None:
    patterns = (
        r"drive\.google\.com/file/d/([^/]+)",
        r"drive\.google\.com/uc\?.*?id=([^&]+)",
        r"drive\.usercontent\.google\.com/download\?.*?id=([^&]+)",
        r"[?&]id=([a-zA-Z0-9_-]{10,})",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _looks_like_html(data: bytes) -> bool:
    head = data[:200].lstrip().lower()
    return head.startswith(b"<!doctype") or head.startswith(b"<html") or b"<html" in head


def _looks_like_media(path: Path, fallback_suffix: str) -> bool:
    data = path.read_bytes()[:64]
    if _looks_like_html(data):
        return False
    if fallback_suffix in {".mp4", ".mov", ".m4v", ".m4a"}:
        return b"ftyp" in data
    if fallback_suffix == ".mp3":
        return data.startswith(b"ID3") or data[:2] == b"\xff\xfb" or data[:2] == b"\xff\xf3"
    if fallback_suffix == ".wav":
        return data.startswith(b"RIFF")
    # Unknown audio/video: accept if not HTML and reasonably large
    return path.stat().st_size > 50_000


def _parse_drive_confirm(html: str) -> str | None:
    patterns = (
        r"confirm=([0-9A-Za-z_-]+)",
        r'name="confirm"\s+value="([^"]+)"',
        r'"downloadForm".*?confirm=([0-9A-Za-z_-]+)',
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            return match.group(1)
    return None


def _stream_download(client: httpx.Client, url: str, path: Path, max_bytes: int) -> str:
    with client.stream("GET", url) as response:
        response.raise_for_status()
        content_type = (response.headers.get("content-type") or "").lower()
        size = 0
        with path.open("wb") as handle:
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(f"Download exceeds {max_bytes // (1024 * 1024)}MB limit")
                handle.write(chunk)
    return content_type


def download_file(url: str, dest_dir: Path, fallback_suffix: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = settings.max_download_mb * 1024 * 1024
    drive_id = extract_google_drive_id(url)

    candidate_urls: list[str] = []
    if drive_id:
        candidate_urls.extend(
            [
                f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&confirm=t",
                f"https://drive.google.com/uc?export=download&id={drive_id}&confirm=t",
            ]
        )
    else:
        candidate_urls.append(url)

    last_error = "Download failed"
    with httpx.Client(follow_redirects=True, timeout=60.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        for candidate in candidate_urls:
            path = dest_dir / f"{uuid.uuid4().hex}{fallback_suffix}"
            try:
                content_type = _stream_download(client, candidate, path, max_bytes)
                head = path.read_bytes()[:500]

                # Large Drive files sometimes return an HTML interstitial
                if drive_id and ("text/html" in content_type or _looks_like_html(head)):
                    html = path.read_text(encoding="utf-8", errors="ignore")
                    confirm = _parse_drive_confirm(html)
                    path.unlink(missing_ok=True)
                    if not confirm:
                        last_error = "Google Drive returned HTML instead of media"
                        continue
                    confirmed = (
                        f"https://drive.usercontent.google.com/download?"
                        f"id={drive_id}&export=download&confirm={confirm}"
                    )
                    path = dest_dir / f"{uuid.uuid4().hex}{fallback_suffix}"
                    content_type = _stream_download(client, confirmed, path, max_bytes)
                    head = path.read_bytes()[:500]

                if path.stat().st_size < 1024 or _looks_like_html(head):
                    path.unlink(missing_ok=True)
                    last_error = (
                        "Google Drive returned HTML instead of a media file "
                        "(check sharing is Anyone with the link)"
                    )
                    continue

                final_suffix = _guess_suffix(candidate, content_type, fallback_suffix)
                if final_suffix != path.suffix:
                    renamed = path.with_suffix(final_suffix)
                    path.rename(renamed)
                    path = renamed

                if not _looks_like_media(path, fallback_suffix):
                    path.unlink(missing_ok=True)
                    last_error = f"Downloaded file is not valid media ({fallback_suffix})"
                    continue

                logger.info(
                    "Downloaded %s bytes from %s",
                    path.stat().st_size,
                    candidate.split("?", 1)[0],
                )
                return path
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                path.unlink(missing_ok=True)
                logger.warning("Download attempt failed for %s: %s", candidate[:80], exc)

    raise ValueError(last_error)


def prune_old_renders(output_dir: Path) -> None:
    files = sorted(output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in files[settings.keep_renders :]:
        stale.unlink(missing_ok=True)


def build_scale_command(
    video_path: Path,
    scaled_path: Path,
    duration_seconds: float,
    start_seconds: float = 0.0,
    clip_index: int = 0,
) -> list[str]:
    """Scale/crop a short slice as a clean hard cut (no black fades)."""
    # Vary framing per beat so cuts read as new shots, not the same frame
    zoom_steps = (1.0, 1.08, 1.04, 1.12)
    zoom = zoom_steps[clip_index % len(zoom_steps)]
    scale_w = int(WIDTH * zoom)
    scale_h = int(HEIGHT * zoom)
    # Shift crop window slightly (left / center / right) for extra variety
    offsets = ("(iw-ow)/2", "0", "(iw-ow)", "(iw-ow)/2")
    crop_x = offsets[clip_index % len(offsets)]
    cmd = [
        settings.ffmpeg_binary,
        "-y",
        "-threads",
        "1",
        "-filter_threads",
        "1",
    ]
    if start_seconds > 0:
        cmd.extend(["-ss", f"{start_seconds:.3f}"])
    cmd.extend(
        [
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-t",
            f"{duration_seconds:.3f}",
            "-vf",
            (
                f"fps=30,scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase:"
                f"flags=bilinear,crop={WIDTH}:{HEIGHT}:{crop_x}:(ih-oh)/2,setsar=1"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "1",
            str(scaled_path),
        ]
    )
    return cmd


def build_concat_command(segment_paths: list[Path], concat_list: Path, output_path: Path) -> list[str]:
    lines = []
    for path in segment_paths:
        escaped = path.resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [
        settings.ffmpeg_binary,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(output_path),
    ]


def _fade_alpha(start: float, fade: float = 0.35) -> str:
    # Fade text in over `fade` seconds after start
    return (
        f"if(lt(t\\,{start:.3f})\\,0\\,"
        f"if(lt(t\\,{start + fade:.3f})\\,(t-{start:.3f})/{fade:.3f}\\,1))"
    )


def _alpha_in_out(t0: float, t1: float, fade_in: float = 0.42, fade_out: float = 0.28) -> str:
    """Fade in at slide start, fade out before slide ends."""
    tin = t0 + fade_in
    tout_start = max(tin + 0.08, t1 - fade_out)
    return (
        f"if(lt(t\\,{t0:.3f})\\,0\\,"
        f"if(lt(t\\,{tin:.3f})\\,(t-{t0:.3f})/{fade_in:.3f}\\,"
        f"if(lt(t\\,{tout_start:.3f})\\,1\\,"
        f"if(lt(t\\,{t1:.3f})\\,({t1:.3f}-t)/{max(0.05, t1 - tout_start):.3f}\\,0))))"
    )


def _fontsize_pop(base: int, t0: float, pop_s: float = 0.38) -> str:
    """Scale text from ~78% → 108% → 100% (pop / zoom-in)."""
    mid = t0 + pop_s * 0.65
    end = t0 + pop_s
    return (
        f"{base}*("
        f"if(lt(t\\,{t0:.3f})\\,0.78\\,"
        f"if(lt(t\\,{mid:.3f})\\,0.78+0.30*((t-{t0:.3f})/{max(0.05, mid - t0):.3f})\\,"
        f"if(lt(t\\,{end:.3f})\\,1.08-0.08*((t-{mid:.3f})/{max(0.05, end - mid):.3f})\\,1)))"
    )


def build_ffmpeg_command(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    text_dir: Path,
    texts: list[str],
    duration_seconds: int,
    music_volume: float,
) -> list[str]:
    font = settings.resolved_font()
    if not font.exists():
        raise RuntimeError(
            f"No font file found at {font}. Set FONT_PATH to a .ttf file."
        )
    font_arg = f":fontfile='{escape_filter_path(font)}'"
    logger.info("Using font: %s", font)

    slides = [sanitize_overlay_text(t, 78) for t in (texts or []) if str(t).strip()]
    if not slides:
        slides = ["Fully Funded Scholarship", "Details in the Caption"]

    n = len(slides)
    seg = duration_seconds / float(n)
    # Lora Bold (serif) — white + outline; serif strokes need a lighter border
    outline = "borderw=4:bordercolor=black@0.95"
    shadow = "shadowcolor=black@0.5:shadowx=2:shadowy=3"
    y_base = "h*0.32"
    # Fast text in/out timed with clip changes
    fade_in = 0.18
    fade_out = 0.14

    filters: list[str] = []
    for i, slide in enumerate(slides):
        # Lora has a smaller x-height than sans fonts, so bump the base size
        base_size = 76 if i == 0 else 70
        lines, size = fit_text_lines(slide, base_size)
        line_height = int(size * 1.24)
        block_top = f"{y_base}-{(line_height * (len(lines) - 1)) // 2}"

        t0 = round(i * seg, 3)
        t1 = round((i + 1) * seg, 3) if i < n - 1 else float(duration_seconds)
        alpha = _alpha_in_out(t0, t1, fade_in=fade_in, fade_out=fade_out)
        enable = f"between(t\\,{t0:.3f}\\,{t1:.3f})" if i < n - 1 else f"gte(t\\,{t0:.3f})"
        style = f"fontsize={size}:fontcolor=white:{outline}:{shadow}"

        # One drawtext per line so every line is centred and clamped on its own
        for j, line in enumerate(lines):
            path = text_dir / f"slide_{i}_{j}.txt"
            path.write_text(line, encoding="utf-8")
            text_file = escape_filter_path(path)
            x_center = (
                f"max({SAFE_MARGIN}\\,min((w-text_w)/2\\,w-text_w-{SAFE_MARGIN}))"
            )
            rise = f"(36*max(0\\,1-min(1\\,(t-{t0:.3f})/{fade_in:.3f})))"
            y_pos = f"{block_top}+{j * line_height}+{rise}"
            filters.append(
                f"drawtext=textfile='{text_file}'{font_arg}:{style}:"
                f"x='{x_center}':y='{y_pos}':alpha='{alpha}':enable='{enable}'"
            )
        logger.info("Slide %s: size=%s lines=%s", i, size, lines)

    video_filter = "[0:v]" + ",".join(filters) + "[vout]"
    fade_out_start = max(0.0, float(duration_seconds) - 1.2)
    audio_filter = (
        f"[1:a]volume={music_volume:.2f},"
        f"afade=t=in:st=0:d=0.8,"
        f"afade=t=out:st={fade_out_start:.3f}:d=1.2,"
        f"atrim=start=0:end={int(duration_seconds)},"
        f"asetpts=PTS-STARTPTS[aout]"
    )

    return [
        settings.ffmpeg_binary,
        "-y",
        "-i",
        str(video_path),
        "-stream_loop",
        "-1",
        "-i",
        str(music_path),
        "-filter_complex",
        f"{video_filter};{audio_filter}",
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-t",
        str(duration_seconds),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-threads",
        "1",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def _run_ffmpeg(command: list[str], label: str) -> None:
    logger.info("Running FFmpeg %s", label)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.error("FFmpeg %s stderr: %s", label, (result.stderr or "")[-4000:])
        if result.returncode in (-9, 137):
            raise RuntimeError(
                "FFmpeg ran out of memory on the server. Use a shorter/smaller source clip."
            )
        raise RuntimeError((result.stderr or "")[-1500:] or f"FFmpeg {label} failed")


def render_reel(
    video_urls: list[str],
    music_url: str,
    hook: str = "",
    script: str = "",
    cta: str = "",
    texts: list[str] | None = None,
    duration_seconds: int = 15,
    music_volume: float = 0.38,
) -> tuple[str, Path]:
    slides = [t for t in (texts or []) if str(t).strip()]
    if not slides:
        slides = [
            hook or "Fully Funded Scholarship",
            script or "Applications are open",
            cta or "Apply Now",
        ]
    slides = slides[:8]
    duration_seconds = max(12, min(int(duration_seconds or (len(slides) * 2.1)), 17))

    urls = [u for u in (video_urls or []) if u]
    if not urls:
        raise ValueError("At least one video_url / video_urls entry is required")

    unique: list[str] = []
    for u in urls:
        if u not in unique:
            unique.append(u)

    # Cut every ~1.8s regardless of slide count so the background never sits still
    clip_count = max(len(slides), round(duration_seconds / 1.8))
    clip_count = max(4, min(clip_count, 10))
    urls = [unique[i % len(unique)] for i in range(clip_count)]
    segment_seconds = duration_seconds / float(clip_count)
    logger.info("Montage slides=%s clips=%s unique=%s seg=%.2fs", len(slides), clip_count, len(unique), segment_seconds)

    work_id = uuid.uuid4().hex
    work_dir = settings.output_dir / "tmp" / work_id
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        music_path = download_file(music_url, work_dir, ".mp3")
        segment_paths: list[Path] = []
        source_cache: dict[str, Path] = {}

        for idx, url in enumerate(urls):
            if url not in source_cache:
                source_cache[url] = download_file(url, work_dir, ".mp4")
            source = source_cache[url]
            scaled = work_dir / f"seg_{idx}.mp4"
            # Different in-point per beat so clips don't feel stuck
            start_seconds = (idx * 1.7) + (0.4 if idx % 2 else 0.0)
            _run_ffmpeg(
                build_scale_command(
                    source,
                    scaled,
                    segment_seconds,
                    start_seconds=start_seconds,
                    clip_index=idx,
                ),
                f"scale-{idx}",
            )
            segment_paths.append(scaled)

        for source in source_cache.values():
            source.unlink(missing_ok=True)

        concat_list = work_dir / "concat.txt"
        scaled_path = work_dir / "scaled.mp4"
        _run_ffmpeg(
            build_concat_command(segment_paths, concat_list, scaled_path),
            "concat",
        )
        for seg in segment_paths:
            seg.unlink(missing_ok=True)

        output_path = output_dir / f"{work_id}.mp4"
        _run_ffmpeg(
            build_ffmpeg_command(
                video_path=scaled_path,
                music_path=music_path,
                output_path=output_path,
                text_dir=work_dir,
                texts=slides,
                duration_seconds=duration_seconds,
                music_volume=music_volume,
            ),
            "overlay",
        )

        if not output_path.exists() or output_path.stat().st_size < 10_000:
            raise RuntimeError("Render produced an empty or missing file")

        prune_old_renders(output_dir)
        return work_id, output_path
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def safe_render_id(render_id: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{16,64}", render_id):
        raise ValueError("Invalid render id")
    return render_id
