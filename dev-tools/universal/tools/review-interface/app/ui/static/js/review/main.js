function renderAll() { renderReadUI(); renderThreads(); renderApprove(); }

initFileSections();
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
initTimer();
initFullView();
initComments();
initChat();
addEventListener('focus', reload);
document.addEventListener('visibilitychange', () => { if (!document.hidden) reload();
syncGithub();
setInterval(syncGithub, 60000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) syncGithub(); }); });
renderStore();
renderAll();
computeCurrent();
reload();
