{{
(() => {
  let raw =
    $('AI Content').item.json.output?.[0]?.content?.[0]?.text
    ?? $('AI Content').item.json.message?.content
    ?? $('AI Content').item.json.text
    ?? $('AI Content').item.json;

  if (typeof raw === 'string') {
    try { raw = JSON.parse(raw); } catch (e) { /* keep as string */ }
  }

  const ai = (raw && typeof raw === 'object') ? raw : {};
  const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : [];
  const sceneLines = scenes
    .map((s) => (s.text || '').toString().trim())
    .filter(Boolean)
    .slice(0, 3)
    .join('. ');

  const vo = (
    ai.voiceoverScript
    || ai.voiceover_script
    || ai.script
    || ai.hook
    || sceneLines
    || (ai.caption || '').toString().split('\n')[0]
    || 'Scholarship details are in the caption. Follow for more opportunities.'
  ).toString().trim();

  return vo.slice(0, 400);
})()
}}
