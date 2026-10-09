// gth-loading-bar — see components/loading_bar.html and docs/components.md
// (v0.17). Counts in-flight htmx requests: each xhr is counted from
// htmx:beforeSend until its own loadend (which fires on success, error,
// abort and timeout alike, so the count can't stick). Once a request has
// been running for data-delay ms the bar shows (.is-active, creeping towards
// the end); when the count drops to zero it completes (.is-done) and fades.
(function () {
  var bar = document.querySelector("[data-gth-loading-bar]");
  if (!bar) return;
  var delay = parseInt(bar.getAttribute("data-delay"), 10);
  if (!(delay >= 0)) delay = 300;
  var inFlight = 0;
  var timer = null;
  var resetTimer = null;

  function show() {
    timer = null;
    if (inFlight === 0 || bar.classList.contains("is-active")) return;
    window.clearTimeout(resetTimer);
    bar.classList.remove("is-done");
    void bar.offsetWidth; // restart from 0 width so the creep transition runs
    bar.classList.add("is-active");
  }

  function finish() {
    window.clearTimeout(timer);
    timer = null;
    if (!bar.classList.contains("is-active")) return;
    bar.classList.remove("is-active");
    bar.classList.add("is-done");
    // After the fade, back to 0 width with no transition (.is-done gone).
    resetTimer = window.setTimeout(function () { bar.classList.remove("is-done"); }, 600);
  }

  document.addEventListener("htmx:beforeSend", function (evt) {
    var xhr = evt.detail && evt.detail.xhr;
    if (!xhr || xhr._gthLoadingBar) return;
    xhr._gthLoadingBar = true;
    inFlight++;
    if (!timer && !bar.classList.contains("is-active")) timer = window.setTimeout(show, delay);
    xhr.addEventListener("loadend", function () {
      inFlight = Math.max(0, inFlight - 1);
      if (inFlight === 0) finish();
    });
  });
})();
