// CODE NODE: Check Render Status
// After Wait → IF ready? true→IG / false→Wait again

const config = $('Config').item.json;
const base = String(config.ffmpeg_api_url || '').replace(/\/$/, '');
const renderId = $json.render_id || $json.id;
if (!renderId) throw new Error('Missing render_id');
if (!base) throw new Error('Missing Config.ffmpeg_api_url');

const headers = {};
if (config.ffmpeg_api_key) {
  headers.Authorization = `Bearer ${config.ffmpeg_api_key}`;
}

const result = await this.helpers.httpRequest({
  method: 'GET',
  url: `${base}/render/${renderId}`,
  headers,
  json: true,
  timeout: 30000,
});

const body = (result && result.data && typeof result.data === 'object')
  ? result.data
  : result;

const status = String(body.status || '').toLowerCase();
const mp4Url = `${base}/files/${renderId}.mp4`;
let url = body.url || null;

if (status === 'failed') {
  throw new Error(body.error || 'Render failed on server');
}

// Ready when succeeded OR when URL is already a downloadable mp4
let ready = status === 'succeeded' || (!!url && String(url).includes('.mp4'));
if (ready) {
  if (!url || !String(url).includes('.mp4')) url = mp4Url;
}

if (!ready && status === 'processing') {
  const started = Date.parse(body.started_at || $json.started_at || '');
  if (!Number.isNaN(started) && Date.now() - started > 6 * 60 * 1000) {
    throw new Error(
      `Render stuck processing >6m (id=${renderId}). Open ${mp4Url} — if it plays, Railway is done but status is stale. Redeploy ffmpeg-render.`
    );
  }
}

return [{
  json: {
    id: renderId,
    render_id: renderId,
    status: ready ? 'succeeded' : status,
    url: ready ? url : url,
    width: body.width || 1080,
    height: body.height || 1920,
    error: body.error || null,
    started_at: body.started_at || null,
    ready: !!ready,
    // helpful for IF debugging
    api_status: status,
    api_url: body.url || null,
  },
}];
