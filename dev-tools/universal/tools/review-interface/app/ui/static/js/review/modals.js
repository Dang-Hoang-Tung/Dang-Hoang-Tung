let treeModal, mapModal, briefModal;
function initModals() {
  treeModal = $('#treemodal'); mapModal = $('#mapmodal'); briefModal = $('#briefmodal');
  $$('dialog.modal').forEach(m => {
    $('[data-close]', m).onclick = () => m.close();
    m.addEventListener('click', e => { if (e.target === m) m.close(); });
  });
  $('#treebtn').onclick = () => { treeModal.showModal(); tree.start(); };
  $('#mapbtn').onclick = () => { mapModal.showModal(); requestAnimationFrame(drawTreemap); };
  $('#briefbtn').onclick = () => startNav({ kind: 'brief' });
}
