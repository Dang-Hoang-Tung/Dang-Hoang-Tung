const drafts = {};
const isSynced = t => !!t.synced || String(t.id).startsWith('gh-');
const stale = t => !isSynced(t) && !!t.commit && t.commit !== SHA;
const STALE_TIP = 'This thread was started on an older commit, so GitHub would put it on the wrong line. Post it from a new thread.';
const BUBBLE = '<svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>';
const anchors = new Map();
function anchorThreads() {
  const rows = new Map();
  $$('tr[data-f]').forEach(r => {
    if (r.dataset.n) rows.set(r.dataset.f + 'R' + r.dataset.n, r.id);
    if (r.dataset.o && r.classList.contains('del')) rows.set(r.dataset.f + 'L' + r.dataset.o, r.id);
  });
  anchors.clear();
  for (const t of state.threads) {
    const f = D.files.findIndex(x => x.path === t.path), side = t.side === 'LEFT' ? 'L' : 'R';
    if (f < 0 || !t.line || !rows.has(f + side + t.line)) continue;
    const ids = [];
    for (let n = t.start_line || t.line; n <= t.line; n++) if (rows.has(f + side + n)) ids.push(rows.get(f + side + n));
    anchors.set(t.id, { rows: ids, endRow: rows.get(f + side + t.line) });
  }
}
const linkedNote = t => !!(t.noteKey && noteByKey.has(t.noteKey));
const cardIdFor = t => (linkedNote(t) ? 'n:' + t.noteKey : 't:' + t.id);
function startDraft(anchor) {
  delete drafts.new;
  draftFor = { ...anchor, noteKey: null };
  renderThreads();
  openCard('new', { pinned: true });
}
function createThread(anchor, noteKey, text, post) {
  const sync = !!post;
  const msg = { id: uid(), who: 'me', text, at: now(), ...(post && { post: true }) };
  const t = { id: uid(), ...anchor, noteKey, commit: SHA, created: now(), resolved: false, resolvedAt: null, posted: null, ...(sync && { synced: true }), messages: [msg] };
  state.threads.push(t);
  renderThreads();
  openCard(cardIdFor(t), { pinned: true, focus: false });
  if (post) postThread(t, msg.id); else persist();
}
function addThread(text, post) {
  const { noteKey, ...anchor } = draftFor;
  draftFor = null; sel = null; delete drafts.new;
  paintSel();
  createThread(anchor, noteKey, text, post);
}
const liveThread = t => state.threads.find(x => x.id === t.id) || t;
function addReply(t, text, post, draftKey = t.id) {
  t = liveThread(t);
  const msg = { id: uid(), who: 'me', text, at: now(), ...(post && { post: true }) };
  delete drafts[draftKey]; t.messages.push(msg); renderThreads();
  if (post) postThread(t, msg.id); else persist();
}
function addNoteReply(n, text, post) {
  const ts = threadsFor(n.key);
  if (ts.length) addReply(ts[0], text, post, 'n:' + n.key);
  else { delete drafts['n:' + n.key]; createThread(anchorFor(n), n.key, text, post); }
}
function toggleResolved(t) { t = liveThread(t); t.resolved = !t.resolved; t.resolvedAt = now(); renderThreads(); persist(); }
const where = t => (t.path ? t.path.split('/').pop() : 'General') + (t.line ? ' ' + span(t) : '');
function whereEl(t) {
  const w = el('span', 'where');
  const i = t.path ? D.files.findIndex(f => f.path === t.path) : -1;
  if (i >= 0) w.append(statusIcon(i));
  w.append(where(t));
  return w;
}
function composer(key, placeholder, value, onSave, onCancel, saveLabel, blocked, fixed = null) {
  const c = el('div', 'compose');
  const ta = el('textarea'); ta.placeholder = placeholder; ta.value = key in drafts ? drafts[key].value : value || ''; ta.dataset.draft = key;
  if (onCancel) ta.id = 'newtext';
  const row = el('div', 'row');
  const opt = el('label', 'postopt'), box = el('input'); box.type = 'checkbox'; box.dataset.postfor = key;
  box.checked = fixed === null ? !blocked && !!(drafts[key] && drafts[key].post) : fixed;
  if (blocked && fixed === null) { box.disabled = true; opt.title = blocked; }
  opt.append(box, 'Post GitHub comment');
  if (fixed === null) row.append(opt);
  if (onCancel) { const x = el('button', 'sm', 'Cancel'); x.type = 'button'; x.onclick = onCancel; row.append(x); }
  const s = el('button', 'primary sm', saveLabel); s.type = 'button'; s.title = '⌘↵';
  const label = () => { s.textContent = fixed ? saveLabel : box.checked ? 'Post' : saveLabel; s.classList.toggle('post', box.checked); };
  const keep = () => { drafts[key] = { ...drafts[key], value: ta.value, post: fixed === null && box.checked }; label(); };
  ta.addEventListener('input', keep); box.addEventListener('change', keep); label();
  s.onclick = () => {
    const v = ta.value.trim(), post = box.checked;
    if (!v) return;
    // Cleared before saving: the re-render would otherwise read the text back into the draft.
    ta.value = ''; delete drafts[key];
    onSave(v, post);
  };
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) s.click(); });
  row.append(s);
  c.append(ta, row);
  return c;
}
function stepsList(steps) {
  const d = el('details', 'steps');
  d.append(el('summary', null, `Show steps (${steps.length})`));
  const ol = el('ol');
  steps.forEach(st => ol.append(el('li', null, st.text)));
  d.append(ol);
  return d;
}
function thinkingNow(steps) {
  const box = el('div', 'thinking');
  box.setAttribute('aria-live', 'polite');
  steps.forEach((st, k) => box.append(el('div', k === steps.length - 1 ? 'now' : 'done', st.text)));
  return box;
}
function messageList(t, box) {
  for (const m of t.messages) {
    const gh = m.who === 'github';
    const d = el('div', 'msg ' + (isAi(m) ? 'claude' : gh ? 'gh' : 'me'));
    const bub = el('div', 'bubble');
    const meta = el('div', 'meta'); const tm = el('time', null, ago(m.at)); tm.dateTime = m.at;
    const name = isAi(m) ? AI_NAME : gh ? m.author || 'GitHub' : ME;
    if (gh && String(m.url).startsWith('https://')) { const a = el('a', null, name); a.href = m.url; a.target = '_blank'; a.rel = 'noopener'; meta.append(el('b', null), tm); $('b', meta).append(a); }
    else meta.append(el('b', null, name), tm);
    bub.append(meta, el('div', 'text', m.text));
    if (isAi(m) && m.steps && m.steps.length) bub.append(stepsList(m.steps));
    d.append(el('span', 'avatar', name.charAt(0).toUpperCase()), bub);
    box.append(d);
  }
  if (t.thinking && t.thinking.length && lastFromMe(t)) box.append(thinkingNow(t.thinking));
  if (t.posted && t.posted.url) {
    const d = el('div', 'posted'), label = t.posted.dry_run ? 'Posted (dry run)' : 'Posted to GitHub';
    if (String(t.posted.url).startsWith('https://')) { const a = el('a', null, label); a.href = t.posted.url; a.target = '_blank'; a.rel = 'noopener'; d.append(a); }
    else d.append(label);
    box.append(d);
  }
  const ps = postState[t.id];
  if (ps && ps.busy) box.append(el('div', 'posting', 'Posting to GitHub…'));
  if (ps && ps.error) {
    const d = el('div', 'post-error', ps.error);
    const retry = el('button', 'sm', 'Try again'); retry.type = 'button';
    if (stale(t)) { retry.disabled = true; retry.title = STALE_TIP; }
    const lastPost = [...t.messages].reverse().find(m => !isAi(m) && m.post);
    retry.onclick = () => postThread(liveThread(t), lastPost && lastPost.id);
    d.append(retry); box.append(d);
  }
}
function syncPills(t) {
  if (!isSynced(t)) return [];
  const p = [el('span', 'pill gh', 'GitHub')];
  if (t.outdated) p.push(el('span', 'pill outdated', 'outdated'));
  return p;
}
function threadState(t) {
  const last = t.messages[t.messages.length - 1];
  const st = el('span', 'state', t.resolved ? 'Resolved' : t.posted ? 'Posted' : isAi(last) ? AI_NAME + ' replied' : 'Open');
  st.classList.toggle('replied', !t.resolved && !t.posted && isAi(last));
  st.classList.toggle('posted', !!t.posted && !t.resolved);
  return st;
}
function resolveButton(t) {
  const b = el('button', 'sm', t.resolved ? 'Reopen' : 'Resolve'); b.type = 'button'; b.onclick = () => toggleResolved(t);
  return b;
}
function threadCard(t) {
  const box = el('div', 'thread' + (t.resolved ? ' resolved' : ''));
  const head = el('div', 'thread-head');
  head.append(whereEl(t));
  if (stale(t)) { const o = el('span', 'old-commit', 'on an older commit'); o.title = STALE_TIP; head.append(o); }
  head.append(...syncPills(t), threadState(t));
  head.title = t.path || '';
  box.append(head);
  messageList(t, box);
  const sy = isSynced(t);
  const c = composer(t.id, 'Reply…', '', v => addReply(t, v, sy), null, sy ? 'Reply on GitHub' : 'Send', '', sy);
  $('.row', c).insertBefore(resolveButton(t), $('.row .primary', c));
  box.append(c);
  return box;
}
function draftCard() {
  const box = el('div', 'thread new');
  const head = el('div', 'thread-head'); head.append(whereEl(draftFor), el('span', 'state', 'New'));
  const cancel = () => { draftFor = null; delete drafts.new; closeCard(); renderThreads(); paintSel(); };
  box.append(head, composer('new', 'Leave a comment…', '', addThread, cancel, 'Comment'));
  return box;
}
function marker(id, cls, count, label) {
  const b = el('button', 'ti ' + cls); b.type = 'button'; b.dataset.card = id;
  b.setAttribute('aria-label', label); b.innerHTML = BUBBLE;
  if (count) b.append(el('span', 'n', count));
  if (id === cs.id) b.classList.add('open');
  return b;
}
function drawMarkers() {
  $$('.ti').forEach(b => b.remove());
  const byRow = new Map();
  const add = (rowId, b) => { if (rowId) byRow.set(rowId, [...(byRow.get(rowId) || []), b]); };
  for (const n of D.notes) {
    const count = threadsFor(n.key).reduce((s, t) => s + t.messages.length, 0);
    add(noteRow(n), marker('n:' + n.key, n.kind + (isChecked(n.key) ? ' done' : ''), count, LABEL[n.kind] + ': ' + n.title));
  }
  for (const t of state.threads) {
    const a = anchors.get(t.id);
    if (a && !linkedNote(t)) add(a.endRow, marker('t:' + t.id, 'thread' + (t.resolved ? ' resolved' : ''), t.messages.length, 'Comment thread ' + where(t)));
  }
  if (draftFor) add(draftFor.endRow, marker('new', 'thread draft', 0, 'New comment'));
  for (const [rowId, bs] of byRow) {
    const r = document.getElementById(rowId);
    if (r) $('td.code', r).append(...bs);
  }
}
function saveDrafts() {
  const focused = document.activeElement;
  let refocus = null;
  $$('textarea[data-draft]', pcard).forEach(ta => {
    const k = ta.dataset.draft, post = !!(drafts[k] && drafts[k].post);
    if (ta.value || post) drafts[k] = { value: ta.value, post, start: ta.selectionStart, end: ta.selectionEnd };
    else delete drafts[k];
    if (ta === focused) refocus = k;
  });
  return refocus;
}
function renderThreads() {
  const refocus = saveDrafts();
  anchorThreads();
  drawMarkers();
  renderNoteList();
  paintNav();
  refreshCard(refocus);
  renderChat();
  watchReplies();
}
