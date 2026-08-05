// Select Random Music — put after List Music Files
const rows = (typeof $input !== 'undefined' && $input.all)
  ? $input.all()
  : (typeof items !== 'undefined' ? items : []);

const files = rows
  .map((i) => i.json || i)
  .filter((f) => {
    if (!f || !f.id) return false;
    const name = (f.name || '').toLowerCase();
    const mime = (f.mimeType || f.mime_type || '').toLowerCase();
    return (
      name.endsWith('.mp3') ||
      name.endsWith('.wav') ||
      name.endsWith('.m4a') ||
      name.endsWith('.aac') ||
      mime.includes('audio')
    );
  });

if (!files.length) {
  throw new Error(
    'No music files found in Drive Music folder. Add .mp3/.wav/.m4a files and make sure List Music Files points to the Music folder.'
  );
}

const pick = files[Math.floor(Math.random() * files.length)];
const musicUrl = `https://drive.google.com/uc?export=download&confirm=t&id=${pick.id}`;

return [{
  json: {
    musicFileId: pick.id,
    musicName: pick.name,
    musicUrl,
  },
}];
