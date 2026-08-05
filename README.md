# Instagram Scholarship Reel Automation (n8n)

This repo is the **working** automation: an n8n Cloud workflow that builds Instagram Reels and posts them.

It does **not** run as a Python app on a PC. It runs in **n8n** (browser) and calls a small **FFmpeg render API** (Railway).

## What is in this repo

| Folder | Purpose |
|--------|---------|
| `n8n/` | Workflow JSON exports + Code node scripts + AI prompt |
| `ffmpeg-render/` | Video renderer (deploy to Railway) |

No `.env` or `secrets/` are in this repo. Each person uses their own keys.

## Client setup (so it works on their side)

### 1. Export the live workflow (you, the seller)

In n8n Cloud:

1. Open **Scholarship Reel Automation**
2. Click the **⋯** menu (top right of the editor)
3. Click **Download** / **Export**
4. Save the `.json` file
5. Put it in `n8n/` (replace the old export if needed) and share this repo / zip

Credentials are **not** inside the export. Only the node layout and settings are.

### 2. Client: create accounts

Client needs:

- [n8n Cloud](https://n8n.io) account (or self-hosted n8n)
- Google account → Sheet + Drive (clips by country + music folder)
- OpenAI API key (for captions / AI content)
- Instagram Business/Creator account + Meta Graph token + IG User ID
- Railway account (for `ffmpeg-render`) **or** use your shared Railway URL

### 3. Client: import workflow

1. In n8n → **Workflows** → **Import from File**
2. Select the exported JSON
3. Open each red / broken credential node and connect **their** Google, OpenAI, Instagram credentials
4. Open the **Config** node and set:
   - `ffmpeg_api_url` = their Railway URL (example: `https://xxxx.up.railway.app`)
   - `ffmpeg_api_key` = optional, only if they set `API_KEY` on Railway
   - Instagram / page IDs to **their** account

### 4. Client: deploy the video renderer

```powershell
cd ffmpeg-render
railway login
railway link   # or create a new project
railway up
```

Set Railway env:

- `PUBLIC_BASE_URL` = the public Railway HTTPS URL (no trailing slash)
- `API_KEY` = optional shared secret

Health check: `GET https://YOUR-URL/health`

### 5. Client: Sheet + Drive

- Sheet columns must match the workflow (especially **Status** = `Pending` to publish)
- Drive: country clip folders + music folder (same structure you use)
- Share Sheet/Drive with the Google account connected in n8n

### 6. Test

1. Put one row as **Pending**
2. Run the workflow once (manual)
3. Confirm Reel posts and Sheet status becomes **Published**

## Code node scripts

If an imported Code node is empty/outdated, paste from:

- `n8n/prepare_render_body.js`
- `n8n/select_random_clips.js`
- `n8n/select_random_music.js`
- `n8n/ffmpeg_render_code_node.js`
- `n8n/ffmpeg_check_status_code_node.js`
- `n8n/ai_content_prompt.txt` → AI Content system/user prompt

## What the client PC needs

Only a **browser**. No Python install required for this workflow.

PC is used to:

- Edit the Google Sheet
- Open n8n and run / monitor the workflow
- Manage Drive clips and music
