const LIMITS = { left: [200, 560, 284], right: [300, 720, 392] };
function setWidth(side, px) {
  const [min, max] = LIMITS[side];
  const w = Math.round(Math.min(max, Math.max(min, px)));
  document.documentElement.style.setProperty('--' + side, w + 'px');
  return w;
}

function initResizers() {
  try { for (const side of ['left', 'right']) { const w = +localStorage.getItem('pr-review-w-' + side); if (w) setWidth(side, w); } } catch (_) {}
  $$('.resizer').forEach(r => {
    const side = r.dataset.side;
    r.addEventListener('pointerdown', e => {
      e.preventDefault();
      r.setPointerCapture(e.pointerId);
      r.classList.add('dragging'); document.body.classList.add('resizing');
      const move = ev => {
        const w = setWidth(side, side === 'left' ? ev.clientX : innerWidth - ev.clientX);
        r.dataset.w = w;
      };
      const up = () => {
        r.classList.remove('dragging'); document.body.classList.remove('resizing');
        r.removeEventListener('pointermove', move); r.removeEventListener('pointerup', up);
        try { if (r.dataset.w) localStorage.setItem('pr-review-w-' + side, r.dataset.w); } catch (_) {}
        tree.start(); if (sel) paintSel();
      };
      r.addEventListener('pointermove', move);
      r.addEventListener('pointerup', up);
    });
    r.addEventListener('dblclick', () => {
      setWidth(side, LIMITS[side][2]);
      try { localStorage.removeItem('pr-review-w-' + side); } catch (_) {}
      tree.start();
    });
  });
}
