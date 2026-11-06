function renderRequestedTimes() {
  $$('time[data-req]').forEach(t => {
    const when = new Date(t.dateTime);
    t.textContent = 'requested ' + ago(t.dateTime, {days: 30, dateFormat: {day: 'numeric', month: 'short', year: 'numeric'}});
    t.title = when.toLocaleString();
  });
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
  renderRequestedTimes();
  initBriefButtons();
  initFilters();
}
initRefresh();
