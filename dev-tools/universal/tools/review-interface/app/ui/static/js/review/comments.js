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

const foldedGroups = new Set();
function commentGroup(path, ts) {
  const key = path || '';
  const g = el('section', 'cgroup' + (foldedGroups.has(key) ? ' folded' : ''));
  const head = el('div', 'chead');
  const fold = el('button', 'cfold'); fold.type = 'button';
  const body = el('div', 'cbody'); body.id = 'cg-' + Math.random().toString(36).slice(2, 8);
  const paint = () => {
    const open = !g.classList.contains('folded');
    fold.setAttribute('aria-expanded', String(open)); fold.setAttribute('aria-controls', body.id);
    fold.setAttribute('aria-label', (open ? 'Collapse ' : 'Expand ') + (path || 'General'));
  };
  fold.onclick = () => { g.classList.toggle('folded'); if (g.classList.contains('folded')) foldedGroups.add(key); else foldedGroups.delete(key); paint(); };
  const i = path ? D.files.findIndex(f => f.path === path) : -1;
  const name = el(i >= 0 ? 'button' : 'span', 'cpath');
  if (i >= 0) {
    name.type = 'button'; name.title = 'Open this file';
    name.onclick = () => openFromComments(path, ts.find(t => t.line));
    name.append(statusIcon(i));
  }
  name.append(el('span', 'cname', path || 'General'));
  head.append(fold, name, el('span', 'ccount', ts.length + (ts.length === 1 ? ' thread' : ' threads')));
  head.onclick = e => { if (e.target === head) fold.click(); };
  body.append(...ts.map(commentThread));
  g.append(head, body);
  paint();
  return g;
}

function renderComments() {
  const list = $('#clist');
  const groups = commentGroups();
  if (!groups.length) { list.replaceChildren(el('p', 'cempty', 'No comments yet.')); return; }
  list.replaceChildren(...groups.map(([path, ts]) => commentGroup(path, ts)));
}

function initComments() {
  $('#commentsbtn').onclick = () => { renderComments(); commentsModal.showModal(); };
}
