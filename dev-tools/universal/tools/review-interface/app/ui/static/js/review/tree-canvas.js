function panZoom(box) {
  const stage = $('.stage', box), svg = $('svg', stage);
  const W = +svg.getAttribute('width'), H = +svg.getAttribute('height');
  let s = 1, x = 0, y = 0, drag = null, moved = false;
  const apply = () => { stage.style.transform = `translate(${x}px,${y}px) scale(${s})`; };
  const fit = () => {
    s = Math.min(1, (box.clientWidth - 32) / W, 520 / H);
    box.style.height = Math.min(Math.max(H * s + 32, 200), 560) + 'px';
    x = (box.clientWidth - W * s) / 2; y = 16; apply();
  };
  const start = () => {
    s = Math.max(Math.min(1, (box.clientWidth - 32) / W), 0.85);
    box.style.height = Math.min(Math.max(H * s + 32, 220), 520) + 'px';
    const root = svg.querySelector('rect.root');
    const rootX = root ? +root.getAttribute('x') + +root.getAttribute('width') / 2 : 0;
    x = W * s <= box.clientWidth ? (box.clientWidth - W * s) / 2 : Math.min(16, box.clientWidth / 2 - rootX * s); y = 16; apply();
  };
  const zoomAt = (f, cx, cy) => { const ns = Math.min(2.5, Math.max(0.15, s * f)); x = cx - ((cx - x) * ns) / s; y = cy - ((cy - y) * ns) / s; s = ns; apply(); };
  box.addEventListener('wheel', e => {
    if (e.ctrlKey || e.metaKey) { e.preventDefault(); const r = box.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY / 300), e.clientX - r.left, e.clientY - r.top); return; }
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) { e.preventDefault(); x -= e.deltaX; apply(); }
  }, { passive: false });
  box.addEventListener('pointerdown', e => { if (e.button !== 0) return; drag = { px: e.clientX, py: e.clientY, x, y }; moved = false; });
  addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.px, dy = e.clientY - drag.py;
    if (!moved && Math.hypot(dx, dy) > 4) { moved = true; box.classList.add('dragging'); }
    if (moved) { x = drag.x + dx; y = drag.y + dy; apply(); }
  });
  addEventListener('pointerup', () => { drag = null; box.classList.remove('dragging'); });
  box.addEventListener('click', e => { if (moved) { e.stopPropagation(); e.preventDefault(); moved = false; } }, true);
  return { fit, start, zoom: f => zoomAt(f, box.clientWidth / 2, box.clientHeight / 2) };
}

let tree;
function bindTreeLinks(root, after) {
  $$('a.tlink', root).forEach(a => {
    const go = () => { if (after) after(); goToFile(+a.dataset.file); };
    a.addEventListener('click', go);
    a.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
  });
}
function initTreeCanvas() {
  tree = panZoom($('#treecanvas'));
  $$('[data-zoom]').forEach(b => b.onclick = () => (b.dataset.zoom === 'fit' ? tree.fit() : tree.zoom(b.dataset.zoom === 'in' ? 1.25 : 0.8)));
  addEventListener('resize', () => tree.start());
  bindTreeLinks($('#treecanvas'));
}
