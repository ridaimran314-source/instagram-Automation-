const fs = require('fs');

const path =
  'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_FIXED.json';
const w = JSON.parse(fs.readFileSync(path, 'utf8'));

const ig = w.nodes.find((n) => n.name === 'IG Create Container');
if (!ig) throw new Error('IG Create Container missing');

// Hardcoded URL avoids the =https / {{ literal }} bugs in the UI
ig.parameters = {
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
  specifyBody: 'json',
  jsonBody:
    "={{ JSON.stringify((() => { let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json; if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } } const caption = (ai.caption || ai.hook || 'New scholarship opportunity').toString().trim(); const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : ''; const fullCaption = [caption, tags].filter(Boolean).join('\\n\\n'); const videoUrl = $json.url || $('Render Status').item.json.url; if (!videoUrl) throw new Error('Missing video url'); return { media_type: 'REELS', video_url: videoUrl, caption: fullCaption }; })()) }}",
  options: {},
};

// Ensure Create Render stays correct
const create = w.nodes.find((n) => n.name === 'Create Render');
if (create) {
  create.parameters.method = 'POST';
  create.parameters.url = 'https://api.creatomate.com/v2/renders';
  create.parameters.sendHeaders = true;
  create.parameters.headerParameters = {
    parameters: [{ name: 'Content-Type', value: 'application/json' }],
  };
  create.parameters.sendBody = true;
  create.parameters.contentType = 'raw';
  create.parameters.rawContentType = 'text/plain';
  create.parameters.body = '={{ $json.jsonBody }}';
}

const prepare = w.nodes.find((n) => n.name === 'Prepare Render Body');
if (prepare && !prepare.parameters.jsCode.includes('jsonBody')) {
  // leave as-is if already patched
}

fs.writeFileSync(path, JSON.stringify(w, null, 2));
fs.copyFileSync(
  path,
  'C:/Users/HP/Downloads/Scholarship_Reel_Automation_FIXED.json'
);

console.log('IG URL:', ig.parameters.url);
console.log('IG has access_token:', ig.parameters.queryParameters.parameters[0].name);
console.log('IG specifyBody:', ig.parameters.specifyBody);
console.log('COPIED_TO_DOWNLOADS');
