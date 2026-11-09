// One file in a modal: the preview's changes, the whole file, or (via an import link) a file the PR doesn't touch.
// Rows of PR files behave like the preview, so selection and comments work. Back/forward walk the files visited.
let fv = null;
const fvBox = $('#fullview'), fvBody = $('#fvbody');
const fvNav = { stack: [], pos: -1 };
const resolved = new Map();
const IMPORT_RE = /(\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*|\bexport\s+\*\s+from\s*)(['"])([^'"\n]+)\2/g;
const MODE_LABEL = { preview: 'changes', full: 'full file', blob: 'file' };

function fvRow(side, line) {
  if (!fv || !line) return null;
  const r = side === 'L' ? $(`tr.del[data-o="${line}"]`, fvBody) : $(`tr[data-n="${line}"]`, fvBody);
  return r ? r.id : null;
}
const noteRow = n => (fv && n.file === fv.file && fvRow('R', n.end || n.start)) || n.endRow;
const fileIndex = path => D.files.findIndex(f => f.path === path);

function langFor(i) {
  const s = i >= 0 && $('#f-' + i);
  return s && s.dataset.lang;
}

function previewTable(i) {
  const s = $('#f-' + i);
  const lazy = s && $('template.lazy', s);
  const table = s && ($('table.diff', s) || (lazy && lazy.content.querySelector('table.diff')));
  if (!table) return null;
  const copy = (table.closest('.diffwrap') || table).cloneNode(true);
  $$('[id]', copy).forEach(n => { n.id = 'x' + n.id.slice(1); });
  $$('.ti', copy).forEach(n => n.remove());
  $$('tr.sel, tr.flash', copy).forEach(r => r.classList.remove('sel', 'flash'));
  return { copy, painted: !!s.dataset.highlighted };
}

async function fvApi(url) {
  const r = await fetch(url, { credentials: 'same-origin' });
  const res = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(res.error || 'the helper replied ' + r.status);
  return res;
}

function wrapRange(t, start, end, spec) {
  let pos = 0;
  const walker = document.createTreeWalker(t, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const len = n.textContent.length;
    if (start >= pos && end <= pos + len) {
      const mid = n.splitText(start - pos);
      mid.splitText(end - start);
      const a = el('span', 'implink'); a.dataset.spec = spec; a.title = 'Open ' + spec;
      mid.replaceWith(a); a.append(mid);
      return;
    }
    pos += len;
  }
}

function linkImports(wrap) {
  if (!served) return;
  $$('td.code .t', wrap).forEach(t => {
    const text = t.textContent;
    const hits = [...text.matchAll(IMPORT_RE)];
    for (const m of hits.reverse()) {
      const start = m.index + m[1].length + 1;
      wrapRange(t, start, start + m[3].length, m[3]);
    }
  });
}

async function paintCode(wrap, painted) {
  if (!painted) await highlightSection(wrap);
  linkImports(wrap);
}

function topLine() {
  const top = fvBody.getBoundingClientRect().top;
  const r = $$('tr[data-n]', fvBody).find(x => x.dataset.n && x.getBoundingClientRect().bottom > top + 8);
  return r ? +r.dataset.n : null;
}

function scrollToLine(side, line, flash) {
  const id = fvRow(side, line);
  const r = id ? document.getElementById(id) : $('tr.add, tr.del', fvBody);
  if (!r) { fvBody.scrollTop = 0; return; }
  r.scrollIntoView({ block: line && !flash ? 'start' : 'center' });
  if (flash && id) { r.classList.add('flash'); setTimeout(() => r.classList.remove('flash'), 1600); }
}

function note(text) {
  const n = $('#fvnote');
  n.textContent = text; n.hidden = !text;
  clearTimeout(note.t);
  if (text) note.t = setTimeout(() => { n.hidden = true; }, 3500);
}

function paintHead() {
  const blob = fv && fv.mode === 'blob';
  const title = $('#fvtitle');
  title.replaceChildren();
  if (fv && fv.file !== null) title.append(statusIcon(fv.file));
  if (fv) title.append(fv.path);
  $('#fvtag').hidden = !blob;
  $('.fv-seg', fvBox).hidden = blob;
  $$('.fv-seg button', fvBox).forEach(b => {
    b.setAttribute('aria-pressed', String(!!fv && b.dataset.mode === fv.mode));
    if (b.dataset.mode === 'full') { b.disabled = !served; b.title = served ? '' : 'Needs the local helper (run review.py)'; }
  });
  const prev = fvNav.stack[fvNav.pos - 1], next = fvNav.stack[fvNav.pos + 1];
  const tip = (dir, e) => (e ? `${dir}: ${e.path} (${MODE_LABEL[e.mode]})` : dir);
  const back = $('#fvback'), fwd = $('#fvfwd');
  back.disabled = !prev; back.title = tip('Back', prev); back.setAttribute('aria-label', back.title);
  fwd.disabled = !next; fwd.title = tip('Forward', next); fwd.setAttribute('aria-label', fwd.title);
}

function dropModalDraft() {
  if (draftFor && /^[xb]/.test(String(draftFor.endRow))) { draftFor = null; delete drafts.new; }
}

async function show(entry, { side = 'R', line = null, flash = false } = {}) {
  closeCard(); sel = null; paintSel(); dropModalDraft(); note('');
  const i = fileIndex(entry.path);
  fv = { file: i >= 0 ? i : null, path: entry.path, mode: entry.mode };
  paintHead();
  const ticket = fv;
  fvBody.replaceChildren(el('p', 'fv-msg', 'Loading…'));
  try {
    const wrap = el('div', 'fvfile');
    let painted = false;
    if (entry.mode === 'preview') {
      const p = previewTable(i);
      if (!p) { fvBody.replaceChildren(el('p', 'fv-msg', 'No changes to show for this file.')); return; }
      wrap.append(p.copy); painted = p.painted;
    } else if (entry.mode === 'full') {
      const res = await fvApi(`/api/file/${D.slug}?i=${i}&path=${encodeURIComponent(entry.path)}`);
      if (fv !== ticket) return;
      if (!res.html) { fvBody.replaceChildren(el('p', 'fv-msg', 'Nothing to show for this file.')); return; }
      wrap.innerHTML = res.html;
      if (typeof Diff !== 'undefined') highlightTable($('table.diff', wrap));
    } else {
      const res = await fvApi(`/api/blob/${D.slug}?path=${encodeURIComponent(entry.path)}`);
      if (fv !== ticket) return;
      wrap.innerHTML = res.html;
      if (res.lang) wrap.dataset.lang = res.lang;
    }
    if (!wrap.dataset.lang && langFor(i)) wrap.dataset.lang = langFor(i);
    fvBody.replaceChildren(wrap);
    renderThreads();
    scrollToLine(side, line, flash);
    await paintCode(wrap, painted);
  } catch (e) {
    if (fv === ticket) fvBody.replaceChildren(el('p', 'fv-msg err', 'Could not load the file: ' + e.message));
  }
}

function remember() {
  const cur = fvNav.stack[fvNav.pos];
  if (cur && fv) { cur.line = topLine(); cur.mode = fv.mode; }
}

function go(path, mode) {
  remember();
  fvNav.stack = fvNav.stack.slice(0, fvNav.pos + 1);
  fvNav.stack.push({ path, mode, line: null });
  fvNav.pos++;
  show(fvNav.stack[fvNav.pos]);
}

function step(d) {
  const e = fvNav.stack[fvNav.pos + d];
  if (!e) return;
  remember();
  fvNav.pos += d;
  show(e, { line: e.line });
}

async function followImport(span) {
  const key = (fv && fv.path) + '\n' + span.dataset.spec;
  try {
    let path = resolved.get(key);
    if (!path) {
      note('Finding ' + span.dataset.spec + '…');
      path = (await fvApi(`/api/resolve/${D.slug}?from=${encodeURIComponent(fv.path)}&spec=${encodeURIComponent(span.dataset.spec)}`)).path;
      resolved.set(key, path);
    }
    go(path, fileIndex(path) >= 0 ? 'full' : 'blob');
  } catch (e) { note(e.message); }
}

function openFile(i, { mode = 'full', side = 'R', line = null } = {}) {
  const entry = { path: D.files[i].path, mode: mode === 'full' && !served ? 'preview' : mode, line: null };
  fvNav.stack = [entry]; fvNav.pos = 0;
  fvBox.hidden = false;
  document.body.classList.add('fv-open');
  show(entry, { side, line, flash: !!line });
}

function closeFull() {
  if (!fv) return;
  dropModalDraft();
  fv = null; sel = null;
  fvNav.stack = []; fvNav.pos = -1;
  closeCard();
  fvBox.hidden = true;
  fvBody.replaceChildren();
  document.body.classList.remove('fv-open');
  paintSel();
  renderThreads();
}

function initFullView() {
  $$('.fullbtn').forEach(b => {
    if (!served) { b.hidden = true; return; }
    b.onclick = e => { e.stopPropagation(); openFile(+b.dataset.full); };
  });
  $$('.fv-seg button', fvBox).forEach(b => {
    b.onclick = () => {
      if (!fv || fv.file === null || b.dataset.mode === fv.mode) return;
      const line = topLine(), cur = fvNav.stack[fvNav.pos];
      cur.mode = b.dataset.mode;
      show(cur, { line });
    };
  });
  $('#fvback').onclick = () => step(-1);
  $('#fvfwd').onclick = () => step(1);
  fvBody.addEventListener('click', e => { const s = e.target.closest('.implink'); if (s) followImport(s); });
  $('[data-close]', fvBox).onclick = closeFull;
  fvBox.addEventListener('click', e => { if (e.target === fvBox) closeFull(); });
  fvBody.addEventListener('scroll', () => { placeCard(); if (sel) paintSel(); }, { passive: true });
  addEventListener('keydown', e => {
    if (!fv || $('dialog[open]')) return;
    if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) { e.preventDefault(); step(e.key === 'ArrowLeft' ? -1 : 1); return; }
    if (e.key !== 'Escape' || cs.id || sel) return;
    e.stopPropagation();
    closeFull();
  }, true);
}
