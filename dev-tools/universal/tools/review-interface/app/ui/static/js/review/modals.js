let treeModal, mapModal, briefModal;
function initModals() {
  treeModal = $('#treemodal'); mapModal = $('#mapmodal'); briefModal = $('#briefmodal');
  $$('dialog.modal').forEach(m => {
    $('[data-close]', m).onclick = () => m.close();
    m.addEventListener('click', e => { if (e.target === m) m.close(); });
  });
  initFabMenu();
  $('#treebtn').onclick = () => { treeModal.showModal(); tree.start(); };
  $('#mapbtn').onclick = () => { mapModal.showModal(); requestAnimationFrame(drawTreemap); };
  $('#briefbtn').onclick = () => startNav({ kind: 'brief' });
}

// "Overview": one button by the chat bar that opens AI Brief, PR comments, Code tree and Treemap.
function initFabMenu() {
  const menu = $('#fabmenu'), btn = $('#fabtoggle');
  const setOpen = open => { menu.hidden = !open; btn.setAttribute('aria-expanded', String(open)); };
  btn.onclick = () => setOpen(menu.hidden);
  menu.addEventListener('click', e => { if (e.target.closest('.fab')) setOpen(false); });
  document.addEventListener('pointerdown', e => { if (!menu.hidden && !$('#fabs').contains(e.target)) setOpen(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { setOpen(false); btn.focus(); } });
}
