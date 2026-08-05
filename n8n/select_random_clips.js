const clips = $input.all().filter((i) => i.json && i.json.id);
if (clips.length === 0) {
  return [{ json: { hasVideo: false } }];
}

const shuffled = clips
  .map((c) => c.json)
  .sort(() => Math.random() - 0.5);

const unique = [];
const seen = new Set();
for (const clip of shuffled) {
  if (seen.has(clip.id)) continue;
  seen.add(clip.id);
  unique.push(clip);
  if (unique.length >= 8) break;
}

// Up to 8 clips — change background with almost every text beat
const target = Math.max(4, Math.min(8, unique.length || 4));
const picks = [];
while (picks.length < target) {
  picks.push(unique[picks.length % unique.length]);
}

const videoUrls = picks.map(
  (p) => `https://drive.google.com/uc?export=download&confirm=t&id=${p.id}`
);

return [{
  json: {
    hasVideo: true,
    videoUrl: videoUrls[0],
    videoUrls,
    fileIds: picks.map((p) => p.id),
    fileNames: picks.map((p) => p.name),
    clipCount: unique.length,
    uniqueClipCount: unique.length,
    needsMoreClips: unique.length < 3,
  },
}];
