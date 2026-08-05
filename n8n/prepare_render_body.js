function pickMusicUrl() {
  const candidates = [];
  const pushMusic = (obj) => {
    if (!obj || typeof obj !== 'object') return;
    // Ignore clip payloads wrongly placed in the music node
    if (obj.hasVideo || obj.videoUrls || obj.videoUrl) return;
    const u = obj.musicUrl || obj.music_url;
    if (u && String(u).includes('http')) candidates.push(String(u).trim());
  };

  pushMusic($json);
  try { pushMusic($('Select Random Music').item.json); } catch (e) {}
  try { pushMusic($('Select Random Music').first().json); } catch (e) {}

  try {
    for (const item of $('Select Random Music').all()) pushMusic(item.json);
  } catch (e) {}

  if (candidates.length) return candidates[0];

  // Fallback: pick directly from List Music Files (if Select Random Music has wrong code)
  try {
    const files = $('List Music Files').all()
      .map((i) => i.json || {})
      .filter((f) => {
        if (!f.id) return false;
        const name = String(f.name || '').toLowerCase();
        const mime = String(f.mimeType || f.mime_type || '').toLowerCase();
        return (
          name.endsWith('.mp3') ||
          name.endsWith('.wav') ||
          name.endsWith('.m4a') ||
          name.endsWith('.aac') ||
          mime.includes('audio')
        );
      });
    if (files.length) {
      const pick = files[Math.floor(Math.random() * files.length)];
      return `https://drive.google.com/uc?export=download&confirm=t&id=${pick.id}`;
    }
  } catch (e) {}

  return '';
}

const musicUrl = pickMusicUrl();

const clipNode = $('Select Random Clip').item.json;

// Parse AI first — caption is the source of truth for which scholarship this run is
let ai = {};
try {
  ai = $('AI Content').item.json.output?.[0]?.content?.[0]?.text || $('AI Content').item.json;
  if (typeof ai === 'string') {
    try { ai = JSON.parse(ai); } catch (e) { ai = {}; }
  }
} catch (e) { ai = {}; }
if (!ai || typeof ai !== 'object') ai = {};

const aiBlob = [
  ai.caption, ai.hook, ai.headline, ai.university_line,
  ai.field_line, ai.cta,
  ...(Array.isArray(ai.video_scenes) ? ai.video_scenes.map((s) => s.text) : []),
].filter(Boolean).join(' ');

/** Detect country from AI caption/hook (never trust Get Pending first row) */
function detectCountryFromAi(text) {
  const t = String(text || '').toLowerCase();
  const rules = [
    { re: /qatar|doha|lusail/, country: 'Qatar' },
    { re: /australia|monash|melbourne|sydney/, country: 'Australia' },
    { re: /united kingdom|\buk\b|britain|bristol|london|england/, country: 'United Kingdom' },
    { re: /united states|\busa\b|\bus\b|america/, country: 'United States' },
    { re: /germany|berlin|munich|daad/, country: 'Germany' },
    { re: /canada|toronto|vancouver/, country: 'Canada' },
    { re: /france|paris/, country: 'France' },
    { re: /netherlands|holland|delft/, country: 'Netherlands' },
    { re: /china|beijing|shanghai/, country: 'China' },
    { re: /japan|tokyo/, country: 'Japan' },
    { re: /uae|dubai|abu dhabi/, country: 'United Arab Emirates' },
  ];
  for (const r of rules) {
    if (r.re.test(t)) return r.country;
  }
  return '';
}

function getSheetRow() {
  const aiCountry = detectCountryFromAi(aiBlob);

  // 1) Filter Pending — the row currently being processed
  for (const name of ['Filter Pending', 'Pending Row']) {
    try {
      const rows = $(name).all().map((i) => i.json).filter((r) => r && (r['Host Country'] || r['Scholarship Name']));
      if (rows.length === 1) return rows[0];
      if (rows.length > 1 && aiCountry) {
        const match = rows.find((r) => String(r['Host Country'] || '').toLowerCase().includes(aiCountry.toLowerCase().replace(/^the\s+/, '')));
        if (match) return match;
      }
      if (rows.length) return rows[0];
    } catch (e) {}
  }

  // 2) Match among ALL sheet rows using AI country / university — NEVER default to index 0 blindly
  let all = [];
  try {
    all = $('Get Pending Scholarship').all().map((i) => i.json).filter(Boolean);
  } catch (e) {}

  if (aiCountry && all.length) {
    const key = aiCountry.toLowerCase();
    const match2 = all.find((r) => {
      const c = String(r['Host Country'] || '').toLowerCase();
      if (key === 'united kingdom') return c.includes('united kingdom') || c === 'uk';
      if (key === 'united states') return c.includes('united states') || c === 'usa' || c === 'us';
      return c.includes(key);
    });
    if (match2) return match2;
  }

  // 3) Match by university name in AI text
  if (all.length) {
    for (const r of all) {
      const uni = String(r['University'] || r['Scholarship Name'] || '').trim();
      if (uni.length > 4 && aiBlob.toLowerCase().includes(uni.toLowerCase().slice(0, Math.min(12, uni.length)))) {
        return r;
      }
    }
  }

  // 4) Pending-only rows
  const pending = all.filter((r) => String(r.Status || '').toLowerCase() === 'pending');
  if (pending.length === 1) return pending[0];
  if (pending.length > 1 && aiCountry) {
    const m = pending.find((r) => String(r['Host Country'] || '').toLowerCase().includes(aiCountry.toLowerCase()));
    if (m) return m;
  }

  // 5) Last resort: synthetic row from AI country (avoids Germany default)
  if (aiCountry) {
    return {
      'Host Country': aiCountry,
      'University': (ai.university_line || '').replace(/^study at\s+/i, ''),
      'Degree Type': ai.audience_line || '',
      'Field of Study': (ai.field_line || '').replace(/^field:\s*/i, ''),
      'Deadline': '',
      'Scholarship Type': '',
      Status: 'Pending',
    };
  }

  throw new Error(
    'Could not resolve scholarship row. Fix Country Folder / Filter Pending to use $json["Host Country"], not Get Pending Scholarship.item (that always picks Germany).'
  );
}

const sheet = getSheetRow();
const aiCountryDetected = detectCountryFromAi(aiBlob);

const videoUrls = Array.isArray(clipNode.videoUrls) && clipNode.videoUrls.length
  ? clipNode.videoUrls
  : (clipNode.videoUrl ? [clipNode.videoUrl] : []);

if (!musicUrl) {
  let musicDebug = {};
  try { musicDebug = $('Select Random Music').item.json || {}; } catch (e) {
    musicDebug = { error: 'Node "Select Random Music" not found or not executed' };
  }
  const looksLikeClips = !!(musicDebug.hasVideo || musicDebug.videoUrls);
  throw new Error(
    looksLikeClips
      ? 'Select Random Music has CLIP code (hasVideo/videoUrls). Open that node and paste select_random_music.js instead.'
      : 'No musicUrl. Paste select_random_music.js into Select Random Music, and point List Music Files at the Music folder with .mp3 files. ' +
        `Got keys: ${Object.keys(musicDebug).join(', ') || '(empty)'}`
  );
}
if (!videoUrls.length) throw new Error('No videoUrls');

// ai already parsed above
const scenes = Array.isArray(ai.video_scenes) ? ai.video_scenes : [];
const sceneText = (n) => (scenes.find((s) => Number(s.scene) === n)?.text || '').toString().trim();

const clean = (v, max) => (v || '').toString().replace(/\s+/g, ' ').trim().slice(0, max);
const dangling = new Set(['a','an','the','in','on','at','to','for','of','and','or','with','from']);

const COUNTRY_SHORT = {
  'united kingdom': 'the UK',
  'uk': 'the UK',
  'great britain': 'the UK',
  'england': 'the UK',
  'united states': 'the USA',
  'united states of america': 'the USA',
  'usa': 'the USA',
  'us': 'the USA',
  'u.s.': 'the USA',
  'u.s.a.': 'the USA',
  'united arab emirates': 'the UAE',
  'uae': 'the UAE',
  'saudi arabia': 'Saudi Arabia',
  'south korea': 'South Korea',
  'germany': 'Germany',
  'canada': 'Canada',
  'australia': 'Australia',
  'qatar': 'Qatar',
  'france': 'France',
  'italy': 'Italy',
  'netherlands': 'the Netherlands',
  'china': 'China',
  'japan': 'Japan',
};

const shortCountry = (raw) => {
  const t = clean(raw, 40);
  if (!t) return '';
  const mapped = COUNTRY_SHORT[t.toLowerCase()];
  if (mapped) return mapped;
  // keep short names as-is; prefix "the" only when mapped
  return t;
};

const completeLine = (v, max = 48) => {
  let t = clean(v, max + 12);
  if (!t) return '';
  if (t.length > max) {
    t = t.slice(0, max + 1);
    if (t.includes(' ')) t = t.slice(0, t.lastIndexOf(' '));
  }
  let words = t.split(/\s+/).filter(Boolean);
  while (words.length && dangling.has(words[words.length - 1].toLowerCase().replace(/[.,!?]/g, ''))) {
    words.pop();
  }
  return balanceBrackets(words.join(' '));
};

/** Fix cut-off parentheses: "Arts (School of Music limited" → "Arts" or add ")" */
function balanceBrackets(text) {
  let t = String(text || '').replace(/\s+/g, ' ').trim();
  if (!t) return '';

  const opens = (t.match(/\(/g) || []).length;
  const closes = (t.match(/\)/g) || []).length;

  // Unclosed "(" — drop incomplete parenthetical (cleaner on Reels)
  if (opens > closes) {
    const idx = t.indexOf('(');
    if (idx > 0) {
      const before = t.slice(0, idx).trim();
      if (before.length >= 3) return before.replace(/[,\-–—:]+$/g, '').trim();
    }
    // Only parenthetical left — close it if short enough
    if (t.length <= 40) return `${t})`;
    return t.replace(/\([^)]*$/g, '').trim();
  }

  // Extra ")" without "(" — strip trailing orphans
  if (closes > opens) {
    while ((t.match(/\)/g) || []).length > (t.match(/\(/g) || []).length) {
      t = t.replace(/\)([^)]*)$/, '$1').trim();
    }
  }

  return t;
}

/** Prefer short field name; keep commas if the phrase stays short */
function shortFieldName(raw) {
  let t = clean(raw, 80);
  if (!t) return '';
  // Keep short comma lists: "Arts, Music" / "Business & Law"
  if (t.length <= 34 && /[,&]/.test(t) && !/\(/.test(t)) {
    return balanceBrackets(completeLine(t, 34));
  }
  // Long text: take main label (before / or |, and before long parenthetical)
  t = (t.split(/[/|]/)[0] || t).trim();
  if (t.includes(',') && t.length > 34) {
    t = t.split(',')[0].trim();
  }
  const paren = t.indexOf('(');
  if (paren > 0 && t.length > 28) {
    t = t.slice(0, paren).trim();
  }
  t = completeLine(t, 28);
  return balanceBrackets(t);
}

/** Turn short sheet values into full on-screen phrases */
const enrichLine = (line) => {
  let t = completeLine(line, 52);
  if (!t) return '';
  const low = t.toLowerCase();

  // Ban tiny/incomplete slides
  if (t.split(/\s+/).length <= 1) {
    if (/master/.test(low)) return "Master's Degree Programs";
    if (/bachelor|undergrad/.test(low)) return "Bachelor's Degree Programs";
    if (/phd|doctoral|doctorate/.test(low)) return 'PhD Programs Available';
    if (/funded/.test(low)) return 'Fully Funded Scholarships';
    return '';
  }

  if (/^(masters?|master'?s)$/i.test(t)) return "Master's Degree Programs";
  if (/^(bachelors?|bachelor'?s)$/i.test(t)) return "Bachelor's Degree Programs";
  if (/^(phd|ph\.d\.?)$/i.test(t)) return 'PhD Programs Available';

  // Incomplete "in the" / "in" endings already stripped by completeLine
  if (/\bin the$/i.test(t) || /\bin$/i.test(t)) return '';

  return t;
};

const countryShort = shortCountry(
  aiCountryDetected || sheet['Host Country'] || ''
);
const university = enrichLine(sheet['University'] || ai.university_line || '');
const degreeRaw = clean(sheet['Degree Type'] || ai.audience_line || '', 40);
const fieldShort = shortFieldName(sheet['Field of Study'] || '');
const deadline = completeLine(sheet['Deadline'] || '', 28);

const degreeWord = (() => {
  if (/master/i.test(degreeRaw) && /phd|ph\.?d/i.test(degreeRaw)) return "Master's & PhD";
  if (/master/i.test(degreeRaw)) return "Master's";
  if (/bachelor/i.test(degreeRaw)) return "Bachelor's";
  if (/phd|ph\.?d/i.test(degreeRaw)) return 'PhD';
  return '';
})();

// ONE complete phrase per slide — combine degree + field when both exist
let degreeFieldLine = '';
if (degreeWord && fieldShort) {
  degreeFieldLine = balanceBrackets(`${degreeWord} in ${fieldShort}`);
} else if (fieldShort) {
  degreeFieldLine = balanceBrackets(`Field: ${fieldShort}`);
} else if (degreeWord) {
  degreeFieldLine = `${degreeWord} Degree Programs`;
}

// Headline ALWAYS follows AI caption country (fixes "always Germany" bug)
const countryLabel = countryShort || shortCountry(aiCountryDetected) || 'Abroad';
const headline = countryLabel && countryLabel !== 'Abroad'
  ? `Fully Funded Scholarships in ${countryLabel}`
  : 'Fully Funded Scholarships Abroad';

const benefitRaw = clean(sheet['Scholarship Type'] || sceneText(5) || '', 40);
let benefitLine = '';
if (benefitRaw && !/fully funded/i.test(benefitRaw)) {
  benefitLine = enrichLine(benefitRaw);
  if (benefitLine && benefitLine.split(/\s+/).length <= 2 && !/ielts|stipend|tuition|fee/i.test(benefitLine)) {
    benefitLine = completeLine(`${benefitLine} Included`, 40) || benefitLine;
  }
}

const deadlineLine = deadline ? `Deadline: ${deadline}` : '';
let cta = enrichLine(ai.cta || sceneText(7) || sceneText(6) || 'Apply Now') || 'Apply Now';
cta = balanceBrackets(cta);
// Prefer a clear CTA with exclamation when it's an action line
if (/^(apply now|tag a friend|save this|follow for more)/i.test(cta) && !/[!]$/.test(cta)) {
  cta = `${cta.replace(/[.]+$/g, '')}!`;
}

const uniLine = university
  ? (university.split(/\s+/).length <= 3 ? `Study at ${university}` : university)
  : '';

// Each item is one full on-screen phrase
const structured = [headline];
if (uniLine) structured.push(uniLine);
if (degreeFieldLine) structured.push(degreeFieldLine);
if (benefitLine) structured.push(benefitLine);
if (deadlineLine) structured.push(deadlineLine);
structured.push(cta);

const fromScenes = scenes
  .map((s) => enrichLine(s.text))
  .filter((t) => t && t.split(/\s+/).length >= 2);

const texts = [];
const seen = new Set();
for (const line of [...structured, ...fromScenes]) {
  const fixed = balanceBrackets(line);
  const key = (fixed || '').toLowerCase();
  if (!fixed || seen.has(key)) continue;
  if (dangling.has(key.split(/\s+/).pop())) continue;
  if (fixed.split(/\s+/).length < 2 && !/^apply now$/i.test(fixed)) continue;
  // Skip lines that still have unclosed brackets
  if ((fixed.match(/\(/g) || []).length !== (fixed.match(/\)/g) || []).length) continue;
  seen.add(key);
  texts.push(fixed);
  if (texts.length >= 8) break;
}

// Ensure slide 1 is always the full funded+country line
if (texts[0] !== headline) {
  texts.unshift(headline);
  while (texts.length > 8) texts.pop();
}
while (texts.length < 3) texts.push('Follow for more scholarships!');

const uniqueUrls = [];
for (const u of videoUrls) {
  if (u && !uniqueUrls.includes(u)) uniqueUrls.push(u);
}
while (uniqueUrls.length < texts.length && videoUrls.length) {
  uniqueUrls.push(videoUrls[uniqueUrls.length % videoUrls.length]);
}

const hook = texts[0];
const script = texts[Math.min(1, texts.length - 1)];
const ctaOut = texts[texts.length - 1];
const bio = clean(ai.bio || ai.profile_bio || '', 150);

const payload = {
  video_url: uniqueUrls[0],
  video_urls: uniqueUrls.slice(0, texts.length),
  music_url: musicUrl,
  texts,
  hook,
  script,
  cta: ctaOut,
  // ~2.1s per beat so clips / text change often
  duration_seconds: Math.min(17, Math.max(12, Math.round(texts.length * 2.1))),
  music_volume: 0.38,
};

return [{
  json: {
    ...payload,
    video_urls_text: payload.video_urls.join('\n'),
    render_body: JSON.stringify(payload),
    profile_bio: bio,
    caption: (ai.caption || '').toString().trim(),
    hashtags: Array.isArray(ai.hashtags) ? ai.hashtags : [],
    field_of_study: fieldShort,
    country_short: countryLabel,
    host_country_resolved: sheet['Host Country'] || aiCountryDetected || '',
    ai_country_detected: aiCountryDetected || '',
  },
}];
