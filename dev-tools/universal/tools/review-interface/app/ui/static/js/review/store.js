const now = () => new Date().toISOString();
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

let state = { pr: PR, commit: SHA, threads: [], read: {}, checked: {} };
let online = false, viewedCollapsed = false;
const served = location.protocol.startsWith('http');

async function api(method, body) {
  const r = await fetch('/api/state/' + D.slug, {
    method, credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (r.status === 403) throw new Error('the session ended. Run review.py again');
  if (r.status !== 200) { const b = await r.json().catch(() => ({})); throw Object.assign(new Error(b.error || 'the helper replied ' + r.status), { status: r.status }); }
  return r.json();
}
function laterMap(a = {}, b = {}) {
  const out = { ...a };
  for (const [k, v] of Object.entries(b)) if (!out[k] || (v.at || '') > (out[k].at || '')) out[k] = v;
  return out;
}
function merge(disk, mine) {
  const byId = new Map((disk.threads || []).map(t => [t.id, t]));
  for (const t of mine.threads) {
    const d = byId.get(t.id);
    if (!d) { byId.set(t.id, t); continue; }
    const ids = new Set(d.messages.map(m => m.id));
    d.messages.push(...t.messages.filter(m => !ids.has(m.id)));
    d.messages.sort((a, b) => a.at.localeCompare(b.at));
    if ((t.resolvedAt || '') > (d.resolvedAt || '')) { d.resolved = t.resolved; d.resolvedAt = t.resolvedAt; }
    d.posted = d.posted || t.posted;
  }
  return { pr: PR, commit: SHA, threads: [...byId.values()], read: laterMap(disk.read, mine.read), checked: laterMap(disk.checked, mine.checked), approval: disk.approval || mine.approval };
}
let saving = Promise.resolve();
function persist() {
  saving = saving.then(async () => {
    if (!online) { renderStore('Not saved: the review helper is not connected.'); return; }
    try { state = merge(await api('PUT', { ...state, commit: SHA }), state); renderStore(); }
    catch (e) { if (!e.status) online = false; renderStore('Could not save: ' + e.message + '.'); }
  });
  return saving;
}
async function postThread(t, messageId) {
  postState[t.id] = { busy: true }; renderThreads();
  await persist();
  try {
    const r = await fetch('/api/post/' + D.slug, {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threadId: t.id, messageId }),
    });
    const res = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(res.error || 'the helper replied ' + r.status);
    state = merge(res.state, state);
    delete postState[t.id];
  } catch (e) { postState[t.id] = { error: 'Not posted: ' + e.message }; }
  renderThreads();
}
async function reload() {
  if (!served) { renderStore(); return; }
  try {
    const next = merge(await api('GET'), state);
    const changed = JSON.stringify(next) !== JSON.stringify(state);
    state = next; online = true;
    if (changed) renderAll();
    if (!viewedCollapsed) { viewedCollapsed = true; for (const i of D.order) if (isRead(i)) setCollapsed(i, true); }
    renderStore();
  }
  catch (e) { online = false; renderStore('Not connected: ' + e.message + '.'); }
}
function renderStore(msg) {
  const box = $('#store');
  box.textContent = '';
  box.classList.toggle('ok', online);
  if (!served) box.append(el('span', null, 'This page was opened as a file, so nothing is saved. Open the queue with review.py.'));
  else if (online && !msg) box.append(el('span', 'hint', 'Saved automatically.'));
  if (msg) box.append(el('span', 'hint warn', msg));
}
