function ago(iso, opts = {}) {
  const s = (Date.now() - new Date(iso)) / 1000;
  if (s < 60) return 'just now';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  if (s < 86400) return Math.floor(s / 3600) + 'h ago';
  const d = Math.floor(s / 86400);
  if (opts.days && d <= opts.days) return d + 'd ago';
  return new Date(iso).toLocaleDateString(undefined, opts.dateFormat);
}
