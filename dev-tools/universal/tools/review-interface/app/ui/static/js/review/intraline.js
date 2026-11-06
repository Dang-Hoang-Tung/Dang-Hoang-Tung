// Word-level highlights inside changed lines, using jsdiff (Diff.diffArrays) when it loaded.
const REWRITE_SHARE = 0.6;
const MAX_BLOCK_LINES = 300;
const isSpace = t => /^[^\S\n]+$/.test(t);
const tokenize = s => s.match(/\n|[^\S\n]+|\w+|[^\s\w]/g) || [];
const sameToken = (a, b) => a === b || (isSpace(a) && isSpace(b));

function lineRanges(tokens, changed, lineCount) {
  const out = Array.from({ length: lineCount }, () => []);
  let line = 0, col = 0;
  tokens.forEach((t, i) => {
    if (t === '\n') { line++; col = 0; return; }
    if (changed[i] && !isSpace(t)) {
      const last = out[line][out[line].length - 1];
      if (last && last[1] === col) last[1] = col + t.length; else out[line].push([col, col + t.length]);
    }
    col += t.length;
  });
  return out;
}

function blockSpans(oldLines, newLines) {
  const a = tokenize(oldLines.join('\n')), b = tokenize(newLines.join('\n'));
  const oldChanged = new Array(a.length).fill(false), newChanged = new Array(b.length).fill(false);
  let i = 0, j = 0;
  for (const part of Diff.diffArrays(a, b, { comparator: sameToken })) {
    if (part.added) { for (let k = 0; k < part.count; k++) newChanged[j++] = true; }
    else if (part.removed) { for (let k = 0; k < part.count; k++) oldChanged[i++] = true; }
    else { i += part.count; j += part.count; }
  }
  const weight = (tokens, flags) => tokens.reduce((s, t, k) => (isSpace(t) || t === '\n' ? s : [s[0] + t.length, s[1] + (flags[k] ? t.length : 0)]), [0, 0]);
  const [oldAll, oldDiff] = weight(a, oldChanged), [newAll, newDiff] = weight(b, newChanged);
  if ((oldDiff + newDiff) / Math.max(1, oldAll + newAll) > REWRITE_SHARE) return null;
  return { old: lineRanges(a, oldChanged, oldLines.length), new: lineRanges(b, newChanged, newLines.length) };
}

function plainText(row) {
  const t = $('.t', row);
  const node = t && t.childNodes.length === 1 ? t.firstChild : null;
  return node && node.nodeType === Node.TEXT_NODE ? node : null;
}

function paintLine(row, ranges) {
  if (!ranges.length) return;
  const node = plainText(row);
  if (!node) return;
  const text = node.textContent, frag = document.createDocumentFragment();
  let pos = 0;
  for (const [s, e] of ranges) {
    if (s > pos) frag.append(text.slice(pos, s));
    frag.append(el('span', 'hl', text.slice(s, e)));
    pos = e;
  }
  if (pos < text.length) frag.append(text.slice(pos));
  node.replaceWith(frag);
}

const plain = (r, kind) => r.classList.contains(kind) && !r.classList.contains('moved');

function highlightTable(table) {
  if (table.dataset.spans === 'difft') return;
  const rows = [...table.rows];
  for (let i = 0; i < rows.length;) {
    if (!plain(rows[i], 'del')) { i++; continue; }
    const dels = [], adds = [];
    while (i < rows.length && plain(rows[i], 'del')) dels.push(rows[i++]);
    while (i < rows.length && plain(rows[i], 'add')) adds.push(rows[i++]);
    if (!adds.length || dels.length + adds.length > MAX_BLOCK_LINES) continue;
    const text = r => { const n = plainText(r); return n ? n.textContent : ''; };
    const spans = blockSpans(dels.map(text), adds.map(text));
    if (!spans) continue;
    dels.forEach((r, k) => paintLine(r, spans.old[k]));
    adds.forEach((r, k) => paintLine(r, spans.new[k]));
  }
}

function initIntraline() {
  if (typeof Diff === 'undefined') return;
  $$('section.file:not(.generated) table.diff').forEach(highlightTable);
}
