// ============================================================
// Instagram caption expression
// Use in IG Create Container / caption field
// ============================================================

{{
(() => {
  const ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text
    || $('AI Content').item.json;
  const caption = (ai.caption || '').toString().trim();
  const tags = Array.isArray(ai.hashtags) ? ai.hashtags.join(' ') : '';
  return [caption, tags].filter(Boolean).join('\n\n');
})()
}}
