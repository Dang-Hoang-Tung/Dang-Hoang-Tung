function renderTimes() {
  const fmt = { days: 30, dateFormat: { day: 'numeric', month: 'short', year: 'numeric' } };
  for (const [sel, word] of [['time[data-opened]', 'opened'], ['time[data-req]', 'requested']]) {
    $$(sel).forEach(t => {
      t.textContent = word + ' ' + ago(t.dateTime, fmt);
      t.title = word.charAt(0).toUpperCase() + word.slice(1) + ' ' + new Date(t.dateTime).toLocaleString();
    });
  }
}

function markApproved(item) {
  if (item.classList.contains('approved')) return;
  item.classList.add('approved');
  const chip = el('span', 'chip approved', '✓ Approved');
  $('.qrow', item).insertBefore(chip, $('time[data-opened]', item));
}

async function checkApprovals() {
  if (!location.protocol.startsWith('http')) return;
  await Promise.all($$('.qitem:not(.approved)').map(async item => {
    try {
      const r = await fetch('/api/state/' + item.dataset.slug, { credentials: 'same-origin' });
      if (!r.ok) return;
      const s = await r.json();
      const c = (s.approval && s.approval.commit) || '', sha = item.dataset.sha;
      if (c.length >= 7 && (c.startsWith(sha) || sha.startsWith(c))) markApproved(item);
    } catch (_) {}
  }));
}

function initBriefButtons() {
  $$('.briefbtn').forEach(b => b.addEventListener('click', e => {
    e.preventDefault(); e.stopPropagation();
    const item = b.closest('.qitem'); const open = item.classList.toggle('open');
    b.setAttribute('aria-expanded', String(open));
  }));
}

function initAvatars() {
  $$('.qbhead').forEach(h => withAvatarFallback($('img', h), $('span', h).textContent));
}

if ($('.qitem')) {
  initAvatars();
  renderTimes();
  checkApprovals();
  addEventListener('focus', checkApprovals);
  initBriefButtons();
  initFilters();
}
initRefresh();
