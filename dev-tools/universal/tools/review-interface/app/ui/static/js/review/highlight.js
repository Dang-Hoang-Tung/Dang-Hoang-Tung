const SHIKI = 'https://esm.sh/shiki@4.6.0';
const SHIKI_THEMES = { light: 'github-light', dark: 'github-dark' };
let shiki;

function loadShiki() {
  shiki = shiki || Promise.all([
    import(`${SHIKI}/core`), import(`${SHIKI}/engine/javascript`),
    import(`${SHIKI}/themes/github-light`), import(`${SHIKI}/themes/github-dark`),
  ]).then(([core, engine, light, dark]) => core.createHighlighterCore({
    themes: [light.default, dark.default], langs: [], engine: engine.createJavaScriptRegexEngine(),
  })).catch(() => null);
  return shiki;
}

function changedRanges(t) {
  const ranges = [];
  let pos = 0;
  for (const n of t.childNodes) {
    const end = pos + n.textContent.length;
    if (n.nodeType === 1 && n.classList.contains('hl')) ranges.push([pos, end]);
    pos = end;
  }
  return ranges;
}

function paint(t, tokens) {
  const ranges = changedRanges(t);
  const bounds = ranges.flat();
  const frag = document.createDocumentFragment();
  let pos = 0;
  for (const tok of tokens) {
    const end = pos + tok.content.length;
    const cuts = [pos, ...bounds.filter(p => p > pos && p < end), end];
    for (let k = 0; k < cuts.length - 1; k++) {
      const changed = ranges.some(([s, e]) => cuts[k] >= s && cuts[k] < e);
      const piece = el('span', changed ? 'tk hl' : 'tk', tok.content.slice(cuts[k] - pos, cuts[k + 1] - pos));
      piece.style.cssText = Object.entries(tok.htmlStyle).map(([name, v]) => `${name}:${v}`).join(';');
      frag.append(piece);
    }
    pos = end;
  }
  t.replaceChildren(frag);
}

function highlightHunk(h, lang, rows) {
  const painted = new Map();
  for (const [kind, other] of [['add', 'del'], ['del', 'add']]) {
    const side = rows.filter(r => !r.classList.contains(other));
    const lines = side.map(r => $('.t', r).textContent);
    const { tokens } = h.codeToTokens(lines.join('\n'), { lang, themes: SHIKI_THEMES, defaultColor: false });
    side.forEach((r, i) => {
      const matches = tokens[i].map(tk => tk.content).join('') === lines[i];
      if (matches && (r.classList.contains(kind) || !painted.has(r))) painted.set(r, tokens[i]);
    });
  }
  painted.forEach((tokens, r) => paint($('.t', r), tokens));
}

async function highlightSection(s) {
  const lang = s.dataset.lang, table = $('table.diff', s);
  if (!lang || !table || s.dataset.highlighted) return;
  s.dataset.highlighted = '1';
  const h = await loadShiki();
  if (!h) return;
  try { await h.loadLanguage(import(`${SHIKI}/langs/${lang}`)); } catch (_) { return; }
  let rows = [];
  for (const r of $$('tr', table)) {
    if (!r.classList.contains('hunk') && !$('.t', r)) continue;
    if (r.classList.contains('hunk')) { if (rows.length) highlightHunk(h, lang, rows); rows = []; }
    else rows.push(r);
  }
  if (rows.length) highlightHunk(h, lang, rows);
}

function initHighlight() {
  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) return;
    io.unobserve(e.target);
    highlightSection(e.target);
  }), { rootMargin: '800px 0px' });
  $$('section.file[data-lang]').forEach(s => io.observe(s));
}
