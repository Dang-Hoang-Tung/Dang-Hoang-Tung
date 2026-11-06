const mq = matchMedia('(prefers-color-scheme: dark)');
const effectiveTheme = () => document.documentElement.dataset.theme || 'dark';
function paintThemeBtn() { $('#themebtn').title = effectiveTheme() === 'dark' ? 'Switch to light' : 'Switch to dark'; }
let menu, paletteBtn;
function renderThemeMenu() {
  menu.textContent = '';
  menu.append(el('div', 'mtitle', 'Theme'));
  const fam = document.documentElement.dataset.family;
  for (const [key, t] of Object.entries(window.REVIEW_THEMES)) {
    const b = el('button', key === fam ? 'on' : ''); b.type = 'button';
    const sw = el('span', 'sw');
    for (const c of [t.light.bg, t.light.accent, t.dark.surface, t.dark.accent]) { const i = el('i'); i.style.background = c; sw.append(i); }
    b.append(sw, el('span', null, t.name), el('span', 'chk', key === fam ? '✓' : ''));
    b.onclick = () => { try { localStorage.setItem('pr-review-family', key); } catch (_) {} window.applyReviewTheme(); renderThemeMenu(); };
    menu.append(b);
  }
}
function initTheme() {
  menu = $('#thememenu'); paletteBtn = $('#palettebtn');
  $('#themebtn').onclick = () => {
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('pr-review-theme', next); } catch (_) {}
    window.applyReviewTheme(); paintThemeBtn(); renderThemeMenu();
  };
  mq.addEventListener('change', () => { paintThemeBtn(); renderThemeMenu(); });
  paintThemeBtn();
  paletteBtn.onclick = e => {
    e.stopPropagation();
    menu.hidden = !menu.hidden;
    paletteBtn.setAttribute('aria-expanded', String(!menu.hidden));
    if (!menu.hidden) renderThemeMenu();
  };
  document.addEventListener('click', e => { if (!menu.hidden && !e.target.closest('.picker')) { menu.hidden = true; paletteBtn.setAttribute('aria-expanded', 'false'); } });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { menu.hidden = true; paletteBtn.focus(); } });
}
