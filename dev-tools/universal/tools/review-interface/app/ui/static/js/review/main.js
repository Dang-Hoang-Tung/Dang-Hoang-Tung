function renderAll() { renderReadUI(); renderChecks(); renderThreads(); }

initFileSections();
initTabs();
initScrollSpy();
initTheme();
initResizers();
initTreeCanvas();
initModals();
initSelection();
initThreads();
addEventListener('focus', reload);
document.addEventListener('visibilitychange', () => { if (!document.hidden) reload(); });
renderStore();
renderAll();
tree.start();
computeCurrent();
reload();
