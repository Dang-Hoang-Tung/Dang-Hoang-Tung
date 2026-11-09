const section = i => document.getElementById('f-' + i);
function setCollapsed(i, collapsed) {
  const s = section(i); if (!s) return;
  s.classList.toggle('collapsed', collapsed);
  $('.fold', s).setAttribute('aria-expanded', String(!collapsed));
}
// If the file's top has scrolled under the top bar, collapsing it would jump the page; keep its header just under the bar.
function keepHeaderInView(i, change) {
  const s = section(i), bar = $('header.appbar').getBoundingClientRect().bottom;
  const above = s.getBoundingClientRect().top < bar;
  change();
  if (above && s.classList.contains('collapsed')) scrollTo({ top: scrollY + s.getBoundingClientRect().top - bar, behavior: 'instant' });
}
function initFileSections() {
  $$('section.file').forEach(s => {
    const i = +s.dataset.f;
    const toggle = () => keepHeaderInView(i, () => setCollapsed(i, !s.classList.contains('collapsed')));
    $('.fold', s).onclick = toggle;
    $('.path', s).onclick = toggle;
    $('input[data-read]', s).onchange = e => keepHeaderInView(i, () => setRead([i], e.target.checked));
  });
  $$('button.expand').forEach(b => b.onclick = () => {
    const t = b.previousElementSibling, s = b.closest('section.file');
    t.replaceWith(t.content.cloneNode(true)); b.remove();
    applyHideWs(); renderThreads(); highlightSection(s);
  });
}

function goToFile(i, block = 'start') {
  const s = section(i); if (!s) return;
  setCollapsed(i, false);
  s.scrollIntoView({ block, behavior: reduced ? 'auto' : 'smooth' });
}
function goToRows(rowIds, instant) {
  const end = rowIds.length && document.getElementById(rowIds[rowIds.length - 1]);
  if (!end) return;
  setCollapsed(+end.dataset.f, false);
  $$('tr.flash').forEach(r => r.classList.remove('flash'));
  rowIds.forEach(id => { const r = document.getElementById(id); if (r) r.classList.add('flash'); });
  end.scrollIntoView({ block: 'center', behavior: reduced || instant ? 'auto' : 'smooth' });
}
function goToMoved(btn) {
  const id = btn.dataset.target;
  setCollapsed(+btn.dataset.file, false);
  if (!document.getElementById(id)) { goToFile(+btn.dataset.file); return; }
  goToRows([id]);
  setTimeout(() => { const r = document.getElementById(id); if (r) r.classList.remove('flash'); }, 1600);
}
document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('button.mvlabel[data-target]'); if (b) goToMoved(b); });
