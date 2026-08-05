# Setup Checklist — Instagram Scholarship Reels

Follow these steps in order. Do not run the pipeline until the checklist is green.

## 1. Google Sheet columns

Keep your existing columns A–F, then **add** these headers in row 1:

| Col | Header | Purpose |
|-----|--------|---------|
| A | Scholarship Name | Required |
| B | Scholarship Type | Overlay / caption |
| C | Deadline | `YYYY-MM-DD` |
| D | Host Country | Picks video folder |
| E | Degree Type | Overlay / caption |
| F | Field of Study | Caption / voice |
| G | Status | `Pending` / `Processing` / `Published` / `Failed` |
| H | Instagram URL | Filled by app |
| I | Publish Date | Filled by app |
| J | Error | Filled on failure |
| K | Last Processed At | Filled by app |

For every row you want processed, set **Status** = `Pending`.

## 2. Google Cloud credentials

1. Create a Google Cloud project → enable **Google Sheets API**.
2. Create a **Service Account** → download JSON key.
3. Save it as `secrets/google-sa.json` (this folder is local-only).
4. Open the JSON and copy `client_email`.
5. In Google Sheets: **Share** → paste that email → role **Editor**.
6. Copy the Sheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`
7. Put `SHEET_ID` into `.env` as `GOOGLE_SHEET_ID`.

## 3. Videos

Put stock MP4s here (one folder per country):

```
videos/
  Germany/*.mp4
  Australia/*.mp4
  UK/*.mp4
  USA/*.mp4
  Qatar/*.mp4
  Default/*.mp4   ← fallback if country folder missing
```

Aliases: `United Kingdom` → `UK`, `United States` → `USA`.

## 4. Branding assets

```
assets/logo/logo.png
assets/music/*.mp3   (at least one track)
assets/fonts/        (optional custom fonts)
```

## 5. API keys in `.env`

Fill:

- `OPENAI_API_KEY` — captions + TTS
- Instagram Graph fields (`INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_IG_USER_ID`, …)
- `PUBLIC_ASSET_BASE_URL` — public HTTPS URL that serves `/public/output/...`

Leave `SCHEDULER_ENABLED=false` until a manual test succeeds.

## 6. Install & run

```powershell
cd "C:\Users\HP\OneDrive\Desktop\insta automation"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Open: http://localhost:8000/docs

## 7. First manual run

1. `POST /operations/sync-scholarships` — pulls Sheet into DB  
2. `POST /operations/run-pipeline-once` — processes one Pending row  

Check the Sheet: Status should become `Published` or `Failed` with an Error.

## 8. Turn on daily automation

After a successful live publish:

```env
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Karachi
SCHEDULER_POLL_CRON=0 9 * * *
```

Restart the app.
