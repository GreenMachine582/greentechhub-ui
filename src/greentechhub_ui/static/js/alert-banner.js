// gth-alert-banner — see components/alert_banner.html and docs/components.md
// (v0.13).
//
// [data-gth-banner-dismiss] closes its .gth-alert-banner. A banner with an
// id (data-gth-banner) remembers the dismissal in localStorage as
// "gth-banner:<id>" = a hash of its message. app.html's pre-paint script
// hides every remembered id before first paint; this file then reveals any
// of those whose message has changed since (data-gth-banner-current), so an
// edited banner shows again while an unchanged one never flashes.
(function () {
  var PREFIX = "gth-banner:";

  function messageHash(banner) {
    var el = banner.querySelector(".gth-alert-banner-message");
    var text = (el ? el.textContent : "").trim();
    var h = 0x811c9dc5; // FNV-1a, 32-bit
    for (var i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h.toString(36);
  }
  function stored(id) {
    try { return localStorage.getItem(PREFIX + id); } catch (e) { return null; }
  }

  document.querySelectorAll("[data-gth-banner]").forEach(function (banner) {
    var saved = stored(banner.getAttribute("data-gth-banner"));
    if (saved !== null && saved !== messageHash(banner)) {
      banner.setAttribute("data-gth-banner-current", "");
    }
  });

  document.addEventListener("click", function (evt) {
    var btn = evt.target.closest && evt.target.closest("[data-gth-banner-dismiss]");
    if (!btn) return;
    var banner = btn.closest(".gth-alert-banner");
    if (!banner) return;
    var id = banner.getAttribute("data-gth-banner");
    if (id) {
      try { localStorage.setItem(PREFIX + id, messageHash(banner)); } catch (e) {}
    }
    banner.remove();
  });
})();
