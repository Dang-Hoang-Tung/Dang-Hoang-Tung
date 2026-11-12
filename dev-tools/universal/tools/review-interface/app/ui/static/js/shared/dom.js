const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
function withAvatarFallback(img, label) {
  const swap = () => img.replaceWith(el('span', img.className + ' avatar-fb', (label || '?').charAt(0).toUpperCase()));
  if (img.complete && img.naturalWidth === 0 && img.src) swap();
  else img.addEventListener('error', swap, { once: true });
  return img;
}
// Keys typed into a field are the browser's (word jumps, selection), not page shortcuts.
const typingIn = e => !!(e.target && e.target.closest && e.target.closest('input, textarea, select, [contenteditable]'));
