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
// A theme saved some other way — a settings form, say — is applied without a
// reload by the "gth:theme" event, whose detail is the mode: the server sends
// it in the save response's HX-Trigger, e.g.
// toast("Preferences saved", events={"gth:theme": "light"}). It only applies
// and stores locally; the server has already saved it.
//
// While the mode is "system" (data-gth-theme-mode), the theme follows
// prefers-color-scheme live. A click picks an explicit light/dark.
(function () {
  var KEY = "gth-theme-mode";
  var MODES = ["light", "dark", "system"];
  var root = document.documentElement;
  var light = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;

  function apply(mode) {
    if (MODES.indexOf(mode) === -1) return false;
    root.setAttribute("data-gth-theme-mode", mode);
    if (mode === "system") mode = light && light.matches ? "light" : "dark";
    root.setAttribute("data-bs-theme", mode);
    return true;
  }

  function store(mode) {
    try {
      localStorage.setItem(KEY, mode);
    } catch (e) {}
  }

  function save(mode, source) {
    store(mode);
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
    apply(next);
    save(next, btn);
  });

  // htmx dispatches an HX-Trigger event with a non-object value as
  // detail.value; a plain CustomEvent may carry the mode as detail itself.
  document.addEventListener("gth:theme", function (e) {
    var d = e.detail;
    var mode = d && typeof d === "object" ? d.value : d;
    if (apply(mode)) store(mode);
  });

  if (light) {
    var follow = function () {
      if (root.getAttribute("data-gth-theme-mode") === "system") {
        root.setAttribute("data-bs-theme", light.matches ? "light" : "dark");
      }
    };
    if (light.addEventListener) light.addEventListener("change", follow);
    else if (light.addListener) light.addListener(follow);
  }
})();
