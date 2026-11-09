// "PR comments": every comment thread, grouped by file, without code. A file path opens that file's changes.
const commentsModal = $('#commentsmodal');

function commentGroups() {
  const groups = new Map();
  for (const t of state.threads) {
    if (t.id === CHAT_ID || !t.messages || !t.messages.length) continue;
    const key = t.path || '';
    groups.set(key, [...(groups.get(key) || []), t]);
  }
  const order = p => { const i = D.files.findIndex(f => f.path === p); return p ? (i < 0 ? 1e6 : i) : -1; };
  return [...groups].sort((a, b) => order(a[0]) - order(b[0]))
    .map(([path, ts]) => [path, ts.sort((a, b) => (a.line || 0) - (b.line || 0))]);
}

function openFromComments(path, t) {
  const i = D.files.findIndex(f => f.path === path);
  if (i < 0) return;
  commentsModal.close();
  openFile(i, { mode: 'preview', side: t && t.side === 'LEFT' ? 'L' : 'R', line: t ? t.line : null });
}

function commentThread(t) {
  const box = el('div', 'thread cthread' + (t.resolved ? ' resolved' : ''));
  const head = el('div', 'thread-head');
  const loc = t.line ? el('button', 'where cloc', span(t)) : el('span', 'where', 'General');
  if (t.line) { loc.type = 'button'; loc.title = 'Show in file'; loc.onclick = () => openFromComments(t.path, t); }
  head.append(loc, ...syncPills(t), threadState(t));
  box.append(head);
  messageList(t, box);
  return box;
}

function renderComments() {
  const list = $('#clist');
  const groups = commentGroups();
  if (!groups.length) { list.replaceChildren(el('p', 'cempty', 'No comments yet.')); return; }
  list.replaceChildren(...groups.map(([path, ts]) => {
    const g = el('section', 'cgroup');
    const known = D.files.some(f => f.path === path);
    const h = el(known ? 'button' : 'h3', 'cpath');
    if (known) h.append(statusIcon(D.files.findIndex(f => f.path === path)));
    h.append(path || 'General');
    if (known) { h.type = 'button'; h.title = 'Open this file'; h.onclick = () => openFromComments(path, ts.find(t => t.line)); }
    g.append(h, ...ts.map(commentThread));
    return g;
  }));
}

function initComments() {
  $('#commentsbtn').onclick = () => { renderComments(); commentsModal.showModal(); };
}
