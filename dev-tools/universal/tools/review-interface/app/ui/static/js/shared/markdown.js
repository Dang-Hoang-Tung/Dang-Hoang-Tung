const escHtml = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function md(text) {
  const inline = t => escHtml(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  const out = []; let list = null;
  for (const raw of text.split('\n')) {
    const line = raw.trim(); if (!line) continue;
    const m = line.match(/^(?:[-*]|\d+\.|\([a-z]\))\s+(.*)$/);
    if (m) { if (!list) { list = []; out.push(list); } list.push(m[1]); }
    else { list = null; out.push(line); }
  }
  return out.map(b => Array.isArray(b) ? '<ul>' + b.map(i => '<li>' + inline(i) + '</li>').join('') + '</ul>' : '<p>' + inline(b) + '</p>').join('');
}
