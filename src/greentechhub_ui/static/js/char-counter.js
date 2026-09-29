// gth-char-counter — see gth_form_field(maxlength=...) in components/form.html
// (v0.11). Keeps each [data-gth-counter-for] counter at "N / max" as its field
// changes, with .is-near from 90% and .is-full at the limit. The counter is in
// the field's aria-describedby (read on focus); screen readers are only told
// when the count crosses into the last 10% and when the limit is reached,
// through one shared polite live region — never on every keystroke.
(function () {
  var live = null;

  function announce(text) {
    if (!live) {
      live = document.createElement("div");
      live.className = "visually-hidden";
      live.id = "gth-char-counter-status";
      live.setAttribute("aria-live", "polite");
      document.body.appendChild(live);
    }
    // Clear first so the same message twice is still announced.
    live.textContent = "";
    window.setTimeout(function () { live.textContent = text; }, 50);
  }

  function counterFor(field) {
    return field.id ? document.querySelector('[data-gth-counter-for="' + field.id + '"]') : null;
  }

  function update(field, speak) {
    var counter = counterFor(field);
    var max = parseInt(field.getAttribute("maxlength"), 10);
    if (!counter || !(max > 0)) return;
    var n = field.value.length;
    var left = max - n;
    var near = n >= Math.ceil(max * 0.9);
    var full = n >= max;
    var was = counter.classList.contains("is-full") ? "full" : counter.classList.contains("is-near") ? "near" : "";
    counter.textContent = n + " / " + max;
    counter.classList.toggle("is-near", near && !full);
    counter.classList.toggle("is-full", full);
    if (!speak) return;
    if (full && was !== "full") announce("Character limit reached");
    else if (near && !full && was === "") announce(left + (left === 1 ? " character left" : " characters left"));
  }

  document.addEventListener("input", function (evt) {
    var t = evt.target;
    if (t.hasAttribute && t.hasAttribute("maxlength")) update(t, true);
  });

  function init(scope) {
    if (!scope.querySelectorAll) return;
    scope.querySelectorAll("[data-gth-counter-for]").forEach(function (counter) {
      var field = document.getElementById(counter.getAttribute("data-gth-counter-for"));
      if (field) update(field, false);
    });
  }

  document.addEventListener("htmx:load", function (evt) { init(evt.detail.elt); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(document); });
  else init(document);
})();
