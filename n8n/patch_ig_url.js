const fs = require('fs');
const path = 'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_FIXED.json';
const w = JSON.parse(fs.readFileSync(path, 'utf8'));
const ig = w.nodes.find((n) => n.name === 'IG Create Container');

ig.parameters.url =
  "={{ 'https://graph.facebook.com/v21.0/' + $('Config').item.json.ig_user_id + '/media' }}";

ig.parameters.sendQuery = true;
ig.parameters.queryParameters = {
  parameters: [
    {
      name: 'access_token',
      value: "={{ $('Config').item.json.page_token }}",
    },
  ],
};

ig.parameters.sendBody = true;
ig.parameters.specifyBody = 'json';
ig.parameters.jsonBody =
  "={{ JSON.stringify((() => { let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json; if (typeof ai === 'string') { try { ai = JSON.parse(ai); } catch (e) { ai = {}; } } const caption = (ai.caption || ai.hook || 'New scholarship opportunity').toString().trim(); const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : ''; const fullCaption = [caption, tags].filter(Boolean).join('\\n\\n'); const videoUrl = $json.url || $('Render Status').item.json.url; if (!videoUrl) throw new Error('Missing video url'); return { media_type: 'REELS', video_url: videoUrl, caption: fullCaption }; })()) }}";

fs.writeFileSync(path, JSON.stringify(w, null, 2));
fs.copyFileSync(path, 'C:/Users/HP/Downloads/Scholarship_Reel_Automation_FIXED.json');
console.log('URL:', ig.parameters.url);
console.log('DONE');
