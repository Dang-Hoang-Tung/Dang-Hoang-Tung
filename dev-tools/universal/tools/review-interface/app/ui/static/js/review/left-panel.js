const ringOf = i => D.files[i].kind || 'none';
function checkbox(checked, mixed, onChange, label) {
  const c = el('input', 'rd'); c.type = 'checkbox'; c.checked = checked; c.indeterminate = mixed; c.title = label;
  c.setAttribute('aria-label', label);
  c.onclick = e => e.stopPropagation();
  c.onchange = () => onChange(c.checked);
  return c;
}
function leaves(n, out = []) { if (n.file != null) out.push(n.file); n.kids.forEach(k => leaves(k, out)); return out; }

const FOLD_KEY = 'pr-review-fold-' + PR;
let folds = {};
try { folds = JSON.parse(localStorage.getItem(FOLD_KEY) || '{}'); } catch (_) {}
const isFolded = (key, dflt = false) => (key in folds ? folds[key] : dflt);
function toggleFold(key, dflt) { folds[key] = !isFolded(key, dflt); try { localStorage.setItem(FOLD_KEY, JSON.stringify(folds)); } catch (_) {} }

const FOLDER = '<svg class="fi closed" viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>'
  + '<svg class="fi open" viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v1"/><path d="M3 7v10a2 2 0 0 0 2 2h12.5a2 2 0 0 0 1.9-1.4l1.8-5.6a1.5 1.5 0 0 0-1.4-2H8.3a2 2 0 0 0-1.9 1.4L3 17"/></svg>';
const CHEVRON = '<svg class="chev" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>';

function statusIcon(i) {
  const f = D.files[i], st = (f && f.st) || 'modified';
  const s = el('span', 'fstatus');
  s.innerHTML = D.status_icons[st] || D.status_icons.modified;
  s.title = (D.status_labels[st] || 'Modified') + (st === 'renamed' && f.old ? ' from ' + f.old : '');
  return s;
}

function fileRow(i, depth, name) {
  const row = el('div', 'trow leaf' + (isRead(i) ? ' isread' : ''));
  row.style.setProperty('--d', depth);
  row.dataset.file = i;
  row.title = D.files[i].path;
  const lead = el('span', 'lead');
  lead.append(checkbox(isRead(i), false, on => setRead([i], on), 'Mark as viewed'), el('span', 'vmark', '✓'));
  row.append(lead, statusIcon(i), el('span', 'nm', name));
  if (D.files[i].kind) row.append(el('span', 'ring ' + ringOf(i)));
  if (changedSinceRead(i)) row.append(el('span', 'chg', 'changed'));
  row.onclick = () => goToFile(i);
  return row;
}

function folderRow(name, depth, files, key, dflt, label) {
  const wrap = el('div', 'tdir' + (isFolded(key, dflt) ? ' folded' : ''));
  const row = el('div', 'trow dir');
  row.style.setProperty('--d', depth);
  row.title = name;
  row.setAttribute('role', 'button');
  row.setAttribute('aria-expanded', String(!isFolded(key, dflt)));
  const icon = el('span', 'ficon'); icon.innerHTML = FOLDER;
  const done = files.filter(isRead).length;
  row.append(icon, el('span', 'nm', name), el('span', 'tcount', `${done}/${files.length}`),
    checkbox(done === files.length, done > 0 && done < files.length, on => setRead(files, on), label));
  row.onclick = () => { toggleFold(key, dflt); wrap.classList.toggle('folded', isFolded(key, dflt)); row.setAttribute('aria-expanded', String(!isFolded(key, dflt))); };
  const kids = el('div', 'tkids');
  wrap.append(row, kids);
  return { wrap, kids };
}

function renderFiles() {
  const pane = $('#pane-files'); pane.textContent = '';
  const gen = [];
  const draw = (n, depth, parent, path) => {
    const fs = leaves(n).filter(i => !D.files[i].gen);
    leaves(n).filter(i => D.files[i].gen).forEach(i => { if (!gen.includes(i)) gen.push(i); });
    if (!fs.length) return;
    if (n.file != null) { parent.append(fileRow(n.file, depth, n.name)); return; }
    const key = 'f:' + path + n.name;
    const { wrap, kids } = folderRow(n.name + '/', depth, fs, key, false, 'Mark folder as viewed');
    n.kids.forEach(k => draw(k, depth + 1, kids, path + n.name + '/'));
    parent.append(wrap);
  };
  const tops = [];
  for (const t of D.tree) {
    if (t.file == null && t.kids.length > 1 && t.kids.every(k => k.file == null)) t.kids.forEach(k => tops.push({ ...k, name: t.name + '/' + k.name }));
    else tops.push(t);
  }
  for (const top of tops) {
    const grp = el('div', 'tgroup');
    draw(top, 0, grp, '');
    if (grp.childNodes.length) pane.append(grp);
  }
  if (gen.length) {
    const grp = el('div', 'tgroup gen');
    const { wrap, kids } = folderRow(`Generated · ${gen.length} file${gen.length > 1 ? 's' : ''}`, 0, gen, 'f:__generated', true, 'Mark generated files as viewed');
    gen.forEach(i => kids.append(fileRow(i, 1, fileName(i))));
    grp.append(wrap);
    pane.append(grp);
  }
}

function renderLayers() {
  const pane = $('#pane-layers'); pane.textContent = '';
  for (const layer of D.layers) {
    const fs = D.order.filter(i => D.files[i].layer === layer);
    if (!fs.length) continue;
    const key = 'l:' + layer, dflt = layer === 'Generated';
    const g = el('div', 'lgroup' + (dflt ? ' gen' : '') + (isFolded(key, dflt) ? ' folded' : ''));
    const head = el('div', 'lhead');
    head.setAttribute('role', 'button');
    head.setAttribute('aria-expanded', String(!isFolded(key, dflt)));
    const chev = el('span', 'lchev'); chev.innerHTML = CHEVRON;
    const done = fs.filter(isRead).length;
    head.append(chev, el('span', 'lname', layer), el('span', 'lcount', `${done}/${fs.length}`),
      checkbox(done === fs.length, done > 0 && done < fs.length, on => setRead(fs, on), 'Mark layer as viewed'));
    head.onclick = () => { toggleFold(key, dflt); g.classList.toggle('folded', isFolded(key, dflt)); head.setAttribute('aria-expanded', String(!isFolded(key, dflt))); };
    const kids = el('div', 'tkids');
    fs.forEach(i => kids.append(fileRow(i, 1, fileName(i))));
    g.append(head, kids);
    pane.append(g);
  }
}

let prevDone = null;

const SPARK_COLOURS = ['var(--add)', '#ffd54a', '#ffffff', '#7ee2a8'];
function celebrate(bar, edge, big) {
  const fx = $('#pfx'); if (!fx || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const wrap = fx.parentElement;
  bar.classList.remove('bump'); wrap.classList.remove('glow'); void bar.offsetWidth;
  bar.classList.add('bump'); wrap.classList.add('glow');
  const count = big ? 40 : 16, made = [];
  for (let k = 0; k < count; k++) {
    const sp = document.createElement('i');
    sp.textContent = Math.random() < .7 ? '✦' : '•';
    const ang = big ? Math.random() * 2 * Math.PI : -Math.PI / 2 + (Math.random() - .5) * 2.8;
    const dist = (big ? 45 : 28) + Math.random() * (big ? 55 : 30);
    sp.style.left = (big ? Math.random() * wrap.offsetWidth : edge) + 'px';
    sp.style.setProperty('--dx', Math.cos(ang) * dist + 'px');
    sp.style.setProperty('--dy', Math.sin(ang) * dist + 'px');
    sp.style.setProperty('--sz', (big ? 12 : 10) + Math.random() * (big ? 12 : 8) + 'px');
    sp.style.setProperty('--c', SPARK_COLOURS[k % SPARK_COLOURS.length]);
    sp.style.setProperty('--rot', (Math.random() < .5 ? -1 : 1) * (90 + Math.random() * 270) + 'deg');
    sp.style.setProperty('--t', 1.1 + Math.random() * .7 + 's');
    sp.style.setProperty('--delay', (big ? Math.random() * .5 : .35 + Math.random() * .3) + 's');
    fx.append(sp); made.push(sp);
  }
  setTimeout(() => { made.forEach(sp => sp.remove()); bar.classList.remove('bump'); wrap.classList.remove('glow'); }, 2300);
}

function renderProgress() {
  const n = D.order.filter(isRead).length, total = D.order.length;
  const bar = $('#pbar');
  if (bar) {
    bar.style.width = total ? (100 * n) / total + '%' : '0%';
    if (prevDone !== null && n > prevDone) celebrate(bar, bar.parentElement.offsetWidth * n / total, n === total);
  }
  prevDone = n;
  renderRemaining(n, total);
}

function renderRemaining(n, total) {
  const chip = $('#leftchip'); if (!chip) return;
  const left = D.order.filter(i => !isRead(i));
  const sum = k => left.reduce((s, i) => s + D.files[i][k], 0).toLocaleString();
  $('.a', chip).textContent = '+' + sum('a');
  $('.d', chip).textContent = '−' + sum('d');
  chip.classList.toggle('done', !left.length);
  const done = total - left.length;
  $('.left-files', chip).textContent = `${done}/${total} · ${total ? Math.round(done / total * 100) : 0}%`;
}

function renderReadUI() {
  renderFiles(); renderLayers(); renderProgress();
  for (const i of D.order) {
    const s = section(i), r = isRead(i);
    $('input[data-read]', s).checked = r;
    s.classList.toggle('isread', r);
    s.classList.toggle('changed', changedSinceRead(i));
  }
  markCurrent();
}

function initTabs() {
  $$('.tab').forEach(t => t.onclick = () => {
    $$('.tab').forEach(x => { x.classList.toggle('on', x === t); x.setAttribute('aria-selected', String(x === t)); });
    $$('.pane').forEach(p => p.classList.toggle('on', p.id === 'pane-' + t.dataset.tab));
    try { localStorage.setItem('pr-review-tab', t.dataset.tab); } catch (_) {}
  });
  try { const t = localStorage.getItem('pr-review-tab'); if (t) { const b = $(`.tab[data-tab="${t}"]`); if (b) b.click(); } } catch (_) {}
}
