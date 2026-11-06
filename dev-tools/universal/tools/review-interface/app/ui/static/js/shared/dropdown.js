const DROPDOWN_CHEVRON = '<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>';
const DROPDOWN_SEARCH_MIN = 6;
let dropdownCount = 0;

function dropdownAvatar(url, label) {
  const img = el('img', 'dd-avatar');
  img.src = url; img.alt = '';
  return withAvatarFallback(img, label);
}

function createDropdown(container, { options, value = '', placeholder = '', onChange }) {
  const id = 'dd' + ++dropdownCount;
  const searchable = options.length > DROPDOWN_SEARCH_MIN;
  let current = value, query = '', activeIndex = -1, isOpen = false;

  container.classList.add('dd');
  const button = el('button', 'dd-btn'); button.type = 'button';
  button.setAttribute('aria-haspopup', 'listbox');
  button.setAttribute('aria-expanded', 'false');
  button.setAttribute('aria-controls', id);
  const menu = el('div', 'dd-menu'); menu.hidden = true;
  const list = el('div', 'dd-list'); list.id = id; list.setAttribute('role', 'listbox');
  let search = null;
  if (searchable) {
    search = el('input', 'dd-search'); search.type = 'search'; search.placeholder = 'Filter…';
    search.setAttribute('aria-label', 'Filter options'); search.autocomplete = 'off';
    menu.append(search);
  }
  menu.append(list);
  container.append(button, menu);

  const selected = () => options.find(o => o.value === current);
  const visible = () => options.filter(o => o.label.toLowerCase().includes(query.toLowerCase()));

  function paintButton() {
    const o = selected();
    button.textContent = '';
    if (o && o.avatar) button.append(dropdownAvatar(o.avatar, o.label));
    const label = el('span', 'dd-label' + (o ? '' : ' dd-placeholder'), o ? o.label : placeholder);
    const chevron = el('span', 'dd-chev'); chevron.innerHTML = DROPDOWN_CHEVRON;
    button.append(label, chevron);
  }

  function paintOptions() {
    list.textContent = '';
    const shown = visible();
    shown.forEach((o, i) => {
      const row = el('div', 'dd-opt' + (i === activeIndex ? ' active' : '') + (o.value === current ? ' selected' : ''));
      row.id = `${id}-${i}`;
      row.setAttribute('role', 'option');
      row.setAttribute('aria-selected', String(o.value === current));
      if (o.avatar) row.append(dropdownAvatar(o.avatar, o.label));
      row.append(el('span', 'dd-label', o.label), el('span', 'dd-check', o.value === current ? '✓' : ''));
      row.onmousedown = e => e.preventDefault();
      row.onclick = () => choose(o.value);
      row.onmousemove = () => { if (activeIndex !== i) { activeIndex = i; paintOptions(); } };
      list.append(row);
    });
    if (!shown.length) list.append(el('div', 'dd-empty', 'No matches'));
    const active = list.children[activeIndex];
    button.setAttribute('aria-activedescendant', active && active.id ? active.id : '');
    if (active && active.scrollIntoView) active.scrollIntoView({ block: 'nearest' });
  }

  function open() {
    if (isOpen) return;
    isOpen = true; query = '';
    if (search) search.value = '';
    const shown = visible();
    activeIndex = Math.max(0, shown.findIndex(o => o.value === current));
    menu.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    paintOptions();
    if (search) search.focus();
  }

  function close(refocus) {
    if (!isOpen) return;
    isOpen = false;
    menu.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    button.removeAttribute('aria-activedescendant');
    if (refocus) button.focus();
  }

  function choose(v) {
    const changed = v !== current;
    current = v;
    paintButton();
    close(true);
    if (changed && onChange) onChange(v);
  }

  function move(step) {
    const n = visible().length;
    if (!n) return;
    activeIndex = (activeIndex + step + n) % n;
    paintOptions();
  }

  button.addEventListener('click', () => (isOpen ? close(false) : open()));
  container.addEventListener('keydown', e => {
    if (!isOpen) {
      if (e.target === button && ['Enter', ' ', 'ArrowDown'].includes(e.key)) { e.preventDefault(); open(); }
      return;
    }
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(true); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter' || (e.key === ' ' && e.target === button)) {
      e.preventDefault();
      const o = visible()[activeIndex];
      if (o) choose(o.value);
    }
  });
  if (search) search.addEventListener('input', () => { query = search.value; activeIndex = 0; paintOptions(); });
  document.addEventListener('click', e => { if (isOpen && !container.contains(e.target)) close(false); });

  paintButton();
  return {
    set(v) { current = v; paintButton(); if (isOpen) paintOptions(); },
    get() { return current; },
  };
}
