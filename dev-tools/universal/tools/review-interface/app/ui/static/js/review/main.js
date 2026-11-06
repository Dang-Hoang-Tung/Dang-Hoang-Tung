function renderAll() { renderReadUI(); renderChecks(); renderThreads(); renderApprove(); }

initFileSections();
initHighlight();
initTabs();
initScrollSpy();
initTheme();
initResizers();
initTreeCanvas();
initModals();
initSelection();
initThreads();
initApprove();
addEventListener('focus', reload);
document.addEventListener('visibilitychange', () => { if (!document.hidden) reload(); });
renderStore();
renderAll();
tree.start();
computeCurrent();
reload();
