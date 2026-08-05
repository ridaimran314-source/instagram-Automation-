const fs = require('fs');

const path = 'C:/Users/HP/OneDrive/Desktop/insta automation/n8n/Scholarship_Reel_Automation_FIXED.json';
const w = JSON.parse(fs.readFileSync(path, 'utf8'));

const expr = `={{ (() => {
  let ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json;
  if (typeof ai === 'string') {
    try { ai = JSON.parse(ai); } catch (e) { ai = {}; }
  }
  const caption = (ai.caption || ai.hook || 'New scholarship opportunity').toString().trim();
  const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : '';
  const fullCaption = [caption, tags].filter(Boolean).join('\\n\\n');
  const videoUrl = $('Render Status').item.json.url;
  if (!videoUrl) throw new Error('Render Status missing url');
  return {
    media_type: 'REELS',
    video_url: videoUrl,
    caption: fullCaption
  };
})() }}`;

const ig = w.nodes.find((n) => n.name === 'IG Create Container');
if (!ig) throw new Error('IG Create Container not found');
ig.parameters.jsonBody = expr;

fs.writeFileSync(path, JSON.stringify(w, null, 2));
fs.copyFileSync(path, 'C:/Users/HP/Downloads/Scholarship_Reel_Automation_FIXED.json');
console.log('IG_CREATE_CONTAINER_FIXED');
