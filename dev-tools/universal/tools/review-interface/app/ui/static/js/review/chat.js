const CHAT_ID = 'chat';
const chatThread = () => state.threads.find(t => t.id === CHAT_ID);
const lastFromMe = t => { const m = t.messages[t.messages.length - 1]; return !!m && !isAi(m); };
const waitingThreads = () => state.threads.filter(t => !t.resolved && t.messages.length && lastFromMe(t));
let chatShown = 0;
function fitFabs() {
  const box = $('#chatbox');
  document.documentElement.style.setProperty('--chatbox', (box && !box.hidden ? box.offsetHeight : 0) + 'px');
}
const CHAT_MIN = 150, CHAT_DEFAULT = 250;
function chatMax() {
  const bar = $('header.appbar'), top = bar ? bar.getBoundingClientRect().bottom : 0;
  return Math.max(CHAT_MIN, (innerHeight - top) * 0.9 - $('#chatbar').offsetHeight - 16);
}
function setChatHeight(h, save) {
  const v = Math.round(Math.min(chatMax(), Math.max(CHAT_MIN, h)));
  document.documentElement.style.setProperty('--chath', v + 'px');
  if (save) try { localStorage.setItem('chatHeight', String(v)); } catch (e) { /* ignore */ }
  fitFabs();
}
function initChatGrip() {
  const grip = $('#chatgrip'), box = $('#chatbox'), chat = $('#chat');
  let saved = CHAT_DEFAULT;
  try { saved = Number(localStorage.getItem('chatHeight')) || CHAT_DEFAULT; } catch (e) { /* ignore */ }
  setChatHeight(saved, false);
  grip.addEventListener('pointerdown', e => {
    e.preventDefault();
    const startY = e.clientY, startH = box.offsetHeight;
    grip.setPointerCapture(e.pointerId);
    chat.classList.add('resizing');
    const move = ev => setChatHeight(startH + (startY - ev.clientY), false);
    const up = ev => {
      grip.removeEventListener('pointermove', move); grip.removeEventListener('pointerup', up);
      chat.classList.remove('resizing');
      setChatHeight(startH + (startY - ev.clientY), true);
    };
    grip.addEventListener('pointermove', move); grip.addEventListener('pointerup', up);
  });
  grip.addEventListener('dblclick', () => setChatHeight(CHAT_DEFAULT, true));
  addEventListener('resize', () => setChatHeight(box.offsetHeight || saved, false));
}
function chatOpen() { try { return localStorage.getItem('chatOpen') === '1'; } catch (e) { return false; } }
function setChatOpen(open) {
  $('#chatbox').hidden = !open;
  $('#chatinput').setAttribute('aria-expanded', String(open));
  try { localStorage.setItem('chatOpen', open ? '1' : '0'); } catch (e) { /* ignore */ }
  if (open) renderChat(true);
  fitFabs();
}
function renderChat(force) {
  const log = $('#chatlog'); if (!log) return;
  const t = chatThread(), msgs = t ? t.messages : [];
  const wait = !!t && lastFromMe(t);
  $('#chatwait').hidden = !wait;
  if (!force && msgs.length === chatShown) return;
  const grew = msgs.length !== chatShown || force;
  const atEnd = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  log.textContent = '';
  if (!msgs.length) log.append(el('div', 'empty', 'Ask ' + AI_NAME + ' anything about this PR.'));
  else messageList(t, log);
  chatShown = msgs.length;
  if (grew || atEnd) log.scrollTop = log.scrollHeight;
  fitFabs();
}
function sendChat() {
  const input = $('#chatinput'), text = input.value.trim();
  if (!text) return;
  const msg = { id: uid(), who: 'me', text, at: now() };
  let t = chatThread();
  if (t) t.messages.push(msg);
  else state.threads.push({ id: CHAT_ID, noteKey: null, created: now(), resolved: false, resolvedAt: null, posted: null, messages: [msg] });
  input.value = '';
  if ($('#chatbox').hidden) setChatOpen(true);
  renderThreads();
  persist();
  watchReplies(true);
}
let pollTimer = 0, lastChange = 0;
function watchReplies(fresh) {
  if (fresh) lastChange = Date.now();
  if (pollTimer || document.hidden || !served || !waitingThreads().length) return;
  if (!lastChange) lastChange = Date.now();
  pollTimer = setTimeout(pollTick, 3000);
}
async function pollTick() {
  pollTimer = 0;
  if (document.hidden || !waitingThreads().length || Date.now() - lastChange > 600000) return;
  const before = JSON.stringify(state);
  await saving;
  await reload();
  if (JSON.stringify(state) !== before) lastChange = Date.now();
  watchReplies();
}
function initChat() {
  const input = $('#chatinput');
  input.addEventListener('focus', () => { if ($('#chatbox').hidden) setChatOpen(true); });
  input.addEventListener('click', () => { if ($('#chatbox').hidden) setChatOpen(true); });
  initChatGrip();
  $('#chatclose').onclick = () => { setChatOpen(false); input.blur(); };
  $('#chatsend').onclick = sendChat;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendChat(); }
  });
  input.addEventListener('input', () => { input.style.height = '34px'; input.style.height = Math.min(input.scrollHeight, 120) + 'px'; });
  setChatOpen(chatOpen());
  document.addEventListener('visibilitychange', () => { if (!document.hidden) watchReplies(true); });
}
