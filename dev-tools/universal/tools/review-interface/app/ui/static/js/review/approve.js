const approvedHere = () => !!(state.approval && state.approval.commit === D.sha);
function closeApprove() {
  $('#approvepop').hidden = true;
  $('#approvebtn').setAttribute('aria-expanded', 'false');
}
function renderApprove() {
  const wrap = $('#approvewrap'), btn = $('#approvebtn');
  wrap.hidden = !served;
  const old = $('#approved');
  if (old) old.remove();
  btn.hidden = approvedHere();
  if (!approvedHere()) return;
  closeApprove();
  const a = state.approval, label = 'Approved ✓' + (a.dry_run ? ' (dry run)' : '');
  let done;
  if (String(a.url).startsWith('https://')) { done = el('a', 'approve-btn done', label); done.href = a.url; done.target = '_blank'; done.rel = 'noopener'; }
  else { done = el('button', 'approve-btn done', label); done.type = 'button'; done.disabled = true; }
  done.id = 'approved';
  wrap.prepend(done);
}
async function submitApprove() {
  const err = $('#approveerr'), go = $('#approvego');
  err.hidden = true; go.disabled = true;
  try {
    const r = await fetch('/api/approve/' + D.slug, {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sha: D.sha, body: $('#approvetext').value.trim() }),
    });
    const res = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(res.error || 'the helper replied ' + r.status);
    state = merge(res.state, state);
    state.approval = state.approval || res.approval;
    renderApprove();
  } catch (e) { err.textContent = 'Not approved: ' + e.message; err.hidden = false; }
  go.disabled = false;
}
function initApprove() {
  const btn = $('#approvebtn'), pop = $('#approvepop');
  btn.onclick = () => {
    const open = pop.hidden;
    pop.hidden = !open; btn.setAttribute('aria-expanded', String(open));
    if (open) { $('#approveerr').hidden = true; $('#approvetext').focus(); }
  };
  $('#approvecancel').onclick = closeApprove;
  pop.onsubmit = e => { e.preventDefault(); submitApprove(); };
  $('#approvetext').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) pop.requestSubmit(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !pop.hidden) closeApprove(); });
  document.addEventListener('pointerdown', e => { if (!pop.hidden && !$('#approvewrap').contains(e.target)) closeApprove(); });
}
