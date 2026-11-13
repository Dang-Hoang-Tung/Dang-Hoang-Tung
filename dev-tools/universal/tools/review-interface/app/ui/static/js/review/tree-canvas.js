function panZoom(box) {
  const stage = $('.stage', box);
  const shown = () => $('svg.tree:not([hidden])', stage) || $('svg', stage);
  let W, H;
  const measure = () => { const svg = shown(); W = +svg.getAttribute('width'); H = +svg.getAttribute('height'); };
  measure();
  const PAD = 16;
  let s = 1, x = PAD, y = PAD, drag = null, moved = false;
  const apply = () => { stage.style.transform = `translate(${x}px,${y}px) scale(${s})`; };
  const fit = () => {
    s = Math.min(2.5, (box.clientWidth - 2 * PAD) / W, (box.clientHeight - 2 * PAD) / H);
    x = (box.clientWidth - W * s) / 2; y = (box.clientHeight - H * s) / 2; apply();
  };
  const start = () => { s = 0.9; x = PAD; y = PAD; apply(); };
  const zoomAt = (f, cx, cy) => { const ns = Math.min(2.5, Math.max(0.15, s * f)); x = cx - ((cx - x) * ns) / s; y = cy - ((cy - y) * ns) / s; s = ns; apply(); };
  box.addEventListener('wheel', e => {
    // On the page the wheel scrolls the page; it pans the tree only in the modal (or zooms with ⌘/Ctrl).
    if (!box.closest('dialog') && !(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) { const r = box.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY / 200), e.clientX - r.left, e.clientY - r.top); return; }
    x -= e.deltaX; y -= e.deltaY; apply();
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
  return { fit, start, measure, zoom: f => zoomAt(f, box.clientWidth / 2, box.clientHeight / 2) };
}

let tree;
function bindTreeLinks(root, after) {
  $$('a.tlink', root).forEach(a => {
    const go = () => { if (after) after(); goToFile(+a.dataset.file); };
    a.addEventListener('click', go);
    a.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
  });
}
const COLLAPSE_KEY = 'pr-review-tree-collapse';
function showTreeMode(collapsed) {
  $$('#treecanvas svg.tree[data-mode]').forEach(s => s.toggleAttribute('hidden', s.dataset.mode !== (collapsed ? 'collapsed' : 'full')));
}
function initTreeCanvas() {
  const canvas = $('#treecanvas');
  const toggles = $$('[data-treecollapse]');
  let collapsed = false;
  try { collapsed = localStorage.getItem(COLLAPSE_KEY) === '1'; } catch (_) {}
  toggles.forEach(t => {
    t.checked = collapsed;
    t.onchange = () => {
      try { localStorage.setItem(COLLAPSE_KEY, t.checked ? '1' : '0'); } catch (_) {}
      toggles.forEach(o => { o.checked = t.checked; });
      showTreeMode(t.checked); tree.measure(); tree.start();
    };
  });
  if (toggles.length) showTreeMode(collapsed);
  tree = panZoom(canvas);
  $$('[data-zoom]').forEach(b => b.onclick = () => (b.dataset.zoom === 'fit' ? tree.fit() : tree.zoom(b.dataset.zoom === 'in' ? 1.25 : 0.8)));
  bindTreeLinks(canvas, () => { if (treeModal.open) treeModal.close(); });
  requestAnimationFrame(() => tree.fit());
}
// One canvas: it lives under the description and moves into the modal while that is open.
function openTreeModal() {
  $('#treemodalbody').append($('#treecanvas'));
  treeModal.showModal();
  tree.measure(); tree.start();
}
function returnTreeCanvas() {
  $('#treehome').append($('#treecanvas'));
  tree.measure(); tree.fit();
}
