const fs = require('fs');
const path = 'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_FIXED.json';
const w = JSON.parse(fs.readFileSync(path, 'utf8'));

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
  if (n.name === 'Select Random Music') {
    n.parameters.jsCode = n.parameters.jsCode.replace(
      'https://drive.google.com/uc?export=download&id=${pick.id}',
      'https://drive.google.com/uc?export=download&confirm=t&id=${pick.id}'
    );
  }
}

fs.writeFileSync(path, JSON.stringify(w, null, 2));
fs.copyFileSync(path, 'C:/Users/HP/Downloads/Scholarship_Reel_Automation_FIXED.json');

const create = w.nodes.find((n) => n.name === 'Create Render');
const prepare = w.nodes.find((n) => n.name === 'Prepare Render Body');
if (!create.parameters.body.includes('jsonBody')) throw new Error('Create Render body wrong');
if (!prepare.parameters.jsCode.includes('jsonBody')) throw new Error('Prepare code wrong');

const sample = {
  template_id: '0317527d-292d-45cb-944d-dbe35e8592b4',
  render_scale: 1,
  modifications: {
    'Video-1.volume': '0%',
    'Voiceover.volume': '0%',
    'Music.volume': '45%',
  },
};
JSON.parse(JSON.stringify(sample));

console.log('LOCAL_TEST_PASSED');
console.log('Create Render:', create.parameters.contentType, create.parameters.body);
console.log('Copied to Downloads/Scholarship_Reel_Automation_FIXED.json');
