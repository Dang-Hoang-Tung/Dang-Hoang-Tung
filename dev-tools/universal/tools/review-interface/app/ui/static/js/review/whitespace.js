// "Hide whitespace changes": rows the server marked quiet collapse, so a re-indented line shows once, untinted.
const WS_KEY = 'pr-review-hidews';

function applyHideWs() {
  const box = $('#hidews'), on = !!(box && box.checked);
  $$('tr.quiet.del').forEach(r => r.classList.toggle('ws-hidden', on));
  $$('tr.quiet.add').forEach(r => r.classList.toggle('ws-only', on));
}

function initHideWs() {
  const box = $('#hidews'); if (!box) return;
  try { box.checked = localStorage.getItem(WS_KEY) === '1'; } catch (_) {}
  box.onchange = () => { try { localStorage.setItem(WS_KEY, box.checked ? '1' : '0'); } catch (_) {} applyHideWs(); };
  applyHideWs();
}
