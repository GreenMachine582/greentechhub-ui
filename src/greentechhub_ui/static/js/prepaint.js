// gth pre-paint — app.html loads this synchronously in <head> (prepaint_js_url,
// v0.17), so it runs before the body is painted, like the inline scripts it
// replaces (a strict Content-Security-Policy blocks inline script without a
// nonce). The script tag's data attributes say what to do:
//
// data-sidebar (layout="sidebar"): gth_sidebar's icon rail
//   (gth_sidebar_rail_toggle). This browser's own toggle ("rail"/"full" in
//   localStorage) wins; with none, the value — the viewer's
//   ui.sidebar_default, "rail" or "expanded" (v0.12) — decides.
// data-banners (alert_banner_js_url set): hide gth_alert_banners this browser
//   dismissed (alert-banner.js reveals any whose message has since changed).
//   The rule goes in through CSSOM (a constructed stylesheet), which CSP's
//   style-src doesn't restrict, falling back to a <style> carrying this
//   script's nonce.
(function () {
  var script = document.currentScript;
  if (!script) return;
  var root = document.documentElement;

  if (script.hasAttribute("data-sidebar")) {
    var preferred = script.getAttribute("data-sidebar");
    var stored = null;
    try { stored = localStorage.getItem("gth-sidebar-mode"); } catch (e) {}
    if (stored === "rail" || (stored !== "full" && preferred === "rail")) {
      root.setAttribute("data-gth-sidebar", "rail");
    }
  }

  if (script.hasAttribute("data-banners")) {
    var rules = [];
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var key = localStorage.key(i);
        if (key && key.indexOf("gth-banner:") === 0 && window.CSS && CSS.escape) {
          rules.push('.gth-alert-banner[data-gth-banner="' + CSS.escape(key.slice(11)) +
            '"]:not([data-gth-banner-current])');
        }
      }
    } catch (e) {}
    if (!rules.length) return;
    var css = rules.join(",") + "{display:none!important}";
    try {
      var sheet = new CSSStyleSheet();
      sheet.replaceSync(css);
      document.adoptedStyleSheets = document.adoptedStyleSheets.concat([sheet]);
    } catch (e) {
      var style = document.createElement("style");
      if (script.nonce) style.nonce = script.nonce;
      style.textContent = css;
      document.head.appendChild(style);
    }
  }
})();
