let drag = null, skipClick = false;
let sel = null, draftFor = null, activeThread = null, activeNote = null;
const cbtn = $('#cbtn');
const rowsOf = (a, b) => {
  const all = [...a.closest('table').rows];
  let i = all.indexOf(a), j = all.indexOf(b);
  if (i > j) [i, j] = [j, i];
  return all.slice(i, j + 1).filter(r => r.dataset.f !== undefined);
};
function describe(rows) {
  const f = +rows[0].dataset.f;
  const left = rows.every(r => r.classList.contains('del'));
  const nums = rows.map(r => +(left ? r.dataset.o : r.dataset.n)).filter(Boolean);
  return { file: f, path: D.files[f].path, side: left ? 'LEFT' : 'RIGHT', start_line: Math.min(...nums), line: Math.max(...nums), rows: rows.map(r => r.id), endRow: rows[rows.length - 1].id };
}
const span = t => (t.start_line === t.line ? `L${t.line}` : `L${t.start_line}–${t.line}`) + (t.side === 'LEFT' ? ' (old)' : '');
function paintSel() {
  $$('tr.sel').forEach(r => r.classList.remove('sel'));
  if (!sel || drag) { cbtn.hidden = true; if (!sel) return; }
  const rows = rowsOf(sel.a, sel.b);
  rows.forEach(r => r.classList.add('sel'));
  if (drag) return;
  const last = rows[rows.length - 1], rect = last.getBoundingClientRect();
  cbtn.textContent = 'Comment on ' + span(describe(rows));
  cbtn.style.top = rect.bottom + scrollY + 6 + 'px';
  cbtn.style.left = rect.left + scrollX + 110 + 'px';
  cbtn.hidden = false;
}

function initSelection() {
  document.addEventListener('pointerdown', e => {
    const num = e.target.closest('td.num');
    if (!num || num.parentElement.dataset.f === undefined || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    drag = { a: num.parentElement, moved: false };
  });
  document.addEventListener('pointermove', e => {
    if (!drag) return;
    const tr = document.elementFromPoint(e.clientX, e.clientY)?.closest('tr[data-f]');
    if (!tr || tr.closest('table') !== drag.a.closest('table')) return;
    if (tr === drag.a && !drag.moved) return;
    drag.moved = true;
    sel = { a: drag.a, b: tr };
    paintSel();
  });
  const endDrag = () => {
    if (!drag) return;
    skipClick = drag.moved;
    drag = null;
    if (skipClick) { paintSel(); setTimeout(() => { skipClick = false; }); }
  };
  document.addEventListener('pointerup', endDrag);
  document.addEventListener('pointercancel', endDrag);
  document.addEventListener('click', e => {
    if (skipClick) { skipClick = false; return; }
    const num = e.target.closest('td.num');
    if (num && num.parentElement.dataset.f !== undefined) {
      const tr = num.parentElement;
      if (e.shiftKey && sel && sel.a.closest('table') === tr.closest('table')) sel.b = tr;
      else if (sel && sel.a === tr && sel.b === tr) sel = null;
      else sel = { a: tr, b: tr };
      paintSel();
    }
    const mk = e.target.closest('button.mk');
    if (mk) openNote(mk.dataset.note);
  });
  cbtn.onclick = () => { if (sel) startDraft(describe(rowsOf(sel.a, sel.b)), null, ''); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('dialog[open]') && sel) { sel = null; paintSel(); } });
  addEventListener('resize', () => { if (sel) paintSel(); });
}
