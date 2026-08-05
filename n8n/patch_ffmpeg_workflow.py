"""Patch Scholarship_Reel_Automation_FIXED.json to use FFmpeg HD API instead of Creatomate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WF = ROOT / "Scholarship_Reel_Automation_FIXED.json"

PREPARE_JS = r"""const musicUrl = $('Select Random Music').item.json.musicUrl;
const videoUrl = $('Select Random Clip').item.json.videoUrl;

if (!musicUrl) throw new Error('No musicUrl');
if (!videoUrl) throw new Error('No videoUrl');

let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json;
if (typeof ai === 'string') {
  try { ai = JSON.parse(ai); } catch (e) { ai = {}; }
}

const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : [];
const sceneText = (n) => (scenes.find((s) => Number(s.scene) === n)?.text || '').toString().trim();
const hook = (ai.hook || sceneText(1) || ai.headline || 'Fully Funded Scholarship').toString().split('\n')[0].slice(0, 42);
const script = (ai.script || sceneText(2) || sceneText(3) || 'Applications are open').toString().split('\n')[0].slice(0, 36);
const cta = (ai.cta || 'Details in the Caption').toString().split('\n')[0].slice(0, 36);

const payload = {
  video_url: videoUrl,
  music_url: musicUrl,
  hook,
  script,
  cta,
  duration_seconds: 20,
  music_volume: 0.45,
};

return [{ json: { jsonBody: JSON.stringify(payload), ...payload } }];
"""

CREATE_RENDER_BODY = r"""={{ JSON.stringify((() => {
  const musicUrl = $('Select Random Music').item.json.musicUrl;
  const videoUrl = $('Select Random Clip').item.json.videoUrl;
  if (!musicUrl) throw new Error('No musicUrl');
  if (!videoUrl) throw new Error('No videoUrl');
  let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json;
  if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } }
  const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : [];
  const sceneText = (n) => (scenes.find((s) => Number(s.scene) === n)?.text || '').toString().trim();
  const hook = (ai.hook || sceneText(1) || ai.headline || 'Fully Funded Scholarship').toString().split('\n')[0].slice(0, 42);
  const script = (ai.script || sceneText(2) || sceneText(3) || 'Applications are open').toString().split('\n')[0].slice(0, 36);
  const cta = (ai.cta || 'Details in the Caption').toString().split('\n')[0].slice(0, 36);
  return {
    video_url: videoUrl,
    music_url: musicUrl,
    hook,
    script,
    cta,
    duration_seconds: 20,
    music_volume: 0.45,
  };
})()) }}"""


def main() -> None:
    data = json.loads(WF.read_text(encoding="utf-8"))
    data["name"] = "Scholarship Reel Automation FFmpeg HD"

    for node in data["nodes"]:
        name = node.get("name")
        if name == "Config":
            assignments = node["parameters"]["assignments"]["assignments"]
            by_name = {a.get("name"): a for a in assignments}
            ig = by_name.get("ig_user_id") or {
                "id": "ig",
                "name": "ig_user_id",
                "value": "17841475596000955",
                "type": "string",
            }
            page_token = by_name.get("page_token") or {
                "id": "tok",
                "name": "page_token",
                "value": "",
                "type": "string",
            }
            ffmpeg_url = by_name.get("ffmpeg_api_url") or by_name.get(
                "creatomate_template_id"
            )
            if ffmpeg_url:
                ffmpeg_url = {
                    "id": "ffmpeg_url",
                    "name": "ffmpeg_api_url",
                    "value": (
                        ffmpeg_url["value"]
                        if ffmpeg_url.get("name") == "ffmpeg_api_url"
                        else "https://YOUR-FFMPEG-SERVICE.up.railway.app"
                    ),
                    "type": "string",
                }
            else:
                ffmpeg_url = {
                    "id": "ffmpeg_url",
                    "name": "ffmpeg_api_url",
                    "value": "https://YOUR-FFMPEG-SERVICE.up.railway.app",
                    "type": "string",
                }
            ffmpeg_key = by_name.get("ffmpeg_api_key") or {
                "id": "ffmpeg_key",
                "name": "ffmpeg_api_key",
                "value": "",
                "type": "string",
            }
            node["parameters"]["assignments"]["assignments"] = [
                ig,
                ffmpeg_url,
                page_token,
                ffmpeg_key,
            ]

        if name == "Prepare Render Body":
            node["parameters"]["jsCode"] = PREPARE_JS

        if name == "Create Render":
            node["parameters"] = {
                "method": "POST",
                "url": "={{ ($('Config').item.json.ffmpeg_api_url || '').replace(/\\/$/, '') + '/render' }}",
                "authentication": "none",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Content-Type", "value": "application/json"},
                        {
                            "name": "Authorization",
                            "value": "={{ $('Config').item.json.ffmpeg_api_key ? 'Bearer ' + $('Config').item.json.ffmpeg_api_key : '' }}",
                        },
                    ]
                },
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": CREATE_RENDER_BODY,
                "options": {
                    "timeout": 300000,
                    "response": {
                        "response": {
                            "neverError": False,
                        }
                    },
                },
            }
            node.pop("credentials", None)
            node["retryOnFail"] = True
            node["maxTries"] = 2

        if name == "Mark Failed - Render":
            cols = node["parameters"]["columns"]["value"]
            cols["Error"] = "={{ 'FFmpeg render failed. Check Create Render response / API logs.' }}"

    # Rewire: Create Render -> IG Create Container (skip Creatomate poll)
    conns = data["connections"]
    conns["Create Render"] = {
        "main": [[{"node": "IG Create Container", "type": "main", "index": 0}]]
    }
    # Leave poll nodes disconnected (safe to delete manually in UI later)
    for dead in ("Render Wait", "Render Status", "Render Succeeded?", "Render Failed?"):
        conns.pop(dead, None)

    WF.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched {WF}")


if __name__ == "__main__":
    main()
