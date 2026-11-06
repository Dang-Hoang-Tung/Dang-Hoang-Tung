function renderAll() { renderReadUI(); renderThreads(); renderApprove(); }

initFileSections();
initIntraline();
initHideWs();
initHighlight();
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
initChat();
addEventListener('focus', reload);
document.addEventListener('visibilitychange', () => { if (!document.hidden) reload(); });
renderStore();
renderAll();
computeCurrent();
reload();
