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
function renderChecks() {
  const box = $('#checks'); box.textContent = '';
  const done = D.notes.filter(n => isChecked(n.key)).length;
  $('#checkcount').textContent = D.notes.length ? `${done}/${D.notes.length}` : '';
  if (!D.notes.length) { box.append(el('p', 'empty', D.has_insights ? 'No recommendations for this PR.' : 'No recommendations yet. They appear here when an AI adds insights for this PR.')); return; }
  const ordered = [...D.notes].sort((a, b) => (isChecked(a.key) - isChecked(b.key)) || (RANK.indexOf(a.kind) - RANK.indexOf(b.kind)));
  for (const n of ordered) {
    const c = el('article', 'rec ' + n.kind + (isChecked(n.key) ? ' done' : '') + (activeNote === n.key ? ' active' : ''));
    c.id = 'rec-' + n.key;
    const head = el('div', 'rec-head');
    const cb = el('input', 'rd'); cb.type = 'checkbox'; cb.checked = isChecked(n.key); cb.setAttribute('aria-label', 'Mark as checked');
    cb.onchange = () => setChecked(n.key, cb.checked);
    head.append(cb, el('span', 'tag ' + n.kind, LABEL[n.kind]));
    const loc = el('button', 'rec-loc', noteLoc(n)); loc.type = 'button';
    loc.onclick = () => { activeNote = n.key; renderChecks(); if (n.rows.length) goToRows(n.rows); else if (n.file != null) goToFile(n.file); };
    head.append(loc);
    c.append(head, el('div', 'rec-title', n.title));
    if (n.body) c.append(clamped('rec-body', md(n.body)));
    if (n.comment) {
      const d = el('div', 'draft');
      const lab = el('div', 'draft-label', 'Draft comment');
      const copy = el('button', 'ghost sm', 'Copy'); copy.type = 'button';
      copy.onclick = () => navigator.clipboard.writeText(n.comment.replace(/\s*\n\s*/g, ' ').trim()).then(() => { copy.textContent = 'Copied'; setTimeout(() => (copy.textContent = 'Copy'), 1200); }, () => {});
      lab.append(copy);
      d.append(lab, clamped('draft-text', md(n.comment)));
      c.append(d);
    }
    const actions = el('div', 'rec-actions');
    const ts = threadsFor(n.key);
    if (ts.length) {
      const l = el('button', 'ghost sm', `💬 ${ts.length} thread${ts.length > 1 ? 's' : ''}`); l.type = 'button';
      l.onclick = () => focusThread(ts[0].id);
      actions.append(l);
    }
    actions.append(el('span', 'grow'));
    if (n.comment) {
      const use = el('button', 'sm', 'Use as comment'); use.type = 'button';
      use.onclick = () => startDraft(anchorFor(n), n.key, n.comment.replace(/\s*\n\s*/g, ' ').trim());
      actions.append(use);
    }
    const reply = el('button', 'primary sm', 'Reply'); reply.type = 'button';
    reply.onclick = () => startDraft(anchorFor(n), n.key, '');
    actions.append(reply);
    c.append(actions);
    box.append(c);
  }
}
function anchorFor(n) {
  const rows = n.rows.map(id => document.getElementById(id)).filter(Boolean);
  if (rows.length) return describe(rows);
  return { file: n.file, path: n.file != null ? D.files[n.file].path : null, side: 'RIGHT', start_line: n.start, line: n.end || n.start, rows: [], endRow: null };
}
function openNote(key) {
  activeNote = key;
  $('#checksec').open = true;
  renderChecks();
  const c = document.getElementById('rec-' + key);
  if (c) c.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
}
