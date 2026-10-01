// Flips data-bs-theme on <html> and persists the choice. app.html's anti-FOUC
// script applies a saved choice on load: the server's theme_mode first, then
// localStorage["gth-theme-mode"].
//
// Saving: localStorage always (the fallback, and all there is without a
// server). When the page set theme_save_url (rendered as
// <html data-gth-theme-save-url>), the choice is also POSTed there as
// theme=<light|dark> — through htmx.ajax when htmx is loaded, so the request
// carries the page's hx-headers (e.g. a CSRF token) and a failure gets the
// usual error toast; otherwise a same-origin fetch. The toggle has already
// flipped by then, so a failed save never blocks it.
//
// While the mode is "system" (data-gth-theme-mode, from theme_mode), the theme
// follows prefers-color-scheme live. A click picks an explicit light/dark.
(function () {
  var KEY = "gth-theme-mode";
  var root = document.documentElement;

  function save(mode, source) {
    try {
      localStorage.setItem(KEY, mode);
    } catch (e) {}
    var url = root.getAttribute("data-gth-theme-save-url");
    if (!url) return;
    if (window.htmx && window.htmx.ajax) {
      window.htmx.ajax("POST", url, { source: source, values: { theme: mode }, swap: "none" });
    } else if (window.fetch) {
      window.fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "theme=" + encodeURIComponent(mode),
      }).catch(function () {});
    }
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".gth-theme-toggle");
    if (!btn) return;
    var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-bs-theme", next);
    root.setAttribute("data-gth-theme-mode", next);
    save(next, btn);
  });

  if (window.matchMedia) {
    var light = window.matchMedia("(prefers-color-scheme: light)");
    var follow = function () {
      if (root.getAttribute("data-gth-theme-mode") === "system") {
        root.setAttribute("data-bs-theme", light.matches ? "light" : "dark");
      }
    };
    if (light.addEventListener) light.addEventListener("change", follow);
    else if (light.addListener) light.addListener(follow);
  }
})();
