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
// Delegated from document, so it survives htmx swaps and 422 re-renders.
// Requires htmx (htmx.ajax) and nothing else.
(function () {
  var panels = new WeakMap();   // picker → its panel (wherever it now lives)
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
    var host = picker.closest(".modal") || document.body;
    if (panel.parentNode !== host) {
      // A re-rendered form (e.g. a 422) leaves the old picker's portaled
      // panel behind with the same id — drop it.
      document.querySelectorAll("[data-gth-record-picker-panel]").forEach(function (p) {
        if (p !== panel && p.id === panel.id) p.remove();
      });
      host.appendChild(panel);
    }
  }
  function position(picker) {
    var panel = panelOf(picker);
    var r = trigger(picker).getBoundingClientRect();
    var gap = 4, margin = 8;
    var below = window.innerHeight - r.bottom - gap - margin;
    var above = r.top - gap - margin;
    var placeAbove = below < 240 && above > below;
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
    position(picker);
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
    panelOf(picker).classList.add("d-none");
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
    var picker = ownerOf(t);
    if (!picker) return;
    if (evt.key === "Escape") {
      // Capture phase + stopPropagation: close the panel, not an enclosing
      // modal (Bootstrap listens on the modal element).
      evt.preventDefault();
      evt.stopPropagation();
      close(picker, true);
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
      panel.removeAttribute("data-focus-on-load");
      if (openPicker === picker) focusFirst(picker);
    } else if (openPicker === picker && (document.activeElement === document.body || !document.activeElement)) {
      // A sort/page swap removed the focused control: keep focus in the panel.
      var first = rows(picker)[0];
      if (first) first.focus();
    }
    if (openPicker === picker) position(picker);
  });

  function reposition(evt) {
    if (!openPicker) return;
    if (evt && evt.target && evt.target.nodeType === 1 && panelOf(openPicker).contains(evt.target)) return;
    position(openPicker);
  }
  window.addEventListener("resize", reposition);
  window.addEventListener("scroll", reposition, true);
})();
