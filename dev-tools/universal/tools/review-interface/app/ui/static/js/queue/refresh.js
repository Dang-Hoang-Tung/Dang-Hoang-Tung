const AUTO_EVERY = 15 * 60 * 1000;
const LAST_KEY = 'review-last-refresh';

function initRefresh() {
  const btn = $('#qrefresh');
  if (!btn || !location.protocol.startsWith('http')) return;
  btn.hidden = false;
  try {
    const done = JSON.parse(sessionStorage.getItem('review-refreshed') || 'null');
    sessionStorage.removeItem('review-refreshed');
    if (done) {
      const note = el('span', 'qrefreshed', done.length ? 'Updated · ' + done.map(n => '#' + n).join(', ') + ' changed' : 'Updated · nothing changed');
      btn.before(note);
    }
  } catch (e) {}
  const label = $('span', btn);
  const busy = on => { btn.disabled = on; btn.classList.toggle('busy', on); label.textContent = on ? 'Refreshing…' : 'Refresh'; };
  const call = async method => {
    const post = method === 'POST';
    const r = await fetch('/api/refresh', { method, credentials: 'same-origin', headers: post ? { 'Content-Type': 'application/json' } : {}, body: post ? '{}' : undefined });
    const s = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(s.error || 'the helper replied ' + r.status);
    return s;
  };
  const waitForBuild = async () => {
    for (;;) {
      await new Promise(done => setTimeout(done, 1500));
      const s = await call('GET');
      if (s.running) continue;
      if (s.error) throw new Error(s.error);
      try { sessionStorage.setItem('review-refreshed', JSON.stringify((s.changes && s.changes.check) || [])); } catch (e) {}
      stamp();
      location.reload();
      return;
    }
  };
  const stamp = () => { try { localStorage.setItem(LAST_KEY, String(Date.now())); } catch (e) {} };
  const last = () => { try { return +localStorage.getItem(LAST_KEY) || 0; } catch (e) { return 0; } };
  if (!last()) stamp();
  const due = () => { if (!document.hidden && !btn.disabled && Date.now() - last() >= AUTO_EVERY) { stamp(); btn.click(); } };
  setInterval(due, 30000);
  document.addEventListener('visibilitychange', due);
  btn.title = 'Refreshes on its own every 15 minutes while this page is open';
  const fail = e => { busy(false); label.textContent = 'Refresh failed'; btn.title = e.message; };
  btn.addEventListener('click', () => { busy(true); call('POST').then(waitForBuild).catch(fail); });
  call('GET').then(s => { if (s.running) { busy(true); waitForBuild().catch(fail); } }).catch(() => {});
}
