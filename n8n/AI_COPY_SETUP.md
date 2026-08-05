# AI Reel Copy — your retention prompt

Your writing style is now in:

- [`ai_content_prompt.txt`](ai_content_prompt.txt)
- Workflow exports: `Scholarship_Reel_Automation_FFMPEG.json` / `FIXED.json`

## On-video text (FFmpeg, 12s)

| Beat | Source |
|------|--------|
| 1 Who | `audience_line` / scene 1 |
| 2 Biggest benefit | `hook` / scene 2 |
| 3 CTA | `cta` / last scene |

Caption + hashtags go to Instagram caption.

## Update your LIVE n8n workflow

### Option A (easiest)
Import a fresh copy of `Scholarship_Reel_Automation_FFMPEG.json`.

### Option B (edit current workflow)
1. Open **AI Content**
2. Replace the **system** message with the SYSTEM section from `ai_content_prompt.txt`
3. Open **Prepare Render Body** / **Prepare FFmpeg Body**
4. Paste code from `prepare_render_body.js`
5. In Create Render body, keep `duration_seconds: 12`
6. Save and run one Pending row

You should see on-screen:
1. Who it’s for  
2. Strongest benefit  
3. CTA like “Tag a friend who needs this!”
