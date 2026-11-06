const FILTER_KEY = 'review-queue-filters';
const blank = {q: '', author: '', effort: '', brief: false, failing: false, nodraft: false};
let f = {...blank};
let items = [], buckets = [], authorDropdown = null;
const TOGGLE_KEYS = ['brief', 'failing', 'nodraft'];

function initFiltersMenu() {
  const root = $('#qf'), btn = $('.fbtn', root), panel = $('.fpanel', root);
  const show = open => {
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    root.classList.toggle('open', open);
  };
  btn.addEventListener('click', () => show(panel.hidden));
  document.addEventListener('mousedown', e => { if (!root.contains(e.target)) show(false); });
  root.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) { show(false); btn.focus(); } });
}

function loadFilters() {
  try { f = {...blank, ...JSON.parse(sessionStorage.getItem(FILTER_KEY) || '{}')}; } catch (e) {}
}

const active = () => f.q || f.author || f.effort || f.brief || f.failing || f.nodraft;
const matches = i => {
  const d = i.dataset;
  const q = f.q.trim().toLowerCase().replace(/^#/, '');
  return (!q || d.search.includes(q)) && (!f.author || d.author === f.author) && (!f.effort || d.effort === f.effort)
    && (!f.brief || d.brief === '1') && (!f.failing || d.ci === 'failing') && (!f.nodraft || d.draft !== '1');
};

function apply() {
  let shown = 0, mins = 0;
  items.forEach(i => { const ok = matches(i); i.hidden = !ok; if (ok) { shown++; mins += +i.dataset.min; } });
  buckets.forEach(b => {
    const n = b.querySelectorAll('.qitem:not([hidden])').length;
    b.hidden = !n;
    b.querySelector('.n').textContent = n;
  });
  $('#qsum').textContent = `Showing ${shown} of ${items.length} PRs · ~${mins} min`;
  $('#qclear').hidden = !active();
  $('#qnone').hidden = shown > 0 || !items.length;
  $('#qs').value = f.q;
  authorDropdown.set(f.author);
  $$('.seg [data-effort]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.effort === f.effort)));
  $$('[data-tog]').forEach(b => { b.checked = !!f[b.dataset.tog]; });
  const n = TOGGLE_KEYS.filter(k => f[k]).length;
  const badge = $('.fcount'); badge.textContent = n; badge.hidden = !n;
  $('#fclear').hidden = !n;
  try { sessionStorage.setItem(FILTER_KEY, JSON.stringify(f)); } catch (e) {}
}
const set = patch => { Object.assign(f, patch); apply(); };

function initFilters() {
  items = $$('.qitem');
  buckets = $$('.qbucket');
  loadFilters();
  const host = $('#qa');
  authorDropdown = createDropdown(host, {options: JSON.parse(host.dataset.options), value: f.author, placeholder: 'All authors', onChange: author => set({author})});
  $('#qs').addEventListener('input', e => set({q: e.target.value}));
  $$('.seg [data-effort]').forEach(b => b.addEventListener('click', () => set({effort: b.dataset.effort})));
  $$('[data-tog]').forEach(b => b.addEventListener('change', () => set({[b.dataset.tog]: b.checked})));
  initFiltersMenu();
  $$('.qclear:not(#fclear)').forEach(b => b.addEventListener('click', () => set({...blank})));
  $('#fclear').addEventListener('click', () => set(Object.fromEntries(TOGGLE_KEYS.map(k => [k, false]))));
  document.addEventListener('keydown', e => {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey || /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName)) return;
    e.preventDefault(); $('#qs').focus();
  });
  if (!items.some(i => i.dataset.author === f.author)) f.author = '';
  apply();
}
