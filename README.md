# Insta Reel Automation

Production-oriented FastAPI service for generating and publishing scholarship-focused Instagram Reels from Google Sheets + stock videos (no AI video generation).

## Quick start

1. Follow **[SETUP.md](SETUP.md)** (Sheet columns, credentials, assets).
2. Copy secrets into `.env` and `secrets/google-sa.json`.
3. Install and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

4. Manual workflow:
   - `POST /operations/sync-scholarships`
   - `POST /operations/run-pipeline-once`

API docs: http://localhost:8000/docs

## Pipeline

1. Sync pending rows from Google Sheets  
2. Generate caption / hook / voiceover text  
3. Select stock video by host country  
4. TTS + subtitles + FFmpeg render (1080×1920)  
5. Publish Reel via Instagram Graph API  
6. Write Status / URL / Error back to the Sheet  

## Modules

| Area | Location |
|------|----------|
| Config / logging | `app/core/` |
| DB models | `app/db/` |
| Google Sheets | `app/services/google_sheets/` |
| AI text + TTS | `app/services/ai/` |
| Video select | `app/services/media/` |
| FFmpeg render | `app/services/rendering/` |
| Instagram | `app/services/instagram/` |
| Orchestrator | `app/services/orchestration/` |
| Scheduler | `app/workers/` |

## Safety

- Keep `SCHEDULER_ENABLED=false` until a manual publish works.
- Never commit `.env` or `secrets/`.
