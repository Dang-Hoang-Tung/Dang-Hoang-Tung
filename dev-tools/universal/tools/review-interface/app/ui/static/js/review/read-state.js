const readEntry = i => state.read[D.files[i].path];
const isRead = i => { const r = readEntry(i); return !!(r && r.read && r.hash === D.files[i].hash); };
const changedSinceRead = i => { const r = readEntry(i); return !!(r && r.read && r.hash !== D.files[i].hash); };
function setRead(ids, read) {
  for (const i of ids) state.read[D.files[i].path] = { read, hash: D.files[i].hash, at: now() };
  for (const i of ids) setCollapsed(i, read);
  renderReadUI(); persist();
}
const isChecked = k => !!(state.checked[k] && state.checked[k].on);
function setChecked(k, on) { state.checked[k] = { on, at: now() }; renderChecks(); persist(); }
