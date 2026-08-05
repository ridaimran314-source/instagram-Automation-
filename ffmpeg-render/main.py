"""FastAPI service: HD 1080x1920 Reel renders for n8n."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl, ValidationError, model_validator

from config import settings
from render import render_reel, safe_render_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ffmpeg-render")

app = FastAPI(title="FFmpeg HD Reel Renderer", version="1.6.0")


class RenderRequest(BaseModel):
    video_url: HttpUrl | None = None
    video_urls: list[HttpUrl] = Field(default_factory=list, max_length=8)
    music_url: HttpUrl
    hook: str = "Fully Funded Scholarship"
    script: str = "Applications are open"
    cta: str = "Apply Now"
    texts: list[str] = Field(default_factory=list, max_length=8)
    duration_seconds: int = Field(default=15, ge=10, le=18)
    music_volume: float = Field(default=0.38, ge=0.05, le=1.0)

    @model_validator(mode="after")
    def require_video(self) -> RenderRequest:
        if not self.video_url and not self.video_urls:
            raise ValueError("Provide video_url or video_urls")
        return self

    def resolved_video_urls(self) -> list[str]:
        if self.video_urls:
            return [str(u) for u in self.video_urls]
        return [str(self.video_url)] if self.video_url else []

    def resolved_texts(self) -> list[str]:
        cleaned = [str(t).strip() for t in (self.texts or []) if str(t).strip()]
        if cleaned:
            return cleaned[:6]
        return [
            self.hook.strip() or "Fully Funded Scholarship",
            self.script.strip() or "Applications are open",
            self.cta.strip() or "Apply Now",
        ]


class RenderResponse(BaseModel):
    id: str
    status: str = "succeeded"
    url: str | None = None
    width: int = 1080
    height: int = 1920
    error: str | None = None
    started_at: str | None = None
    render_id: str | None = None


def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    expected = (settings.api_key or "").strip()
    if not expected:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _parse_video_urls(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            pass
    if "\n" in text:
        return [p.strip() for p in text.split("\n") if p.strip()]
    if "," in text and "http" in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if all(p.startswith("http") for p in parts):
            return parts
    return [text]


def _as_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    text = str(value).strip().lstrip("=")
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    text = str(value).strip().lstrip("=")
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _coerce_body(raw: Any) -> dict[str, Any]:
    data = raw
    for _ in range(2):
        if isinstance(data, str):
            text = data.strip()
            if not text or text == "[object Object]":
                raise HTTPException(status_code=422, detail="Empty body from n8n")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=422, detail=f"Invalid JSON body: {exc}") from exc
        else:
            break

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=422,
            detail=f"Body must be an object, got {type(data).__name__}",
        )

    out = {k: v for k, v in data.items() if not str(k).startswith("http")}
    if "video_urls" in out:
        out["video_urls"] = _parse_video_urls(out.get("video_urls"))
    if "texts" in out:
        raw_texts = out.get("texts")
        if isinstance(raw_texts, str):
            if raw_texts.strip().startswith("["):
                try:
                    raw_texts = json.loads(raw_texts)
                except json.JSONDecodeError:
                    raw_texts = [p.strip() for p in raw_texts.split("\n") if p.strip()]
            else:
                raw_texts = [p.strip() for p in raw_texts.split("\n") if p.strip()]
        if isinstance(raw_texts, list):
            out["texts"] = [str(t).strip() for t in raw_texts if str(t).strip()][:6]
    if "duration_seconds" in out:
        out["duration_seconds"] = _as_int(out.get("duration_seconds"), 15)
    if "music_volume" in out:
        out["music_volume"] = _as_float(out.get("music_volume"), 0.38)
    return out


async def _read_request_payload(request: Request) -> Any:
    content_type = (request.headers.get("content-type") or "").lower()
    raw_bytes = await request.body()
    logger.info("Render request content-type=%s bytes=%s", content_type, len(raw_bytes))
    if not raw_bytes:
        raise HTTPException(status_code=422, detail="Empty request body from n8n")

    text = raw_bytes.decode("utf-8", errors="replace")

    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(text, keep_blank_values=True)
        return {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in parsed.items()}

    if "multipart/form-data" in content_type:
        form = await request.form()
        return {k: str(v) for k, v in form.items()}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if "=" in text:
            parsed = parse_qs(text, keep_blank_values=True)
            return {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in parsed.items()}
        raise HTTPException(status_code=422, detail="Invalid JSON body") from None


def _status_path(job_id: str) -> Path:
    return Path(settings.output_dir) / f"{job_id}.status.json"


def _write_job_status(job_id: str, status: str, url: str | None = None, error: str | None = None) -> None:
    from datetime import datetime, timezone

    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    path = _status_path(job_id)
    started_at = None
    if path.exists():
        try:
            started_at = json.loads(path.read_text(encoding="utf-8")).get("started_at")
        except Exception:  # noqa: BLE001
            started_at = None
    if not started_at:
        started_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "id": job_id,
        "status": status,
        "url": url,
        "error": error,
        "started_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _run_render_job(job_id: str, body: RenderRequest) -> None:
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    _write_job_status(job_id, "processing")

    def _do_render() -> None:
        render_id, _path = render_reel(
            video_urls=body.resolved_video_urls(),
            music_url=str(body.music_url),
            hook=body.hook.strip(),
            script=body.script.strip(),
            cta=body.cta.strip(),
            texts=body.resolved_texts(),
            duration_seconds=body.duration_seconds or settings.default_duration_seconds,
            music_volume=body.music_volume,
        )
        final = Path(settings.output_dir) / f"{job_id}.mp4"
        produced = Path(settings.output_dir) / f"{render_id}.mp4"
        if produced.exists() and produced != final:
            produced.replace(final)
        base = settings.public_base_url.rstrip("/")
        _write_job_status(job_id, "succeeded", url=f"{base}/files/{job_id}.mp4")

    try:
        # Hard cap so n8n never waits forever on Drive/FFmpeg hangs
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_do_render)
            fut.result(timeout=300)  # 5 minutes
    except FuturesTimeout:
        logger.error("Async render timed out id=%s", job_id)
        _write_job_status(job_id, "failed", error="Render timed out after 5 minutes")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Async render failed id=%s", job_id)
        _write_job_status(job_id, "failed", error=str(exc)[:2000])


async def _parse_render_request(request: Request) -> RenderRequest:
    raw = await _read_request_payload(request)
    try:
        return RenderRequest.model_validate(_coerce_body(raw))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/render", response_model=RenderResponse, dependencies=[Depends(verify_api_key)])
async def create_render(request: Request) -> RenderResponse:
    """Sync render (use HTTP Request node with timeout 300000)."""
    body = await _parse_render_request(request)
    try:
        render_id, _path = render_reel(
            video_urls=body.resolved_video_urls(),
            music_url=str(body.music_url),
            hook=body.hook.strip(),
            script=body.script.strip(),
            cta=body.cta.strip(),
            texts=body.resolved_texts(),
            duration_seconds=body.duration_seconds or settings.default_duration_seconds,
            music_volume=body.music_volume,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Render failed")
        raise HTTPException(status_code=500, detail=str(exc)[:2000]) from exc

    base = settings.public_base_url.rstrip("/")
    return RenderResponse(
        id=render_id,
        status="succeeded",
        url=f"{base}/files/{render_id}.mp4",
    )


@app.post("/render/async", response_model=RenderResponse, dependencies=[Depends(verify_api_key)])
async def create_render_async(request: Request) -> RenderResponse:
    """Start render in background — returns in <5s (for n8n Code node 60s limit)."""
    body = await _parse_render_request(request)
    job_id = uuid.uuid4().hex
    _write_job_status(job_id, "processing")
    thread = threading.Thread(target=_run_render_job, args=(job_id, body), daemon=True)
    thread.start()
    base = settings.public_base_url.rstrip("/")
    return RenderResponse(
        id=job_id,
        status="processing",
        url=f"{base}/render/{job_id}",
    )


@app.get("/render/{job_id}", response_model=RenderResponse, dependencies=[Depends(verify_api_key)])
def get_render_status(job_id: str) -> RenderResponse:
    try:
        safe_render_id(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc

    status_file = _status_path(job_id)
    mp4 = Path(settings.output_dir) / f"{job_id}.mp4"
    base = settings.public_base_url.rstrip("/")

    if status_file.exists():
        data = json.loads(status_file.read_text(encoding="utf-8"))
        file_url = f"{base}/files/{job_id}.mp4"
        st = (data.get("status") or "processing").lower()
        # If mp4 already exists, never keep clients stuck on "processing"
        if mp4.exists() and st in {"processing", "running", ""}:
            st = "succeeded"
        return RenderResponse(
            id=job_id,
            render_id=job_id,
            status=st,
            url=data.get("url") or (file_url if mp4.exists() or st == "succeeded" else None),
            error=data.get("error"),
            started_at=data.get("started_at"),
        )

    if mp4.exists():
        return RenderResponse(
            id=job_id,
            render_id=job_id,
            status="succeeded",
            url=f"{base}/files/{job_id}.mp4",
        )

    raise HTTPException(status_code=404, detail="Render job not found")


@app.get("/files/{filename}")
def get_file(filename: str) -> FileResponse:
    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=404, detail="Not found")
    render_id = filename[:-4]
    try:
        safe_render_id(render_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc

    path = Path(settings.output_dir) / f"{render_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Render expired or missing")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{render_id}.mp4",
        headers={"Cache-Control": "public, max-age=3600"},
    )
