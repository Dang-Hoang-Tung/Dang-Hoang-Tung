function renderAll() { renderReadUI(); renderThreads(); renderApprove(); }

initFileSections();
initIntraline();
initHideWs();
initTabs();
initScrollSpy();
initTheme();
initResizers();
initTreeCanvas();
initModals();
initSelection();
initPopover();
initNav();
initApprove();
addEventListener('focus', reload);
document.addEventListener('visibilitychange', () => { if (!document.hidden) reload(); });
renderStore();
renderAll();
tree.start();
computeCurrent();
reload();
