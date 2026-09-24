// gth-back-to-top — see components/back_to_top.html (v0.8).
// Shown past the button's data-threshold px of window scroll (a passive,
// rAF-throttled listener); a click scrolls to the top (smooth, or instant
// under prefers-reduced-motion) and moves focus to <main>. While shown,
// <html> carries .gth-back-to-top-shown so the toast stack lifts above it.
(function () {
  var ticking = false;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  function button() { return document.querySelector("[data-gth-back-to-top]"); }
  function update() {
    ticking = false;
    var b = button();
    if (!b) return;
    var threshold = parseInt(b.getAttribute("data-threshold"), 10) || 400;
    var show = window.scrollY > threshold;
    b.hidden = !show;
    document.documentElement.classList.toggle("gth-back-to-top-shown", show);
  }

  window.addEventListener("scroll", function () {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(update);
    }
  }, { passive: true });

  document.addEventListener("click", function (evt) {
    if (!(evt.target.closest && evt.target.closest("[data-gth-back-to-top]"))) return;
    window.scrollTo({ top: 0, behavior: reduce.matches ? "auto" : "smooth" });
    // Focus the page's main content (not the button, which is about to hide)
    // without cutting the smooth scroll short.
    var main = document.querySelector("main");
    if (main) {
      if (!main.hasAttribute("tabindex")) main.setAttribute("tabindex", "-1");
      main.focus({ preventScroll: true });
    }
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", update);
  else update();
})();
