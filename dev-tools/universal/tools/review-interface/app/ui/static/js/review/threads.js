const drafts = {};
const stale = t => !!t.commit && t.commit !== SHA;
const STALE_TIP = 'This thread was started on an older commit, so GitHub would put it on the wrong line. Post it from a new thread.';
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
function startDraft(anchor, noteKey, text) {
  delete drafts.new;
  draftFor = { ...anchor, noteKey, text };
  renderThreads();
  const ta = $('#newtext');
  if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); ta.scrollIntoView({ block: 'nearest' }); }
}
function addThread(text) {
  const { text: _draft, ...anchor } = draftFor;
  const msg = { id: uid(), who: 'me', text, at: now() };
  const t = { id: uid(), ...anchor, commit: SHA, created: now(), resolved: false, resolvedAt: null, posted: null, messages: [msg] };
  state.threads.push(t);
  draftFor = null; sel = null; activeThread = t.id; delete drafts.new;
  paintSel(); renderThreads(); renderChecks();
  if (isPost(text)) postThread(t, msg.id); else persist();
}
const liveThread = t => state.threads.find(x => x.id === t.id) || t;
function addReply(t, text) {
  t = liveThread(t);
  const msg = { id: uid(), who: 'me', text, at: now() };
  delete drafts[t.id]; t.messages.push(msg); renderThreads();
  if (isPost(text)) postThread(t, msg.id); else persist();
}
function toggleResolved(t) { t = liveThread(t); t.resolved = !t.resolved; t.resolvedAt = now(); renderThreads(); persist(); }
function focusThread(id) {
  activeThread = id; renderThreads();
  const c = document.getElementById('th-' + id); if (c) c.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
}
const where = t => (t.path ? t.path.split('/').pop() : 'General') + (t.line ? ' ' + span(t) : '');
function composer(key, placeholder, value, onSave, onCancel, saveLabel, blocked) {
  const c = el('div', 'compose');
  const ta = el('textarea'); ta.placeholder = placeholder; ta.value = key in drafts ? drafts[key].value : value || ''; ta.dataset.draft = key;
  if (onCancel) ta.id = 'newtext';
  const row = el('div', 'row');
  row.append(el('span', 'hint', '⌘↵ send · start with post: to post on GitHub'));
  if (onCancel) { const x = el('button', 'sm', 'Cancel'); x.type = 'button'; x.onclick = onCancel; row.append(x); }
  const s = el('button', 'primary sm', saveLabel); s.type = 'button';
  const label = () => { const p = isPost(ta.value); s.textContent = p ? 'Post to GitHub' : saveLabel; s.classList.toggle('post', p); s.disabled = p && !!blocked; s.title = s.disabled ? blocked : ''; };
  ta.addEventListener('input', () => { drafts[key] = { value: ta.value }; label(); }); label();
  s.onclick = () => { const v = ta.value.trim(); if (v) onSave(v); };
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) s.click(); });
  row.append(s);
  c.append(ta, row);
  return c;
}
function renderThreads() {
  const list = $('#list'), top = list.scrollTop, focused = document.activeElement;
  let refocus = null;
  $$('textarea[data-draft]', list).forEach(ta => {
    if (ta.value) drafts[ta.dataset.draft] = { value: ta.value, start: ta.selectionStart, end: ta.selectionEnd };
    else delete drafts[ta.dataset.draft];
    if (ta === focused) refocus = ta.dataset.draft;
  });
  anchorThreads();
  list.textContent = '';
  const onlyFile = $('#fileonly').checked;
  if (draftFor) {
    const box = el('div', 'thread active new');
    const head = el('div', 'thread-head'); head.append(el('span', 'where', where(draftFor)), el('span', 'state', 'New'));
    box.append(head);
    const n = draftFor.noteKey && noteByKey.get(draftFor.noteKey);
    if (n) box.append(el('div', 'linked', '↳ ' + n.title));
    box.append(composer('new', 'Leave a comment…', draftFor.text, addThread, () => { draftFor = null; delete drafts.new; renderThreads(); }, 'Comment'));
    list.append(box);
  }
  const pos = p => D.order.indexOf(D.files.findIndex(f => f.path === p));
  let ts = [...state.threads].sort((a, b) => (a.resolved - b.resolved) || (pos(a.path) - pos(b.path)) || ((a.line || 0) - (b.line || 0)));
  if (onlyFile && current !== null) ts = ts.filter(t => t.path === D.files[current].path);
  if (!ts.length && !draftFor) list.append(el('p', 'empty', onlyFile ? 'No comments on this file.' : 'No comments yet. Click a line number (shift-click for a range), or Reply on a recommendation.'));
  for (const t of ts) {
    const here = current !== null && t.path === D.files[current].path;
    const box = el('div', 'thread' + (t.resolved ? ' resolved' : '') + (t.id === activeThread ? ' active' : '') + (here ? ' here' : ''));
    box.id = 'th-' + t.id;
    const head = el('div', 'thread-head');
    const last = t.messages[t.messages.length - 1];
    const st = el('span', 'state', t.resolved ? 'Resolved' : t.posted ? 'Posted' : isAi(last) ? AI_NAME + ' replied' : 'Open');
    st.classList.toggle('replied', !t.resolved && !t.posted && isAi(last));
    st.classList.toggle('posted', !!t.posted && !t.resolved);
    head.append(el('span', 'where', where(t)));
    if (stale(t)) { const o = el('span', 'old-commit', 'on an older commit'); o.title = STALE_TIP; head.append(o); }
    head.append(st);
    head.title = t.path || '';
    head.onclick = () => { activeThread = t.id; renderThreads(); const a = anchors.get(t.id); if (a) goToRows(a.rows); };
    box.append(head);
    const n = t.noteKey && noteByKey.get(t.noteKey);
    if (n) { const l = el('button', 'linked', '↳ ' + n.title); l.type = 'button'; l.onclick = () => openNote(t.noteKey); box.append(l); }
    for (const m of t.messages) {
      const d = el('div', 'msg ' + (isAi(m) ? 'claude' : 'me'));
      const bub = el('div', 'bubble');
      const meta = el('div', 'meta'); const tm = el('time', null, ago(m.at)); tm.dateTime = m.at;
      meta.append(el('b', null, isAi(m) ? AI_NAME : ME), tm);
      bub.append(meta, el('div', 'text', m.text));
      d.append(el('span', 'avatar', (isAi(m) ? AI_NAME : ME).charAt(0).toUpperCase()), bub);
      box.append(d);
    }
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
      const lastPost = [...t.messages].reverse().find(m => !isAi(m) && isPost(m.text));
      retry.onclick = () => postThread(liveThread(t), lastPost && lastPost.id);
      d.append(retry); box.append(d);
    }
    const c = composer(t.id, 'Reply…', '', v => addReply(t, v), null, 'Reply', stale(t) ? STALE_TIP : '');
    const res = el('button', 'sm', t.resolved ? 'Reopen' : 'Resolve'); res.type = 'button'; res.onclick = () => toggleResolved(t);
    $('.row', c).insertBefore(res, $('.row .primary', c));
    box.append(c);
    list.append(box);
  }
  list.scrollTop = top;
  const rt = refocus && $(`textarea[data-draft="${refocus}"]`, list);
  if (rt) { rt.focus(); const d = drafts[refocus]; if (d && d.start != null) rt.setSelectionRange(d.start, d.end); }
  pins();
}
function pins() {
  $$('.pin').forEach(p => p.remove());
  const byRow = new Map();
  for (const t of state.threads) { const a = anchors.get(t.id); if (!t.resolved && a) byRow.set(a.endRow, [...(byRow.get(a.endRow) || []), t]); }
  for (const [rowId, ts] of byRow) {
    const r = document.getElementById(rowId); if (!r) continue;
    const b = el('button', 'pin', '💬 ' + ts.length); b.type = 'button';
    b.onclick = () => focusThread(ts[0].id);
    $('td.code', r).append(b);
  }
}
let lastSynced = null;
function syncThreads() {
  if ($('#fileonly').checked) { renderThreads(); return; }
  $$('.thread').forEach(t => t.classList.remove('here'));
  if (current === null) return;
  const p = D.files[current].path;
  const mine = state.threads.filter(t => t.path === p);
  mine.forEach(t => { const e = document.getElementById('th-' + t.id); if (e) e.classList.add('here'); });
  if (mine.length && lastSynced !== current) {
    const e = document.getElementById('th-' + mine[0].id);
    if (e) e.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
  }
  lastSynced = current;
}

function initThreads() {
  $('#fileonly').onchange = renderThreads;
}
