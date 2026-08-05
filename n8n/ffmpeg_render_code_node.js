// CODE NODE: Start FFmpeg Render (async)
const config = $('Config').item.json;
const base = String(config.ffmpeg_api_url || '').replace(/\/$/, '');
if (!base) throw new Error('Missing Config.ffmpeg_api_url');

const payload = {
  video_url: $json.video_url,
  video_urls: $json.video_urls || ($json.video_url ? [$json.video_url] : []),
  music_url: $json.music_url,
  texts: Array.isArray($json.texts) ? $json.texts : [],
  hook: $json.hook,
  script: $json.script,
  cta: $json.cta,
  duration_seconds: Number($json.duration_seconds || 15),
  music_volume: Number($json.music_volume || 0.38),
};

if (!payload.music_url) throw new Error('Missing music_url');
if (!payload.video_urls.length) throw new Error('Missing video_urls');

const headers = { 'Content-Type': 'application/json' };
if (config.ffmpeg_api_key) {
  headers.Authorization = `Bearer ${config.ffmpeg_api_key}`;
}

const result = await this.helpers.httpRequest({
  method: 'POST',
  url: `${base}/render/async`,
  headers,
  body: payload,
  json: true,
  timeout: 30000,
});

return [{
  json: {
    ...result,
    render_id: result.id,
    status: result.status || 'processing',
  },
}];
