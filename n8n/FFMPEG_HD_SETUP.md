# FFmpeg HD render — deploy & connect to n8n

True **1080×1920** Reels for Instagram. **Replaces Creatomate** in your workflow.

Your canvas currently has something like:

`… → Creatomate Render Body → Creatomate Render → Render Status → Render Successful? → Download → IG …`

Replace that middle with:

`… → Prepare FFmpeg Body → FFmpeg HD Render → IG Create Container → …`

## 1. Deploy the FFmpeg service (Railway / Render)

n8n Cloud **cannot** run FFmpeg itself. Deploy the folder `ffmpeg-render/`.

1. Create a project at [railway.app](https://railway.app) (or Render).
2. Use `ffmpeg-render/Dockerfile`.
3. Set env vars:

| Variable | Example | Notes |
|----------|---------|--------|
| `PUBLIC_BASE_URL` | `https://your-app.up.railway.app` | **Required** — Instagram must fetch this host |
| `API_KEY` | long random string | Optional but recommended |
| `OUTPUT_DIR` | `/data/renders` | Default in Docker |

**Start command** (Railway `$PORT`):

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

4. Check `https://YOUR-URL/health` → `{"status":"ok"}`.

## 2. Add FFmpeg to your n8n workflow (easiest)

1. In n8n: **Workflows → Import from File**
2. Import [`Scholarship_Reel_Automation_FFMPEG.json`](Scholarship_Reel_Automation_FFMPEG.json) as a **new** workflow (do not paste into the old Creatomate one — that creates duplicates).
3. Open **Config** and set:
   - `ffmpeg_api_url` = your Railway/Render URL (**no** trailing slash)
   - `ffmpeg_api_key` = same as `API_KEY` (or leave empty)
4. Reconnect Google Sheets / Drive / OpenAI credentials when prompted.
5. Set one Sheet row to **Pending** and run once.

**Happy path:**  
Select Random Music → **Prepare FFmpeg Body** → **FFmpeg HD Render** → IG Create Container → publish.

`FFmpeg HD Render` returns `{ "url": "https://…/files/….mp4", "status": "succeeded" }`.  
IG uses `$json.url` as `video_url` (same as Creatomate’s output URL).

## 3. Or edit your existing canvas by hand

Delete / disconnect these Creatomate nodes:

- Creatomate Render Body / Prepare Creatomate body  
- Creatomate Render  
- Render Status / Wait / Successful?  
- Download Rendered Video (not needed — FFmpeg URL is already public)

Add:

1. **Config** fields: `ffmpeg_api_url`, `ffmpeg_api_key`
2. **HTTP Request** named `FFmpeg HD Render`
   - Method: `POST`
   - URL: `={{ ($('Config').item.json.ffmpeg_api_url || '').replace(/\/$/, '') + '/render' }}`
   - Header `Content-Type`: `application/json`
   - Header `Authorization`: `={{ $('Config').item.json.ffmpeg_api_key ? 'Bearer ' + $('Config').item.json.ffmpeg_api_key : '' }}`
   - Body (JSON): `video_url`, `music_url`, `hook`, `script`, `cta`, `duration_seconds: 20`, `music_volume: 0.45`
   - Timeout: **300000** ms (5 minutes)
3. Connect: music/clip ready → FFmpeg HD Render → IG Create Container  
4. On IG node, keep `video_url` = `={{ $json.url }}`

## 4. Local smoke test (optional)

```powershell
cd "ffmpeg-render"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:PUBLIC_BASE_URL="http://127.0.0.1:8080"
$env:OUTPUT_DIR=".\renders"
uvicorn main:app --host 0.0.0.0 --port 8080
```

n8n Cloud cannot reach `127.0.0.1` — use Railway/Render (or a tunnel) for real runs.

## 5. Quality notes

- Output is always **1080×1920**, music only (clip audio discarded).
- Soft Drive sources stay soft after upscale — prefer real HD clips.
- Instagram must be able to **GET** `PUBLIC_BASE_URL/files/{id}.mp4` with no login.
