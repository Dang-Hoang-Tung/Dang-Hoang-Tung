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
