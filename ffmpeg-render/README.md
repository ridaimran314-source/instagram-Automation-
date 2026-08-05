# FFmpeg HD Reel Renderer

Small FastAPI service used by the n8n scholarship workflow.

- `POST /render` — download clip + music, burn timed text, export **1080×1920** MP4
- `GET /files/{id}.mp4` — public URL Instagram can fetch
- `GET /health` — health check

## Quick start

See [../n8n/FFMPEG_HD_SETUP.md](../n8n/FFMPEG_HD_SETUP.md) for Railway/Render deploy and n8n Config fields (`ffmpeg_api_url`, `ffmpeg_api_key`).

```bash
docker build -t ffmpeg-render .
docker run --rm -p 8080:8080 \
  -e PUBLIC_BASE_URL=https://YOUR-PUBLIC-URL \
  -e API_KEY=optional-secret \
  ffmpeg-render
```
