let treeModal, mapModal;
function initModals() {
  treeModal = $('#treemodal'); mapModal = $('#mapmodal');
  $$('dialog.modal').forEach(m => {
    $('[data-close]', m).onclick = () => m.close();
    m.addEventListener('click', e => { if (e.target === m) m.close(); });
  });
  new IntersectionObserver(([e]) => { $('#treebtn').hidden = e.isIntersecting; }).observe($('#treecard'));
  $('#treebtn').onclick = () => {
    const body = $('.modal-body', treeModal);
    if (!body.firstChild) { body.append($('#treecanvas svg').cloneNode(true)); bindTreeLinks(body, () => treeModal.close()); }
    treeModal.showModal();
  };
  $('#mapbtn').onclick = () => { mapModal.showModal(); requestAnimationFrame(drawTreemap); };
}
