// gth-command-palette — see components/command_palette.html (v0.8).
//
// Ctrl/⌘+K (or any [data-gth-command-open] button) opens the <dialog>.
// Nav entries come from the embedded JSON ([data-gth-command-data]) and are
// filtered here; data-gth-command-url adds debounced server results
// (gth_command_item rows, via htmx.ajax). Options are built with
// textContent, so labels can't inject HTML.
(function () {
  var DEBOUNCE_MS = 200;
  var MAX_PAGES = 50;
  var timer = null;
  var opener = null;
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

  function dialog() { return document.querySelector("[data-gth-command]"); }
  function part(d, sel) { return d.querySelector(sel); }
  function entries(d) {
    if (!d._entries) {
      try { d._entries = JSON.parse(part(d, "[data-gth-command-data]").textContent); }
      catch (e) { d._entries = []; }
    }
    return d._entries;
  }
  function options(d) {
    return Array.prototype.filter.call(d.querySelectorAll("[data-gth-command-option]"), function (o) {
      return !o.closest("[hidden]");
    });
  }
  function setActive(d, index) {
    var opts = options(d);
    opts.forEach(function (o) { o.classList.remove("active"); o.setAttribute("aria-selected", "false"); });
    var input = part(d, "[data-gth-command-input]");
    if (!opts.length) { input.removeAttribute("aria-activedescendant"); return; }
    var opt = opts[(index + opts.length) % opts.length];
    opt.classList.add("active");
    opt.setAttribute("aria-selected", "true");
    input.setAttribute("aria-activedescendant", opt.id);
    opt.scrollIntoView({ block: "nearest" });
  }
  function activeIndex(d) {
    return options(d).findIndex(function (o) { return o.classList.contains("active"); });
  }

  // Rank: label starts with q, then label contains q, then path contains q.
  function rank(entry, q) {
    var label = entry.label.toLowerCase();
    if (label.indexOf(q) === 0) return 0;
    if (label.indexOf(q) !== -1) return 1;
    if ((entry.path || "").toLowerCase().indexOf(q) !== -1) return 2;
    return -1;
  }
  function renderPages(d, q) {
    var box = part(d, "[data-gth-command-page-items]");
    box.textContent = "";
    var list = entries(d).map(function (e, i) { return [rank(e, q), i, e]; })
      .filter(function (r) { return !q || r[0] !== -1; })
      .sort(function (a, b) { return q ? (a[0] - b[0]) || (a[1] - b[1]) : a[1] - b[1]; })
      .slice(0, MAX_PAGES);
    list.forEach(function (r, n) {
      var e = r[2];
      var a = document.createElement("a");
      a.className = "gth-command-item";
      a.id = d.id + "-page-" + n;
      a.href = e.url;
      a.setAttribute("role", "option");
      a.setAttribute("aria-selected", "false");
      a.setAttribute("data-gth-command-option", "");
      var icon = document.createElement("i");
      icon.className = "bi bi-" + (e.icon || "file-earmark");
      icon.setAttribute("aria-hidden", "true");
      var label = document.createElement("span");
      label.className = "gth-command-label";
      label.textContent = e.label;
      a.append(icon, label);
      if (e.path && e.path !== e.label) {
        var hint = document.createElement("span");
        hint.className = "gth-command-hint";
        hint.textContent = e.path;
        a.appendChild(hint);
      }
      box.appendChild(a);
    });
    part(d, "[data-gth-command-pages]").hidden = !list.length;
  }
  function updateEmpty(d) {
    part(d, "[data-gth-command-empty]").hidden = options(d).length > 0;
  }
  function search(d) {
    var q = part(d, "[data-gth-command-input]").value.trim();
    renderPages(d, q.toLowerCase());
    var remote = part(d, "[data-gth-command-remote]");
    clearTimeout(timer);
    if (remote) {
      if (q.length < 2) {
        remote.hidden = true;
      } else {
        var url = d.getAttribute("data-gth-command-url");
        timer = setTimeout(function () {
          htmx.ajax("GET", url + (url.indexOf("?") === -1 ? "?" : "&") + "q=" + encodeURIComponent(q),
            { target: part(d, "[data-gth-command-remote-items]"), swap: "innerHTML" });
        }, DEBOUNCE_MS);
      }
    }
    updateEmpty(d);
    setActive(d, 0);
  }

  function open() {
    var d = dialog();
    if (!d || d.open) return;
    opener = document.activeElement;
    part(d, "[data-gth-command-input]").value = "";
    search(d);
    d.showModal();
    part(d, "[data-gth-command-input]").focus();
  }
  function go(d, opt) {
    if (!opt) return;
    d.close();
    window.location.href = opt.href;
  }

  document.addEventListener("keydown", function (evt) {
    if ((evt.ctrlKey || evt.metaKey) && !evt.altKey && (evt.key === "k" || evt.key === "K")) {
      var d = dialog();
      if (!d) return;
      evt.preventDefault();
      if (d.open) d.close(); else open();
      return;
    }
    var d2 = dialog();
    if (!d2 || !d2.open || !evt.target.matches || !evt.target.matches("[data-gth-command-input]")) return;
    if (evt.key === "ArrowDown" || evt.key === "ArrowUp") {
      evt.preventDefault();
      setActive(d2, activeIndex(d2) + (evt.key === "ArrowDown" ? 1 : -1));
    } else if (evt.key === "Enter") {
      evt.preventDefault();
      go(d2, options(d2)[activeIndex(d2)]);
    }
  });

  document.addEventListener("input", function (evt) {
    if (evt.target.matches && evt.target.matches("[data-gth-command-input]")) search(dialog());
  });

  document.addEventListener("click", function (evt) {
    if (evt.target.closest && evt.target.closest("[data-gth-command-open]")) { open(); return; }
    var d = dialog();
    if (d && evt.target === d) d.close();  // the backdrop (outside the dialog box)
  });

  // Hover follows the pointer, like the arrow keys.
  document.addEventListener("mousemove", function (evt) {
    var opt = evt.target.closest && evt.target.closest("[data-gth-command-option]");
    var d = dialog();
    if (opt && d && d.open && !opt.classList.contains("active")) setActive(d, options(d).indexOf(opt));
  });

  document.body.addEventListener("htmx:afterSwap", function (evt) {
    var d = dialog();
    if (!d || !evt.detail.target.matches("[data-gth-command-remote-items]")) return;
    var remote = part(d, "[data-gth-command-remote]");
    evt.detail.target.querySelectorAll("[data-gth-command-option]").forEach(function (o, i) {
      o.id = d.id + "-result-" + i;
    });
    remote.hidden = !evt.detail.target.querySelector("[data-gth-command-option]");
    var keep = activeIndex(d);
    updateEmpty(d);
    setActive(d, keep < 0 ? 0 : keep);
  });

  document.addEventListener("close", function (evt) {
    if (evt.target.matches && evt.target.matches("[data-gth-command]") && opener && opener.focus) {
      opener.focus();
      opener = null;
    }
  }, true);

  function init() {
    if (!isMac) return;
    document.querySelectorAll("[data-gth-command-open] kbd").forEach(function (k) { k.textContent = "⌘K"; });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
