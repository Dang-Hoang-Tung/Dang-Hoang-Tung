let current = null;
function computeCurrent() {
  const top = 90;
  let cur = null;
  for (const s of $$('section.file')) {
    if (s.offsetParent === null) continue;
    const r = s.getBoundingClientRect();
    if (r.top <= top && r.bottom > top) { cur = +s.dataset.f; break; }
  }
  if (cur === null) {
    const s = $$('section.file').find(x => x.offsetParent !== null && x.getBoundingClientRect().top > 0 && x.getBoundingClientRect().top < innerHeight * 0.5);
    if (s) cur = +s.dataset.f;
  }
  if (cur !== current) { current = cur; markCurrent(); }
}
function markCurrent() {
  $$('.left [data-file], .progress [data-file]').forEach(e => e.classList.toggle('current', current !== null && +e.dataset.file === current));
  const cur = $('.pane.on .current');
  if (cur) { const p = cur.closest('.tabpanes'); const r = cur.getBoundingClientRect(), pr = p.getBoundingClientRect(); if (r.top < pr.top || r.bottom > pr.bottom) cur.scrollIntoView({ block: 'nearest' }); }
}

function initScrollSpy() {
  let ticking = false;
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; computeCurrent(); }); } }, { passive: true });
  $('#focus').onchange = e => { document.body.classList.toggle('focus-only', e.target.checked); computeCurrent(); };
}
