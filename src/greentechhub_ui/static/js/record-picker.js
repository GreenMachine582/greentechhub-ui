// gth-record-picker — see components/record_picker.html and
// docs/components.md (v0.7).
//
// Markup: [data-gth-record-picker] (data-gth-record-picker-url) holding a
// trigger button, an optional clear button, hidden value/label inputs and a
// panel ([data-gth-record-picker-panel]) whose body is loaded from the url
// on first open. Pickable rows are [data-gth-pick] (gth_record_picker_row).
//
// While open the panel is moved to <body>, or to the enclosing .modal so
// Bootstrap's focus trap still counts it as inside: the consumer's panel
// content (gth_table_filter's <form>) mustn't nest inside the form the
// picker lives in, and a modal body's overflow mustn't clip it. It's
// positioned (fixed) under the trigger, or above it when there's no room.
//
// Keyboard: ↓/Enter/Space on the trigger opens; focus lands in the panel's
// search box (or first row); ↓ from the search box enters the rows; ↑/↓,
// Home/End move between rows; Enter/Space picks; Esc closes (not an
// enclosing modal) and returns focus to the trigger.
//
// Sizes: "panel" (floating under the trigger) and "modal" (centred over a
// backdrop, [data-gth-record-picker-backdrop], moved along with the panel).
// The header's [data-gth-record-picker-size] toggles between them without
// reloading; each open starts at data-gth-record-picker-size. At modal size
// Tab wraps inside the panel, and the backdrop, ✕ or Esc close it.
//
// Delegated from document, so it survives htmx swaps and 422 re-renders.
// Requires htmx (htmx.ajax) and nothing else.
(function () {
  var panels = new WeakMap();   // picker → its panel (wherever it now lives)
  var backdrops = new WeakMap(); // picker → its backdrop (moved with the panel)
  var owners = new WeakMap();   // panel → its picker
  var openPicker = null;

  function pickerOf(el) { return el && el.closest ? el.closest("[data-gth-record-picker]") : null; }
  function panelOf(picker) {
    var panel = panels.get(picker);
    if (!panel) {
      panel = picker.querySelector("[data-gth-record-picker-panel]");
      panels.set(picker, panel);
      owners.set(panel, picker);
    }
    return panel;
  }
  function backdropOf(picker) {
    var backdrop = backdrops.get(picker);
    if (!backdrop) {
      backdrop = picker.querySelector("[data-gth-record-picker-backdrop]");
      backdrops.set(picker, backdrop);
    }
    return backdrop;
  }
  function isModal(picker) {
    return panelOf(picker).classList.contains("gth-record-picker-panel--modal");
  }
  function ownerOf(el) {
    var panel = el && el.closest ? el.closest("[data-gth-record-picker-panel]") : null;
    return panel ? owners.get(panel) : null;
  }
  function q(picker, sel) { return picker.querySelector(sel); }
  function trigger(picker) { return q(picker, "[data-gth-record-picker-trigger]"); }
  function rows(picker) {
    return Array.prototype.slice.call(panelOf(picker).querySelectorAll("[data-gth-pick]"));
  }

  function portal(picker) {
    var panel = panelOf(picker);
    var backdrop = backdropOf(picker);
    var host = picker.closest(".modal") || document.body;
    if (panel.parentNode !== host) {
      // A re-rendered form (e.g. a 422) leaves the old picker's portaled
      // panel (and backdrop) behind with the same id — drop them.
      document.querySelectorAll("[data-gth-record-picker-panel]").forEach(function (p) {
        if (p !== panel && p.id === panel.id) p.remove();
      });
      document.querySelectorAll("[data-gth-record-picker-backdrop]").forEach(function (b) {
        if (b !== backdrop && b.getAttribute("data-for") === panel.id) b.remove();
      });
      if (backdrop) host.appendChild(backdrop);
      host.appendChild(panel);
    }
  }
  function setSize(picker, size) {
    var panel = panelOf(picker);
    var modal = size === "modal";
    panel.classList.toggle("gth-record-picker-panel--modal", modal);
    if (modal) panel.setAttribute("aria-modal", "true");
    else panel.removeAttribute("aria-modal");
    var backdrop = backdropOf(picker);
    if (backdrop) backdrop.classList.toggle("d-none", !modal);
    // Inside a Bootstrap modal the page is already scroll-locked.
    document.body.classList.toggle("gth-picker-modal-open", modal && !picker.closest(".modal"));
    var toggle = panel.querySelector("[data-gth-record-picker-size]");
    if (toggle) {
      toggle.setAttribute("aria-pressed", modal ? "true" : "false");
      toggle.setAttribute("aria-label", modal ? "Shrink" : "Expand");
      toggle.title = modal ? "Shrink" : "Expand";
    }
    if (modal) {
      ["top", "bottom", "left", "right", "maxHeight"].forEach(function (p) { panel.style[p] = ""; });
    } else {
      position(picker, true);
    }
  }
  // Height the panel wants with nothing capping it.
  function naturalHeight(panel) {
    var cap = panel.style.maxHeight;
    panel.style.maxHeight = "none";
    var h = panel.offsetHeight;
    panel.style.maxHeight = cap;
    return h;
  }
  // Bottom of any sticky/fixed top bar (the sidebar layout's navbar), which
  // the trigger must stay below when the page scrolls to make room.
  function topInset() {
    var bar = document.querySelector(".gth-navbar.sticky-top, .navbar.fixed-top");
    return bar ? Math.max(0, bar.getBoundingClientRect().bottom) : 0;
  }
  // A spacer at the end of <main> (inside the layout, so a sticky sidebar
  // keeps its column), letting a picker near the page end scroll the page
  // far enough to show its whole panel. Removed on close.
  function spacer() {
    var s = document.querySelector("[data-gth-picker-spacer]");
    if (!s) {
      s = document.createElement("div");
      s.setAttribute("data-gth-picker-spacer", "");
      s.setAttribute("aria-hidden", "true");
      s.style.height = "0px";
      (document.querySelector("main") || document.body).appendChild(s);
    }
    return s;
  }
  function removeSpacer() {
    var s = document.querySelector("[data-gth-picker-spacer]");
    if (s) s.remove();
  }
  // Panel size outside a modal: if the panel doesn't fit below the trigger,
  // scroll the page (growing it with the spacer when already at the end) so
  // it does — keeping the trigger itself below any sticky top bar.
  function makeRoom(picker, gap, margin) {
    var panel = panelOf(picker);
    var r = trigger(picker).getBoundingClientRect();
    var need = naturalHeight(panel) - (window.innerHeight - r.bottom - gap - margin);
    if (need <= 0) return;
    need = Math.min(need, Math.max(0, r.top - topInset() - margin));
    if (need <= 0) return;
    var doc = document.documentElement;
    var spare = doc.scrollHeight - (window.scrollY + window.innerHeight);
    if (need > spare) {
      var s = spacer();
      s.style.height = (parseFloat(s.style.height) + need - spare) + "px";
    }
    // Instant: Bootstrap's reboot makes :root scroll-behavior smooth, and a
    // smooth scroll would keep sliding the panel after it's placed.
    window.scrollBy({ top: need, behavior: "instant" });
  }

  function position(picker, room) {
    var panel = panelOf(picker);
    if (isModal(picker)) return;  // CSS centres it
    var gap = 4, margin = 8;
    var inModal = !!picker.closest(".modal");
    if (room && !inModal) makeRoom(picker, gap, margin);
    var r = trigger(picker).getBoundingClientRect();
    var below = window.innerHeight - r.bottom - gap - margin;
    var above = r.top - gap - margin;
    // Outside a modal the page makes room below (makeRoom); inside one the
    // modal's own scrolling decides, so flip above when that's roomier.
    var placeAbove = inModal && below < 240 && above > below;
    panel.style.maxHeight = Math.max(160, placeAbove ? above : below) + "px";
    if (placeAbove) {
      panel.style.top = "";
      panel.style.bottom = (window.innerHeight - r.top + gap) + "px";
    } else {
      panel.style.bottom = "";
      panel.style.top = (r.bottom + gap) + "px";
    }
    if (window.innerWidth < 576) {
      panel.style.left = margin + "px";
      panel.style.right = margin + "px";
    } else {
      panel.style.right = "";
      var width = panel.offsetWidth;
      var left = Math.min(r.left, window.innerWidth - width - margin);
      panel.style.left = Math.max(margin, left) + "px";
    }
  }
  function focusFirst(picker) {
    var panel = panelOf(picker);
    var target = panel.querySelector("input[type=search], input[type=text]") || rows(picker)[0];
    if (target) target.focus();
  }
  function markSelected(picker) {
    var value = q(picker, "[data-gth-record-picker-value]").value;
    rows(picker).forEach(function (row) {
      var on = value !== "" && row.getAttribute("data-value") === value;
      row.classList.toggle("table-active", on);
      if (on) row.setAttribute("aria-current", "true");
      else row.removeAttribute("aria-current");
    });
  }

  function open(picker) {
    if (openPicker && openPicker !== picker) close(openPicker, false);
    var panel = panelOf(picker);
    portal(picker);
    panel.classList.remove("d-none");
    trigger(picker).setAttribute("aria-expanded", "true");
    openPicker = picker;
    setSize(picker, picker.getAttribute("data-gth-record-picker-size"));
    if (!panel.hasAttribute("data-loaded")) {
      panel.setAttribute("data-loaded", "");
      panel.setAttribute("data-focus-on-load", "");
      htmx.ajax("GET", picker.getAttribute("data-gth-record-picker-url"),
        { target: panel.querySelector("[data-gth-record-picker-body]"), swap: "innerHTML" });
    } else {
      markSelected(picker);
      focusFirst(picker);
    }
  }
  function close(picker, restoreFocus) {
    removeSpacer();
    panelOf(picker).classList.add("d-none");
    if (backdropOf(picker)) backdropOf(picker).classList.add("d-none");
    document.body.classList.remove("gth-picker-modal-open");
    trigger(picker).setAttribute("aria-expanded", "false");
    if (openPicker === picker) openPicker = null;
    if (restoreFocus) trigger(picker).focus();
  }
  function setValue(picker, value, label) {
    var labelEl = q(picker, "[data-gth-record-picker-label]");
    q(picker, "[data-gth-record-picker-value]").value = value;
    q(picker, "[data-gth-record-picker-value-label]").value = value === "" ? "" : label;
    labelEl.textContent = value === "" ? labelEl.getAttribute("data-placeholder") : label;
    labelEl.classList.toggle("text-secondary", value === "");
    trigger(picker).classList.remove("is-invalid");
    var clear = q(picker, "[data-gth-record-picker-clear]");
    if (clear) clear.classList.toggle("d-none", value === "");
    q(picker, "[data-gth-record-picker-value]").dispatchEvent(new Event("change", { bubbles: true }));
  }
  function pick(picker, row) {
    setValue(picker, row.getAttribute("data-value"), row.getAttribute("data-label"));
    close(picker, true);
  }

  // A row pressed a moment before an htmx swap (e.g. a debounced search
  // landing) is gone by the time the button is released: the browser then
  // fires no click at all, or one on whatever replaced the row — possibly a
  // sort button. So remember the pressed row; on release, if it was
  // swapped out, pick it, and swallow any click that follows (capture
  // phase, so htmx on the new element never sees it).
  var pressed = null;
  var swallowClick = false;
  document.addEventListener("mousedown", function (evt) {
    var row = evt.target.closest && evt.target.closest("[data-gth-pick]");
    var owner = row && ownerOf(row);
    pressed = owner ? { picker: owner, row: row } : null;
    swallowClick = false;
  }, true);
  document.addEventListener("mouseup", function (evt) {
    var p = pressed;
    pressed = null;
    if (!p || document.contains(p.row) || openPicker !== p.picker) return;
    if (!panelOf(p.picker).contains(evt.target)) return;
    swallowClick = true;
    // Any click follows in the same task; don't let the flag outlive it and
    // eat a later (e.g. keyboard-triggered) click.
    setTimeout(function () { swallowClick = false; }, 0);
    pick(p.picker, p.row);  // reads data-value/-label off the detached row
  }, true);
  document.addEventListener("click", function (evt) {
    if (!swallowClick) return;
    swallowClick = false;
    evt.preventDefault();
    evt.stopPropagation();
  }, true);

  document.addEventListener("click", function (evt) {
    var t = evt.target;
    var trig = t.closest && t.closest("[data-gth-record-picker-trigger]");
    if (trig) {
      var p = pickerOf(trig);
      if (openPicker === p) close(p, false); else open(p);
      return;
    }
    var clear = t.closest && t.closest("[data-gth-record-picker-clear]");
    if (clear) {
      var cp = pickerOf(clear);
      setValue(cp, "", "");
      trigger(cp).focus();
      return;
    }
    var sizeBtn = t.closest && t.closest("[data-gth-record-picker-size]");
    if (sizeBtn && ownerOf(sizeBtn)) {
      var sp = ownerOf(sizeBtn);
      setSize(sp, isModal(sp) ? "panel" : "modal");
      sizeBtn.focus();
      return;
    }
    var closeBtn = t.closest && t.closest("[data-gth-record-picker-close]");
    if (closeBtn && ownerOf(closeBtn)) {
      close(ownerOf(closeBtn), true);
      return;
    }
    if (openPicker && t.matches && t.matches("[data-gth-record-picker-backdrop]")) {
      close(openPicker, true);
      return;
    }
    var row = t.closest && t.closest("[data-gth-pick]");
    var owner = row && ownerOf(row);
    if (owner) {
      pick(owner, row);
      return;
    }
    // Anywhere else outside the open picker (and its panel) closes it.
    if (openPicker && !ownerOf(t) && !openPicker.contains(t)) close(openPicker, false);
  });

  document.addEventListener("keydown", function (evt) {
    var t = evt.target;
    if (t.matches && t.matches("[data-gth-record-picker-trigger]") && evt.key === "ArrowDown") {
      evt.preventDefault();
      open(pickerOf(t));
      return;
    }
    if (evt.key === "Escape" && openPicker) {
      // An open picker takes Esc first, wherever focus is (it may still be
      // on the trigger while the panel loads). Capture phase +
      // stopPropagation: close the panel, not an enclosing modal (Bootstrap
      // listens on the modal element).
      evt.preventDefault();
      evt.stopPropagation();
      close(openPicker, true);
      return;
    }
    var picker = ownerOf(t);
    if (!picker) return;
    if (evt.key === "Tab" && isModal(picker)) {
      // Modal size: Tab / Shift+Tab wrap inside the panel.
      var focusables = Array.prototype.slice.call(panelOf(picker).querySelectorAll(
        "a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), [tabindex='0']"
      )).filter(function (el) { return el.offsetParent !== null; });
      var first = focusables[0], last = focusables[focusables.length - 1];
      if (evt.shiftKey && t === first) { evt.preventDefault(); last.focus(); }
      else if (!evt.shiftKey && t === last) { evt.preventDefault(); first.focus(); }
      return;
    }
    var all = rows(picker);
    var i = all.indexOf(t);
    if (i === -1) {
      if (evt.key === "ArrowDown" && t.matches("input") && all.length) {
        evt.preventDefault();
        all[0].focus();
      }
      return;
    }
    var next = null;
    if (evt.key === "ArrowDown") next = all[Math.min(i + 1, all.length - 1)];
    else if (evt.key === "ArrowUp") next = i === 0 ? panelOf(picker).querySelector("input[type=search]") || all[0] : all[i - 1];
    else if (evt.key === "Home") next = all[0];
    else if (evt.key === "End") next = all[all.length - 1];
    else if (evt.key === "Enter" || evt.key === " ") {
      evt.preventDefault();
      pick(picker, t);
      return;
    }
    if (next) {
      evt.preventDefault();
      next.focus();
    }
  }, true);

  document.body.addEventListener("htmx:afterSwap", function (evt) {
    var picker = ownerOf(evt.detail.target) || (openPicker && !document.body.contains(evt.detail.target) ? openPicker : null);
    if (!picker) return;
    var panel = panelOf(picker);
    markSelected(picker);
    if (panel.hasAttribute("data-focus-on-load")) {
      // Focused on htmx:afterSettle (below): until then htmx hasn't wired
      // up the new filter form, and a fast typist's first keys are lost.
    } else if (openPicker === picker && (document.activeElement === document.body || !document.activeElement)) {
      // A sort/page swap removed the focused control: keep focus in the panel.
      var first = rows(picker)[0];
      if (first) first.focus();
    }
    if (openPicker === picker) position(picker, true);  // new content: make room
  });

  document.body.addEventListener("htmx:afterSettle", function (evt) {
    var picker = ownerOf(evt.detail.target);
    if (!picker) return;
    var panel = panelOf(picker);
    if (!panel.hasAttribute("data-focus-on-load")) return;
    panel.removeAttribute("data-focus-on-load");
    if (openPicker === picker) focusFirst(picker);
  });

  function reposition(evt) {
    if (!openPicker) return;
    if (evt && evt.target && evt.target.nodeType === 1 && panelOf(openPicker).contains(evt.target)) return;
    position(openPicker);
  }
  window.addEventListener("resize", reposition);
  window.addEventListener("scroll", reposition, true);
})();
