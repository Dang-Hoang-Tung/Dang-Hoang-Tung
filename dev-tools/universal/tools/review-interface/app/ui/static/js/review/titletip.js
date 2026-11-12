(function () {
  var h1 = document.getElementById("prtitle");
  if (!h1) return;
  var tip = null;
  function show() {
    if (h1.scrollWidth <= h1.clientWidth) return;
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "titletip";
      tip.setAttribute("role", "tooltip");
      tip.id = "titletip";
      document.body.appendChild(tip);
    }
    tip.textContent = h1.textContent;
    tip.hidden = false;
    var r = h1.getBoundingClientRect();
    tip.style.left = Math.max(16, r.left) + "px";
    tip.style.top = r.bottom + 6 + "px";
    h1.setAttribute("aria-describedby", "titletip");
  }
  function hide() {
    if (tip) tip.hidden = true;
    h1.removeAttribute("aria-describedby");
  }
  h1.addEventListener("mouseenter", show);
  h1.addEventListener("focus", show);
  h1.addEventListener("mouseleave", hide);
  h1.addEventListener("blur", hide);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(); });
})();

// Instant tooltips for elements with data-tip, in the same style as the title's.
const tipBox = () => {
  let t = $('#metatip');
  if (!t) { t = el('div', 'titletip'); t.id = 'metatip'; t.setAttribute('role', 'tooltip'); t.hidden = true; document.body.append(t); }
  return t;
};
function showTip(target) {
  const t = tipBox(), r = target.getBoundingClientRect();
  t.textContent = target.dataset.tip;
  t.hidden = false;
  t.style.left = Math.max(16, Math.min(r.left, innerWidth - t.offsetWidth - 16)) + 'px';
  t.style.top = r.bottom + 6 + 'px';
}
function hideTip() { const t = $('#metatip'); if (t) t.hidden = true; }
function initBranchCopy() {
  const over = e => { const x = e.target.closest && e.target.closest('[data-tip]'); if (x) showTip(x); };
  const out = e => { const x = e.target.closest && e.target.closest('[data-tip]'); if (x && !x.contains(e.relatedTarget)) hideTip(); };
  document.addEventListener('mouseover', over);
  document.addEventListener('focusin', over);
  document.addEventListener('mouseout', out);
  document.addEventListener('focusout', hideTip);
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.bcopy');
    if (!b) return;
    navigator.clipboard.writeText(b.dataset.copy).then(() => {
      b.classList.add('done'); b.dataset.tip = 'Copied'; showTip(b);
      setTimeout(() => { b.classList.remove('done'); b.dataset.tip = 'Copy branch name'; hideTip(); }, 1200);
    }, () => {});
  });
}
