const D = JSON.parse(document.getElementById('data').textContent);
const PR = D.pr, SHA = D.sha;
const AI_NAME = D.ai_name || 'AI', ME = D.user || 'You';
const isAi = m => m.who === 'ai' || m.who === 'claude';
const postState = {};
const LABEL = D.severity_labels, RANK = D.severities;
const noteByKey = new Map(D.notes.map(n => [n.key, n]));
const fileName = i => D.files[i].path.split('/').pop();
