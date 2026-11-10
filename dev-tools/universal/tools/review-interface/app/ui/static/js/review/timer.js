// Review countdown in the top bar. Per-PR state lives in localStorage: { total, left, end, fired }.
const TIMER_KEY = 'rtimer:' + D.slug;
let timer = null, timerTick = 0;

function loadTimer() {
  const total = Number($('#timer').dataset.default) * 1000;
  try { const t = JSON.parse(localStorage.getItem(TIMER_KEY)); if (t && t.total) return t; } catch (e) {}
  return { total, left: total, end: null, fired: false };
}
function saveTimer() { try { localStorage.setItem(TIMER_KEY, JSON.stringify(timer)); } catch (e) {} }
const timerLeft = () => timer.end ? Math.max(0, timer.end - Date.now()) : timer.left;
function fmtTimer(ms) {
  const s = Math.ceil(ms / 1000);
  return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
}

function renderTimer() {
  const left = timerLeft(), running = !!timer.end, over = !running && left <= 0;
  $('#timerval').textContent = fmtTimer(left);
  const box = $('#timer');
  box.classList.toggle('running', running);
  box.classList.toggle('low', running && left <= 60000);
  box.classList.toggle('over', over);
  const play = $('#timerplay');
  play.textContent = running ? '❚❚' : '▶';
  play.title = running ? 'Pause' : 'Start';
  play.setAttribute('aria-label', running ? 'Pause timer' : 'Start timer');
  play.disabled = over;
}

function runTimer(ms, setTotal) {
  timer.left = ms;
  if (setTotal) timer.total = ms;
  timer.end = ms > 0 ? Date.now() + ms : null;
  timer.fired = false;
  $('#timeup').hidden = true;
  saveTimer(); renderTimer(); armTimer();
}
function pauseTimer() { timer.left = timerLeft(); timer.end = null; saveTimer(); renderTimer(); armTimer(); }

function finishTimer() {
  timer.left = 0; timer.end = null;
  const show = !timer.fired;
  timer.fired = true;
  saveTimer(); renderTimer(); armTimer();
  if (show) { $('#timeup').hidden = false; $('#timeup [data-add]').focus(); }
}

function armTimer() {
  clearInterval(timerTick);
  if (!timer.end) return;
  timerTick = setInterval(() => { if (timerLeft() <= 0) finishTimer(); else renderTimer(); }, 250);
}

function closeTimerPop() { $('#timerpop').hidden = true; $('#timerbtn').setAttribute('aria-expanded', 'false'); }
function openTimerPop() {
  const s = Math.ceil(timerLeft() / 1000) || Math.round(timer.total / 1000);
  $('#timermin').value = Math.floor(s / 60); $('#timersec').value = s % 60;
  $('#timerpop').hidden = false; $('#timerbtn').setAttribute('aria-expanded', 'true');
  $('#timermin').select();
}

function initTimer() {
  timer = loadTimer();
  $('#timerplay').onclick = () => (timer.end ? pauseTimer() : runTimer(timerLeft()));
  $('#timerbtn').onclick = () => ($('#timerpop').hidden ? openTimerPop() : closeTimerPop());
  $('#timerpop').onsubmit = e => {
    e.preventDefault();
    const ms = ((Number($('#timermin').value) || 0) * 60 + Math.min(59, Number($('#timersec').value) || 0)) * 1000;
    closeTimerPop();
    if (ms > 0) runTimer(ms, true);
  };
  $('#timerreset').onclick = () => {
    timer = { total: timer.total, left: timer.total, end: null, fired: false };
    $('#timeup').hidden = true; closeTimerPop(); saveTimer(); renderTimer(); armTimer();
  };
  $$('#timeup [data-add]').forEach(b => { b.onclick = () => runTimer(Number(b.dataset.add) * 60000); });
  $('#timeupclose').onclick = () => { $('#timeup').hidden = true; };
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (!$('#timerpop').hidden) closeTimerPop();
    else if (!$('#timeup').hidden) $('#timeup').hidden = true;
  });
  document.addEventListener('pointerdown', e => { if (!$('#timerpop').hidden && !$('#timer').contains(e.target)) closeTimerPop(); });
  if (timer.end && timerLeft() <= 0) finishTimer();
  else if (!timer.end && timer.left <= 0 && !timer.fired) finishTimer();
  renderTimer(); armTimer();
}
