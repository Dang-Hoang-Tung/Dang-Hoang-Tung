function squarify(items, x, y, w, h) {
  const out = [], total = items.reduce((s, i) => s + i.v, 0);
  const scale = (w * h) / total;
  let rest = items.map(i => ({ ...i, area: i.v * scale }));
  const ratio = (row, side) => {
    const sum = row.reduce((s, r) => s + r.area, 0), mx = Math.max(...row.map(r => r.area)), mn = Math.min(...row.map(r => r.area));
    return Math.max((side * side * mx) / (sum * sum), (sum * sum) / (side * side * mn));
  };
  while (rest.length) {
    const side = Math.min(w, h);
    const row = [rest[0]]; let i = 1;
    while (i < rest.length && ratio([...row, rest[i]], side) <= ratio(row, side)) { row.push(rest[i]); i++; }
    rest = rest.slice(i);
    const sum = row.reduce((s, r) => s + r.area, 0);
    if (w >= h) { const cw = sum / h; let cy = y; for (const r of row) { const rh = r.area / cw; out.push({ ...r, x, y: cy, w: cw, h: rh }); cy += rh; } x += cw; w -= cw; }
    else { const rh = sum / w; let cx = x; for (const r of row) { const rw = r.area / rh; out.push({ ...r, x: cx, y, w: rw, h: rh }); cx += rw; } y += rh; h -= rh; }
  }
  return out;
}
function drawTreemap() {
  const box = $('#treemap'); box.textContent = '';
  const W = box.clientWidth, H = box.clientHeight;
  const biggest = Math.max(1, ...D.files.filter(f => !f.gen).map(f => f.a + f.d));
  const items = D.files.map(f => ({ i: f.i, v: Math.max(1, f.gen ? Math.min(f.a + f.d, biggest) : f.a + f.d) })).sort((a, b) => b.v - a.v);
  for (const r of squarify(items, 0, 0, W, H)) {
    const f = D.files[r.i];
    const b = el('button', 'tm ' + (f.gen ? 'gen' : f.kind || 'none') + (isRead(r.i) ? ' read' : ''));
    b.type = 'button';
    Object.assign(b.style, { left: r.x + 'px', top: r.y + 'px', width: r.w + 'px', height: r.h + 'px' });
    b.title = `${f.path}  +${f.a} −${f.d}`;
    if (r.w > 70 && r.h > 36) {
      const ns = f.notes.map(k => noteByKey.get(k)).filter(Boolean);
      const counts = RANK.filter(k => ns.some(n => n.kind === k)).map(k => `${ns.filter(n => n.kind === k).length} ${LABEL[k].toLowerCase()}`);
      b.append(el('span', 'tmn', f.path.split('/').pop()), el('span', 'tms', `+${f.a} −${f.d}${f.gen ? ' · generated' : ''}${counts.length ? ' · ' + counts.join(' · ') : ''}${isRead(r.i) ? ' · viewed' : ''}`));
    }
    b.onclick = () => { mapModal.close(); goToFile(r.i); };
    box.append(b);
  }
}
