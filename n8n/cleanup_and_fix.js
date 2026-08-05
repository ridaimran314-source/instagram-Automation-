const fs = require('fs');

const path =
  'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_FIXED.json';
const w = JSON.parse(fs.readFileSync(path, 'utf8'));

// Remove duplicated import nodes (names ending in 1)
const removeNames = new Set(
  w.nodes.filter((n) => /\d+$/.test(n.name) && n.name !== 'OpenAI Chat Model').map((n) => n.name)
);
// Only remove clear duplicates like Foo1, Foo2 from import merges
const dupes = w.nodes.filter((n) => /^.+1$/.test(n.name) || /^.+2$/.test(n.name));
const dupeNames = new Set(dupes.map((n) => n.name));

w.nodes = w.nodes.filter((n) => !dupeNames.has(n.name));

for (const key of Object.keys(w.connections)) {
  if (dupeNames.has(key)) {
    delete w.connections[key];
    continue;
  }
  const conn = w.connections[key];
  if (!conn || !conn.main) continue;
  conn.main = conn.main.map((outputs) =>
    (outputs || []).filter((c) => !dupeNames.has(c.node))
  );
}

const createBodyExpr =
  "={{ JSON.stringify((() => { const musicUrl = $('Select Random Music').item.json.musicUrl; const videoUrl = $('Select Random Clip').item.json.videoUrl; if (!musicUrl) throw new Error('No musicUrl'); if (!videoUrl) throw new Error('No videoUrl'); let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json; if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } } const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : []; const sceneText = (n) => (scenes.find((s) => Number(s.scene) === n)?.text || '').toString().trim(); const hook = (ai.hook || sceneText(1) || ai.headline || 'Fully Funded Scholarship').toString().split('\\n')[0].slice(0, 42); const script = (ai.script || sceneText(2) || sceneText(3) || 'Applications are open').toString().split('\\n')[0].slice(0, 36); const cta = (ai.cta || 'Details in the Caption').toString(); return { template_id: '0317527d-292d-45cb-944d-dbe35e8592b4', render_scale: 1, modifications: { 'Video-1.source': videoUrl, 'Video-1.volume': '0%', Hook: hook, Script: script, CTA: cta, 'Voiceover.volume': '0%', 'Music.source': musicUrl, 'Music.volume': '45%' } }; })()) }}";

const captionExpr =
  "={{ (() => { let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json; if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } } const caption = (ai.caption || ai.hook || 'New scholarship opportunity').toString().trim(); const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : ''; return [caption, tags].filter(Boolean).join('\\n\\n'); })() }}";

for (const n of w.nodes) {
  if (n.name === 'Create Render') {
    n.parameters = {
      method: 'POST',
      url: 'https://api.creatomate.com/v2/renders',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendHeaders: true,
      headerParameters: {
        parameters: [{ name: 'Content-Type', value: 'application/json' }],
      },
      sendBody: true,
      contentType: 'raw',
      rawContentType: 'text/plain',
      body: createBodyExpr,
      options: {},
    };
  }

  if (n.name === 'Render Status') {
    n.parameters.url =
      "={{ 'https://api.creatomate.com/v2/renders/' + $('Create Render').item.json.id }}";
  }

  if (n.name === 'IG Create Container') {
    n.parameters = {
      method: 'POST',
      url: 'https://graph.facebook.com/v21.0/17841475596000955/media',
      authentication: 'none',
      sendQuery: true,
      queryParameters: {
        parameters: [
          {
            name: 'access_token',
            value: "={{ $('Config').item.json.page_token }}",
          },
        ],
      },
      sendBody: true,
      contentType: 'form-urlencoded',
      bodyParameters: {
        parameters: [
          { name: 'media_type', value: 'REELS' },
          { name: 'video_url', value: '={{ $json.url }}' },
          { name: 'caption', value: captionExpr },
        ],
      },
      options: {},
    };
  }
}

// Ensure name is clear for new import
w.name = 'Scholarship Reel Automation CLEAN';

fs.writeFileSync(path, JSON.stringify(w, null, 2));
fs.copyFileSync(path, 'C:/Users/HP/Downloads/Scholarship_Reel_Automation_CLEAN.json');

console.log('nodes after cleanup:', w.nodes.length);
console.log(
  'dupes left:',
  w.nodes.filter((n) => /1$|2$/.test(n.name)).map((n) => n.name)
);
console.log('Create Render body starts:', w.nodes.find((n) => n.name === 'Create Render').parameters.body.slice(0, 40));
console.log('Wrote Downloads/Scholarship_Reel_Automation_CLEAN.json');
