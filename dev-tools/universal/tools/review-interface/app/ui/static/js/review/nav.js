let navAt = -1;
function navItems() {
  const pos = id => { const m = /^r(\d+)-(\d+)$/.exec(id || ''); return m ? D.order.indexOf(+m[1]) * 1e6 + +m[2] : -1; };
  const items = [];
  for (const n of D.notes) {
    const shown = rowShown(n.endRow);
    items.push({ id: 'n:' + n.key, rows: shown ? n.rows : [], pos: shown ? pos(n.endRow) : -1 });
  }
  for (const t of state.threads) {
    if (t.id === CHAT_ID || linkedNote(t)) continue;
    const a = anchors.get(t.id);
    items.push({ id: 't:' + t.id, rows: a ? a.rows : [], pos: a ? pos(a.endRow) : -1 });
  }
  return items.sort((a, b) => a.pos - b.pos);
}
function paintNav() {
  const count = $('#navcount');
  if (!count) return;
  const n = D.notes.length, m = state.threads.filter(t => t.id !== CHAT_ID).length;
  count.textContent = `${n} note${n === 1 ? '' : 's'} · ${m} comment${m === 1 ? '' : 's'}`;
  const none = !navItems().length;
  for (const id of ['#navprev', '#navnext']) { const b = $(id); if (b) b.disabled = none; }
}
function navGo(step) {
  const items = navItems();
  if (!items.length) return;
  const open = items.findIndex(x => x.id === cs.id);
  const from = open >= 0 ? open : navAt;
  const i = from < 0 ? (step > 0 ? 0 : items.length - 1) : (from + step + items.length) % items.length;
  const it = items[i];
  navAt = i;
  if (it.rows.length) { goToRows(it.rows, true); openCard(it.id, { pinned: true, focus: false }); }
  else { const s = $('.summary'); if (s) s.scrollIntoView({ block: 'center', behavior: 'auto' }); openCard(it.id, { pinned: true, centred: true, focus: false }); }
}
function initNav() {
  const prev = $('#navprev'), next = $('#navnext');
  if (prev) prev.onclick = () => navGo(-1);
  if (next) next.onclick = () => navGo(1);
  document.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey || (e.key !== 'n' && e.key !== 'p')) return;
    if (typingIn(e) || $('dialog[open]')) return;
    e.preventDefault();
    navGo(e.key === 'n' ? 1 : -1);
  });
}
