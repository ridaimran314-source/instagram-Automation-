const fs = require('fs');

const src =
  'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_WORKING.json';
const w = JSON.parse(fs.readFileSync(src, 'utf8'));

const prepareCode = `const musicUrl = $('Select Random Music').item.json.musicUrl;
const videoUrl = $('Select Random Clip').item.json.videoUrl;

if (!musicUrl) throw new Error('No musicUrl');
if (!videoUrl) throw new Error('No videoUrl');

let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json;
if (typeof ai === 'string') {
  try { ai = JSON.parse(ai); } catch (e) { ai = {}; }
}

const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : [];
const sceneText = (n) => (scenes.find((s) => Number(s.scene) === n)?.text || '').toString().trim();
const hook = (ai.hook || sceneText(1) || ai.headline || 'Fully Funded Scholarship').toString().split('\\n')[0].slice(0, 42);
const script = (ai.script || sceneText(2) || sceneText(3) || 'Applications are open').toString().split('\\n')[0].slice(0, 36);
const cta = (ai.cta || 'Details in the Caption').toString();

const payload = {
  template_id: '0317527d-292d-45cb-944d-dbe35e8592b4',
  render_scale: 1,
  modifications: {
    'Video-1.source': videoUrl,
    'Video-1.volume': '0%',
    Hook: hook,
    Script: script,
    CTA: cta,
    'Voiceover.volume': '0%',
    'Music.source': musicUrl,
    'Music.volume': '45%',
  },
};

return [{ json: { jsonBody: JSON.stringify(payload) } }];
`;

const captionExpr =
  "={{ (() => { let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json; if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } } const caption = (ai.caption || ai.hook || 'New scholarship opportunity').toString().trim(); const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : ''; return [caption, tags].filter(Boolean).join('\\n\\n'); })() }}";

for (const n of w.nodes) {
  if (n.name === 'Prepare Render Body') {
    n.parameters.jsCode = prepareCode;
  }

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
      body: '={{ $json.jsonBody }}',
      options: {},
    };
  }

  if (n.name === 'Render Status') {
    n.parameters.url =
      "={{ 'https://api.creatomate.com/v2/renders/' + $('Create Render').item.json.id }}";
  }

  if (n.name === 'IG Create Container') {
    // Plain URL (no expression) + form fields + access_token query
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
      sendHeaders: false,
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

  if (n.name === 'Select Random Music' && n.parameters.jsCode) {
    n.parameters.jsCode = n.parameters.jsCode.replace(
      'https://drive.google.com/uc?export=download&id=${pick.id}',
      'https://drive.google.com/uc?export=download&confirm=t&id=${pick.id}'
    );
  }
}

const outDir = 'C:/Users/HP/OneDrive/Desktop/insta automation/n8n';
const out1 = `${outDir}/Scholarship_Reel_Automation_FIXED.json`;
const out2 = 'C:/Users/HP/Downloads/Scholarship_Reel_Automation_FIXED.json';
fs.writeFileSync(out1, JSON.stringify(w, null, 2));
fs.copyFileSync(out1, out2);

const ig = w.nodes.find((n) => n.name === 'IG Create Container');
const cr = w.nodes.find((n) => n.name === 'Create Render');
console.log('FIXED');
console.log('IG url:', ig.parameters.url);
console.log('IG access_token:', ig.parameters.queryParameters.parameters[0].name);
console.log('IG body fields:', ig.parameters.bodyParameters.parameters.map((p) => p.name).join(','));
console.log('Create Render body:', cr.parameters.body);
console.log('Wrote:', out2);
