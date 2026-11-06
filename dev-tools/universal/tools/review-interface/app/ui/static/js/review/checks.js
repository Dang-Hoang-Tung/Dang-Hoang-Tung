function clamped(cls, html) {
  const wrap = el('div', 'clamp ' + cls);
  const body = el('div', 'clamp-body'); body.innerHTML = html;
  const more = el('button', 'more', 'More'); more.type = 'button';
  more.onclick = () => { const open = wrap.classList.toggle('open'); more.textContent = open ? 'Less' : 'More'; };
  wrap.append(body, more);
  requestAnimationFrame(() => { if (body.scrollHeight <= body.clientHeight + 2) more.hidden = true; });
  return wrap;
}
function noteLoc(n) {
  if (n.file == null) return 'General';
  const at = n.start == null ? '' : (n.end && n.end !== n.start ? ` L${n.start}–${n.end}` : ` L${n.start}`);
  return fileName(n.file) + at;
}
const threadsFor = key => state.threads.filter(t => t.noteKey === key);
const noteText = n => n.comment.replace(/\s*\n\s*/g, ' ').trim();
function anchorFor(n) {
  const rows = n.rows.map(id => document.getElementById(id)).filter(Boolean);
  if (rows.length) return describe(rows);
  return { file: n.file, path: n.file != null ? D.files[n.file].path : null, side: 'RIGHT', start_line: n.start, line: n.end || n.start, rows: [], endRow: null };
}
function draftBlock(n) {
  const d = el('div', 'draft');
  const lab = el('div', 'draft-label', 'Draft comment');
  const copy = el('button', 'ghost sm', 'Copy'); copy.type = 'button';
  copy.onclick = () => navigator.clipboard.writeText(noteText(n)).then(() => { copy.textContent = 'Copied'; setTimeout(() => (copy.textContent = 'Copy'), 1200); }, () => {});
  const use = el('button', 'ghost sm', 'Use as comment'); use.type = 'button';
  use.onclick = () => { const k = 'n:' + n.key; drafts[k] = { value: noteText(n), post: false }; refreshCard(k); };
  const acts = el('span', 'draft-acts'); acts.append(copy, use);
  lab.append(acts);
  d.append(lab, clamped('draft-text', md(n.comment)));
  return d;
}
function noteCard(n) {
  const c = el('article', 'rec ' + n.kind);
  const head = el('div', 'rec-head');
  head.append(el('span', 'tag ' + n.kind, LABEL[n.kind]));
  const loc = el('button', 'rec-loc', noteLoc(n)); loc.type = 'button';
  loc.onclick = () => { if (n.rows.length) goToRows(n.rows, true); else if (n.file != null) goToFile(n.file); placeCard(); };
  head.append(loc);
  c.append(head, el('div', 'rec-title', n.title));
  if (n.body) c.append(clamped('rec-body', md(n.body)));
  if (n.comment) c.append(draftBlock(n));
  const chk = el('label', 'postopt markchk'), cb = el('input', 'rd'); cb.type = 'checkbox'; cb.checked = isChecked(n.key);
  cb.onchange = () => setChecked(n.key, cb.checked);
  chk.append(cb, 'Mark checked');
  c.append(chk);
  const ts = threadsFor(n.key);
  for (const t of ts) {
    const lt = el('div', 'thread linked-thread' + (t.resolved ? ' resolved' : ''));
    const meta = el('div', 'thread-head');
    if (stale(t)) { const o = el('span', 'old-commit', 'on an older commit'); o.title = STALE_TIP; meta.append(o); }
    meta.append(...syncPills(t), threadState(t), resolveButton(t));
    lt.append(meta);
    messageList(t, lt);
    c.append(lt);
  }
  const sy = ts.length ? isSynced(ts[0]) : null;
  const blocked = ts.length && stale(ts[0]) ? STALE_TIP : '';
  c.append(composer('n:' + n.key, 'Reply…', '', (v, post) => addNoteReply(n, v, post), null, sy ? 'Reply on GitHub' : 'Reply', blocked, sy === null ? null : sy));
  return c;
}
const rowShown = id => !!(id && document.getElementById(id));
function renderNoteList() {
  const box = $('#notelist'); if (!box) return;
  box.textContent = '';
  const items = [];
  for (const n of D.notes) if (!rowShown(n.endRow)) items.push({ id: 'n:' + n.key, tag: el('span', 'tag ' + n.kind, LABEL[n.kind]), title: n.title, loc: noteLoc(n), done: isChecked(n.key) });
  for (const t of state.threads) if (t.id !== CHAT_ID && !linkedNote(t) && !anchors.has(t.id)) items.push({ id: 't:' + t.id, tag: el('span', 'tag thread', 'Comment'), title: t.messages[0].text, loc: where(t), done: t.resolved });
  if (!items.length) return;
  box.append(el('h3', null, 'Notes'));
  for (const it of items) {
    const b = el('button', 'nrow' + (it.done ? ' done' : '')); b.type = 'button';
    b.append(it.tag, el('span', 'nt', it.title), el('span', 'nloc', it.loc));
    b.onclick = () => openCard(it.id, { pinned: true, centred: true });
    box.append(b);
  }
}
