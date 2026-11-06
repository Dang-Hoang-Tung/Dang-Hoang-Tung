// "Hide whitespace changes": a del row and an add row that differ only in whitespace show as one unchanged row.
const WS_KEY = 'pr-review-hidews';
const squash = s => s.replace(/\s+/g, '');
const rowText = r => { const t = $('.t', r); return t ? t.textContent : ''; };

function pairWsBlock(dels, adds) {
  let i = 0, j = 0;
  const same = (a, b) => squash(rowText(a)) === squash(rowText(b));
  for (const part of Diff.diffArrays(dels, adds, { comparator: same })) {
    if (part.added) j += part.count;
    else if (part.removed) i += part.count;
    else {
      for (let k = 0; k < part.count; k++) { dels[i + k].classList.add('ws-hidden'); adds[j + k].classList.add('ws-only'); }
      i += part.count; j += part.count;
    }
  }
}

function applyHideWs() {
  const box = $('#hidews');
  $$('tr.ws-hidden').forEach(r => r.classList.remove('ws-hidden'));
  $$('tr.ws-only').forEach(r => r.classList.remove('ws-only'));
  if (!box || !box.checked || typeof Diff === 'undefined') return;
  $$('section.file table.diff').forEach(table => {
    const rows = [...table.rows];
    for (let i = 0; i < rows.length;) {
      if (!plain(rows[i], 'del')) { i++; continue; }
      const dels = [], adds = [];
      while (i < rows.length && plain(rows[i], 'del')) dels.push(rows[i++]);
      while (i < rows.length && plain(rows[i], 'add')) adds.push(rows[i++]);
      if (adds.length) pairWsBlock(dels, adds);
    }
  });
}

function initHideWs() {
  const box = $('#hidews'); if (!box) return;
  try { box.checked = localStorage.getItem(WS_KEY) === '1'; } catch (_) {}
  box.onchange = () => { try { localStorage.setItem(WS_KEY, box.checked ? '1' : '0'); } catch (_) {} applyHideWs(); };
  applyHideWs();
}
