// Theme families: each has a light and a dark palette of base colours. Every tint (surfaces, lines, soft fills,
// diff backgrounds) is derived from these in tokens.css, so a family only needs to name its core colours.
window.REVIEW_THEMES = {
  graphite: { name: 'Graphite',
    light: { bg: '#f6f7f9', surface: '#ffffff', text: '#161b26', accent: '#2f6bff', 'accent-fg': '#ffffff', add: '#1a7f37', del: '#cf2e2e', block: '#d1242f', should: '#bf6a02', nit: '#6e56cf', look: '#0a8577', question: '#bf3989', soft: '10%', shadow: 'rgba(16,24,40,.06)' },
    dark: { bg: '#0b0e13', surface: '#11151c', text: '#e4e8ef', accent: '#7aa3ff', 'accent-fg': '#0b0e13', add: '#4cc77a', del: '#f26d68', block: '#ff6e62', should: '#f0a443', nit: '#a998ff', look: '#46d0bb', question: '#f383c6', soft: '16%', shadow: 'rgba(0,0,0,.4)' } },
  github: { name: 'GitHub',
    light: { bg: '#f6f8fa', surface: '#ffffff', text: '#1f2328', accent: '#0969da', 'accent-fg': '#ffffff', add: '#1a7f37', del: '#cf222e', block: '#cf222e', should: '#9a6700', nit: '#8250df', look: '#1b7c83', question: '#bf3989', soft: '10%', shadow: 'rgba(31,35,40,.06)' },
    dark: { bg: '#010409', surface: '#0d1117', text: '#e6edf3', accent: '#4493f8', 'accent-fg': '#ffffff', add: '#3fb950', del: '#f85149', block: '#f85149', should: '#d29922', nit: '#ab7df8', look: '#39c5cf', question: '#db61a2', soft: '15%', shadow: 'rgba(1,4,9,.5)' } },
  minimal: { name: 'Minimal',
    light: { bg: '#fafafa', surface: '#ffffff', text: '#202020', accent: '#705dcf', 'accent-fg': '#ffffff', add: '#2f8a4c', del: '#c24848', block: '#c24848', should: '#a8741a', nit: '#705dcf', look: '#2b8279', question: '#a84e82', soft: '8%', shadow: 'rgba(0,0,0,.04)' },
    dark: { bg: '#1a1a1a', surface: '#202020', text: '#dcdcdc', accent: '#a28ae5', 'accent-fg': '#1a1a1a', add: '#6cbf84', del: '#e06c6c', block: '#e06c6c', should: '#d9ab5c', nit: '#a28ae5', look: '#5fb5aa', question: '#d585b3', soft: '13%', shadow: 'rgba(0,0,0,.35)' } },
  vitesse: { name: 'Vitesse',
    light: { bg: '#f7f7f5', surface: '#ffffff', text: '#393a34', accent: '#1c6b48', 'accent-fg': '#ffffff', add: '#1e754f', del: '#ab5959', block: '#ab5959', should: '#a65e2b', nit: '#7a5ac8', look: '#2f798a', question: '#b05a78', soft: '9%', shadow: 'rgba(0,0,0,.05)' },
    dark: { bg: '#121212', surface: '#181818', text: '#dbd7ca', accent: '#4d9375', 'accent-fg': '#121212', add: '#4d9375', del: '#cb7676', block: '#cb7676', should: '#d4976c', nit: '#a990d6', look: '#5eaab5', question: '#d9739f', soft: '14%', shadow: 'rgba(0,0,0,.4)' } },
  catppuccin: { name: 'Catppuccin',
    light: { bg: '#e6e9ef', surface: '#eff1f5', text: '#4c4f69', accent: '#1e66f5', 'accent-fg': '#eff1f5', add: '#40a02b', del: '#d20f39', block: '#d20f39', should: '#df8e1d', nit: '#8839ef', look: '#179299', question: '#ea76cb', soft: '12%', shadow: 'rgba(76,79,105,.08)' },
    dark: { bg: '#181825', surface: '#1e1e2e', text: '#cdd6f4', accent: '#89b4fa', 'accent-fg': '#1e1e2e', add: '#a6e3a1', del: '#f38ba8', block: '#f38ba8', should: '#fab387', nit: '#cba6f7', look: '#94e2d5', question: '#f5c2e7', soft: '15%', shadow: 'rgba(0,0,0,.35)' } },
  rosepine: { name: 'Rosé Pine',
    light: { bg: '#f2e9e1', surface: '#fffaf3', text: '#575279', accent: '#907aa9', 'accent-fg': '#fffaf3', add: '#3e8f8c', del: '#b4637a', block: '#b4637a', should: '#d7932d', nit: '#907aa9', look: '#286983', question: '#d7827e', soft: '12%', shadow: 'rgba(87,82,121,.07)' },
    dark: { bg: '#191724', surface: '#1f1d2e', text: '#e0def4', accent: '#c4a7e7', 'accent-fg': '#191724', add: '#9ccfd8', del: '#eb6f92', block: '#eb6f92', should: '#f6c177', nit: '#c4a7e7', look: '#3e8fb0', question: '#ebbcba', soft: '15%', shadow: 'rgba(0,0,0,.35)' } },
  nord: { name: 'Nord',
    light: { bg: '#e5e9f0', surface: '#eceff4', text: '#2e3440', accent: '#5e81ac', 'accent-fg': '#eceff4', add: '#5b8a47', del: '#bf616a', block: '#bf616a', should: '#b9852f', nit: '#8f6b9b', look: '#4f8b8a', question: '#b06a8f', soft: '13%', shadow: 'rgba(46,52,64,.07)' },
    dark: { bg: '#242933', surface: '#2e3440', text: '#eceff4', accent: '#88c0d0', 'accent-fg': '#2e3440', add: '#a3be8c', del: '#bf616a', block: '#bf616a', should: '#ebcb8b', nit: '#b48ead', look: '#8fbcbb', question: '#d08770', soft: '17%', shadow: 'rgba(0,0,0,.3)' } },
  tokyonight: { name: 'Tokyo Night',
    light: { bg: '#e1e2e7', surface: '#eaebef', text: '#3760bf', accent: '#2e7de9', 'accent-fg': '#ffffff', add: '#587539', del: '#f52a65', block: '#f52a65', should: '#8c6c3e', nit: '#9854f1', look: '#118c74', question: '#b15c00', soft: '12%', shadow: 'rgba(55,96,191,.08)' },
    dark: { bg: '#16161e', surface: '#1a1b26', text: '#c0caf5', accent: '#7aa2f7', 'accent-fg': '#16161e', add: '#9ece6a', del: '#f7768e', block: '#f7768e', should: '#e0af68', nit: '#bb9af7', look: '#73daca', question: '#ff9e64', soft: '15%', shadow: 'rgba(0,0,0,.4)' } },
};

window.applyReviewTheme = function () {
  const d = document.documentElement;
  let fam = null;
  try { fam = localStorage.getItem('pr-review-family'); } catch (_) {}
  if (!window.REVIEW_THEMES[fam]) fam = 'graphite';
  const mode = d.dataset.theme || 'dark';
  const p = window.REVIEW_THEMES[fam][mode];
  for (const k in p) d.style.setProperty('--' + k, p[k]);
  d.style.colorScheme = mode;
  d.dataset.family = fam;
  d.classList.toggle('is-dark', mode === 'dark');
};
try { const t = localStorage.getItem('pr-review-theme'); if (t) document.documentElement.dataset.theme = t; } catch (_) {}
window.applyReviewTheme();
