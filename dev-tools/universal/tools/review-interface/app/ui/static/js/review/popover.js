const pcard = $('#pcard');
const CARD_DELAY = 250;
const cs = { id: null, pinned: false, centred: false, timer: 0 };
function buildCard(id) {
  if (id === 'new') return draftFor ? draftCard() : null;
  const key = id.slice(2);
  if (id.startsWith('n:')) { const n = noteByKey.get(key); return n ? noteCard(n) : null; }
  const t = state.threads.find(x => x.id === key);
  return t ? threadCard(t) : null;
}
const markerFor = id => $$('.ti').find(b => b.dataset.card === id);
function paintOpen() { $$('.ti').forEach(b => b.classList.toggle('open', b.dataset.card === cs.id)); }
// The card stays between the top bar and the chat bar, 8px clear of each.
function cardBounds() {
  const bar = $('header.appbar'), chat = $('#chat');
  const lo = (bar ? bar.getBoundingClientRect().bottom : 0) + 8;
  const hi = (chat && chat.getClientRects().length ? chat.getBoundingClientRect().top : innerHeight) - 8;
  return [lo, hi];
}
function placeCard() {
  if (!cs.id || cs.centred) return;
  const m = markerFor(cs.id);
  if (!m) { closeCard(); return; }
  const [lo, hi] = cardBounds();
  pcard.style.maxHeight = Math.max(160, hi - lo) + 'px';
  const r = m.getBoundingClientRect(), w = pcard.offsetWidth, h = pcard.offsetHeight;
  const left = Math.min(Math.max(8, r.right - w), innerWidth - w - 8);
  let top = r.bottom + 6;
  if (top + h > hi) top = r.top - h - 6 >= lo ? r.top - h - 6 : hi - h;
  top = Math.max(lo, Math.min(top, hi - h));
  pcard.style.left = left + scrollX + 'px';
  pcard.style.top = top + scrollY + 'px';
}
function fillCard() {
  const c = buildCard(cs.id);
  if (!c) return false;
  pcard.replaceChildren(c);
  pcard.classList.toggle('center', cs.centred);
  if (cs.centred) { pcard.style.left = pcard.style.top = ''; }
  pcard.hidden = false;
  placeCard();
  paintOpen();
  return true;
}
function focusDraft(key) {
  const ta = $(`textarea[data-draft="${key}"]`, pcard);
  if (!ta) return;
  ta.focus({ preventScroll: true });
  const d = drafts[key];
  if (d && d.start != null) ta.setSelectionRange(d.start, d.end); else ta.setSelectionRange(ta.value.length, ta.value.length);
}
function refreshCard(refocus) {
  if (!cs.id) return;
  if (!fillCard()) { closeCard(); return; }
  if (refocus) focusDraft(refocus);
}
function openCard(id, { pinned = false, centred = false, focus = pinned } = {}) {
  clearTimeout(cs.timer);
  if (cs.id && cs.id !== id) saveDrafts();
  cs.id = id; cs.pinned = pinned; cs.centred = centred || !markerFor(id);
  if (!fillCard()) { closeCard(); return; }
  if (focus) { const ta = $('textarea', pcard); if (ta) focusDraft(ta.dataset.draft); }
}
function closeCard() {
  clearTimeout(cs.timer);
  if (!cs.id) return;
  saveDrafts();
  cs.id = null; cs.pinned = false;
  pcard.hidden = true; pcard.replaceChildren();
  paintOpen();
}
function initPopover() {
  document.addEventListener('mouseover', e => {
    if (e.target.closest('#pcard')) { clearTimeout(cs.timer); return; }
    const m = e.target.closest('.ti');
    if (m) {
      clearTimeout(cs.timer);
      if (!cs.pinned && cs.id !== m.dataset.card) openCard(m.dataset.card);
      return;
    }
    if (cs.id && !cs.pinned) { clearTimeout(cs.timer); cs.timer = setTimeout(closeCard, CARD_DELAY); }
  });
  document.addEventListener('click', e => {
    const m = e.target.closest('.ti');
    if (!m) return;
    const id = m.dataset.card;
    if (cs.id === id && cs.pinned) closeCard(); else openCard(id, { pinned: true });
  });
  document.addEventListener('pointerdown', e => {
    if (cs.id && cs.pinned && !e.target.closest('#pcard, .ti, .nrow, #cbtn, #navchip')) closeCard();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && cs.id && !$('dialog[open]')) closeCard(); });
  addEventListener('scroll', () => placeCard(), { capture: true, passive: true });
  addEventListener('resize', placeCard);
}
