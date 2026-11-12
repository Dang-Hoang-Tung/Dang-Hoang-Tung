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
  paintViewNav();
}

// One back/forward history across the AI Brief, PR comments and the 1-file viewer.
// Entries: {kind: 'brief'} | {kind: 'comments'} | {kind: 'file', path, mode, line}.
const NAV_DIALOGS = { brief: '#briefmodal', comments: '#commentsmodal' };
const navLabel = e => (e.kind === 'brief' ? 'AI Brief' : e.kind === 'comments' ? 'PR comments' : `${e.path} (${MODE_LABEL[e.mode]})`);

function paintViewNav() {
  const prev = fvNav.stack[fvNav.pos - 1], next = fvNav.stack[fvNav.pos + 1];
  $$('.vnav [data-dir]').forEach(b => {
    const back = b.dataset.dir === '-1', e = back ? prev : next, dir = back ? 'Back' : 'Forward';
    b.disabled = !e;
    b.title = e ? `${dir}: ${navLabel(e)}` : dir;
    b.setAttribute('aria-label', b.title);
  });
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
      applyHideWs();
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

function hideOverlay() {
  if (fvBox.hidden) return;
  dropModalDraft();
  fv = null; sel = null;
  closeCard();
  fvBox.hidden = true;
  fvBody.replaceChildren();
  document.body.classList.remove('fv-open');
  paintSel();
  renderThreads();
}

function closeNavDialogs() {
  Object.values(NAV_DIALOGS).forEach(sel => { const d = $(sel); if (d.open) d.close(); });
}

function remember() {
  const cur = fvNav.stack[fvNav.pos];
  if (!cur) return;
  if (cur.kind === 'file') { if (fv) { cur.line = topLine(); cur.mode = fv.mode; } }
  else cur.scroll = $(NAV_DIALOGS[cur.kind] + ' .modal-body').scrollTop;
}

function present(entry, opts = {}) {
  if (entry.kind === 'file') {
    closeNavDialogs();
    fvBox.hidden = false;
    document.body.classList.add('fv-open');
    return show(entry, opts);
  }
  hideOverlay();
  closeNavDialogs();
  const d = $(NAV_DIALOGS[entry.kind]);
  if (entry.kind === 'comments') renderComments();
  d.showModal();
  $('.modal-body', d).scrollTop = entry.scroll || 0;
  paintViewNav();
  return Promise.resolve();
}

function startNav(entry, opts) {
  remember();
  fvNav.stack = [entry]; fvNav.pos = 0;
  return present(entry, opts);
}

function go(entry, opts) {
  remember();
  fvNav.stack = fvNav.stack.slice(0, fvNav.pos + 1);
  fvNav.stack.push(entry);
  fvNav.pos++;
  return present(entry, opts);
}

function step(d) {
  const e = fvNav.stack[fvNav.pos + d];
  if (!e) return;
  remember();
  fvNav.pos += d;
  present(e, { line: e.line });
}

function endNav() {
  fvNav.stack = []; fvNav.pos = -1;
  hideOverlay();
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
    go({ kind: 'file', path, mode: fileIndex(path) >= 0 ? 'full' : 'blob', line: null });
  } catch (e) { note(e.message); }
}

const fileEntry = (i, mode) => ({ kind: 'file', path: D.files[i].path, mode: mode === 'full' && !served ? 'preview' : mode, line: null });

// From another viewer (brief, comments): a step forward in the history. From the page: a fresh history.
function openFile(i, { mode = 'full', side = 'R', line = null } = {}) {
  const entry = fileEntry(i, mode), opts = { side, line, flash: !!line };
  return fvNav.stack.length ? go(entry, opts) : startNav(entry, opts);
}

// Paths in the AI Brief: `path`, `path:12` or `path:12-14`, matched to a file in this PR (whole path, or a unique ending).
const PATH_RE = /^([\w@.\-/]+\.[A-Za-z0-9]+)(?::(\d+)(?:[-–](\d+))?)?$/;
function briefTarget(text) {
  const m = PATH_RE.exec(text.trim());
  if (!m) return null;
  let i = fileIndex(m[1]);
  if (i < 0) {
    const hits = D.files.map((f, k) => (f.path.endsWith('/' + m[1]) ? k : -1)).filter(k => k >= 0);
    if (hits.length !== 1) return null;
    i = hits[0];
  }
  return { i, line: m[2] ? +m[2] : null };
}

async function openFromBrief(t) {
  await openFile(t.i, { mode: 'preview', line: t.line });
  if (t.line && served && fv && !fvRow('R', t.line)) {
    const cur = fvNav.stack[fvNav.pos];
    cur.mode = 'full';
    await show(cur, { line: t.line, flash: true });
  }
  const n = t.line && D.notes.find(x => x.file === t.i && x.start != null && t.line >= x.start && t.line <= (x.end || x.start));
  if (n && markerFor('n:' + n.key)) openCard('n:' + n.key, { pinned: true });
}

function initBriefLinks() {
  $$('#briefmodal code').forEach(c => {
    const t = briefTarget(c.textContent);
    if (!t) return;
    const b = el('button', 'codelink');
    b.type = 'button';
    b.title = 'Open ' + D.files[t.i].path + (t.line ? ' at line ' + t.line : '');
    c.replaceWith(b);
    b.append(c);
    b.onclick = () => openFromBrief(t);
  });
}

function closeFull() { endNav(); }

function initFullView() {
  initBriefLinks();
  $$('.fullbtn').forEach(b => {
    if (!served) { b.hidden = true; return; }
    b.onclick = e => { e.stopPropagation(); startNav(fileEntry(+b.dataset.full, 'full')); };
  });
  $$('.fv-seg button', fvBox).forEach(b => {
    b.onclick = () => {
      if (!fv || fv.file === null || b.dataset.mode === fv.mode) return;
      const line = topLine(), cur = fvNav.stack[fvNav.pos];
      cur.mode = b.dataset.mode;
      show(cur, { line });
    };
  });
  $$('.vnav [data-dir]').forEach(b => { b.onclick = () => step(+b.dataset.dir); });
  // A dialog closed by the reviewer (×, Esc, backdrop) ends the history; one closed because we moved on does not.
  Object.entries(NAV_DIALOGS).forEach(([kind, sel]) => $(sel).addEventListener('close', () => {
    const cur = fvNav.stack[fvNav.pos];
    if (cur && cur.kind === kind) endNav();
  }));
  fvBody.addEventListener('click', e => { const s = e.target.closest('.implink'); if (s) followImport(s); });
  $('[data-close]', fvBox).onclick = closeFull;
  fvBox.addEventListener('click', e => { if (e.target === fvBox) closeFull(); });
  fvBody.addEventListener('scroll', () => { placeCard(); if (sel) paintSel(); }, { passive: true });
  addEventListener('keydown', e => {
    if (!fvNav.stack.length) return;
    if (e.altKey && !typingIn(e) && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) { e.preventDefault(); step(e.key === 'ArrowLeft' ? -1 : 1); return; }
    if (!fv || $('dialog[open]') || e.key !== 'Escape' || cs.id || sel) return;
    e.stopPropagation();
    closeFull();
  }, true);
}
