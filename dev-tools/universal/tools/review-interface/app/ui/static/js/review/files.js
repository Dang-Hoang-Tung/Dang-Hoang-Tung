const section = i => document.getElementById('f-' + i);
function setCollapsed(i, collapsed) {
  const s = section(i); if (!s) return;
  s.classList.toggle('collapsed', collapsed);
  $('.fold', s).setAttribute('aria-expanded', String(!collapsed));
}
function initFileSections() {
  $$('section.file').forEach(s => {
    const i = +s.dataset.f;
    $('.fold', s).onclick = () => setCollapsed(i, !s.classList.contains('collapsed'));
    $('.path', s).onclick = () => setCollapsed(i, !s.classList.contains('collapsed'));
    $('input[data-read]', s).onchange = e => setRead([i], e.target.checked);
  });
  $$('button.expand').forEach(b => b.onclick = () => { const t = b.previousElementSibling; t.replaceWith(t.content.cloneNode(true)); b.remove(); });
}

function goToFile(i, block = 'start') {
  const s = section(i); if (!s) return;
  setCollapsed(i, false);
  s.scrollIntoView({ block, behavior: reduced ? 'auto' : 'smooth' });
}
function goToRows(rowIds) {
  const end = rowIds.length && document.getElementById(rowIds[rowIds.length - 1]);
  if (!end) return;
  setCollapsed(+end.dataset.f, false);
  $$('tr.flash').forEach(r => r.classList.remove('flash'));
  rowIds.forEach(id => { const r = document.getElementById(id); if (r) r.classList.add('flash'); });
  end.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' });
}
