const CHAT_ID = 'chat';
const chatThread = () => state.threads.find(t => t.id === CHAT_ID);
const lastFromMe = t => { const m = t.messages[t.messages.length - 1]; return !!m && !isAi(m); };
const waitingThreads = () => state.threads.filter(t => !t.resolved && t.messages.length && lastFromMe(t));
let chatShown = 0;
function fitFabs() {
  const box = $('#chatbox');
  document.documentElement.style.setProperty('--chatbox', (box && !box.hidden ? box.offsetHeight : 0) + 'px');
}
function chatOpen() { try { return localStorage.getItem('chatOpen') === '1'; } catch (e) { return false; } }
function setChatOpen(open) {
  $('#chatbox').hidden = !open;
  $('#chattoggle').setAttribute('aria-expanded', String(open));
  try { localStorage.setItem('chatOpen', open ? '1' : '0'); } catch (e) { /* ignore */ }
  if (open) { renderChat(true); $('#chatinput').focus(); }
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
  $('#chattoggle').onclick = () => setChatOpen($('#chatbox').hidden);
  $('#chatsend').onclick = sendChat;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendChat(); }
  });
  input.addEventListener('input', () => { input.style.height = '34px'; input.style.height = Math.min(input.scrollHeight, 120) + 'px'; });
  setChatOpen(chatOpen());
  document.addEventListener('visibilitychange', () => { if (!document.hidden) watchReplies(true); });
}
