// gth-embed-card — see components/embed_card.html and docs/components.md
// (v0.17). Each [data-gth-embed] box loads its iframe once it scrolls into
// view (so an off-screen frame can't time out), with the page's theme added
// as data-gth-embed-theme-param, and reloads it when <html data-bs-theme>
// changes. data-gth-embed-state is "loading" until the frame's load event,
// then "loaded"; still loading after data-gth-embed-timeout ms, it's
// "error" and the error message shows (a late load still clears it).
(function () {
  function theme() {
    return document.documentElement.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";
  }

  function themedSrc(box) {
    var src = box.getAttribute("data-gth-embed-src");
    var param = box.getAttribute("data-gth-embed-theme-param");
    if (!param) return src;
    try {
      var url = new URL(src, document.baseURI);
      url.searchParams.set(param, theme());
      return url.toString();
    } catch (e) {
      return src;
    }
  }

  function load(box) {
    var frame = box.querySelector("iframe.gth-embed-card-frame");
    var error = box.querySelector(".gth-embed-card-error");
    var src = themedSrc(box);
    if (!frame || frame.getAttribute("src") === src) return;
    var timeout = parseInt(box.getAttribute("data-gth-embed-timeout"), 10) || 15000;
    window.clearTimeout(box._gthEmbedTimer);
    box.setAttribute("data-gth-embed-state", "loading");
    if (error) error.hidden = true;
    box._gthEmbedTimer = window.setTimeout(function () {
      if (box.getAttribute("data-gth-embed-state") !== "loading") return;
      box.setAttribute("data-gth-embed-state", "error");
      if (error) error.hidden = false;
    }, timeout);
    frame.onload = function () {
      window.clearTimeout(box._gthEmbedTimer);
      box.setAttribute("data-gth-embed-state", "loaded");
      if (error) error.hidden = true;
    };
    frame.hidden = false;
    frame.setAttribute("src", src);
  }

  var observer = "IntersectionObserver" in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      load(entry.target);
    });
  }, { rootMargin: "200px" }) : null;

  function init(scope) {
    if (!scope.querySelectorAll) return;
    var boxes = scope.matches && scope.matches("[data-gth-embed]") ? [scope] : [];
    boxes.concat([].slice.call(scope.querySelectorAll("[data-gth-embed]"))).forEach(function (box) {
      if (box._gthEmbedSeen) return;
      box._gthEmbedSeen = true;
      if (observer) observer.observe(box);
      else load(box);
    });
  }

  // A theme change reloads every frame that has started loading.
  new MutationObserver(function () {
    document.querySelectorAll("[data-gth-embed][data-gth-embed-state]").forEach(load);
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-bs-theme"] });

  document.addEventListener("htmx:load", function (evt) { init(evt.detail.elt); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(document); });
  else init(document);
})();
