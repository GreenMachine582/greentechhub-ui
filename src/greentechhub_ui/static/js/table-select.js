// gth-data-table bulk selection — see gth_data_table(bulk_actions=...) in
// components/table.html (v0.11).
// Each [data-gth-table-select] wrapper's selection is a Set of row values
// kept in memory by table id, so it survives every swap of the wrapper
// (sort, pager, page size, refresh_event) and load-more appends; it's
// cleared when data-gth-filter-key changes (a filter now hides rows), after
// a bulk action succeeds, by "Clear selection" and by Esc. Bulk-bar buttons
// post the whole Set (rows on other pages too) as data-name, repeated.
(function () {
  var tables = new Map();  // table id -> {ids: Set, filterKey, last}

  function state(root) {
    var key = root.getAttribute("data-gth-filter-key") || "";
    var s = tables.get(root.id);
    if (!s) {
      s = { ids: new Set(), filterKey: key, last: null };
      tables.set(root.id, s);
    } else if (s.filterKey !== key) {
      s.ids.clear();
      s.filterKey = key;
      s.last = null;
    }
    return s;
  }

  function boxes(root) {
    // Own rows only — not those of a table nested in a row.
    return Array.prototype.filter.call(root.querySelectorAll("[data-gth-select]"), function (b) {
      return b.closest("[data-gth-table-select]") === root;
    });
  }

  function sync(root) {
    var s = state(root);
    var shown = boxes(root);
    var shownOn = 0;
    shown.forEach(function (b) {
      var on = s.ids.has(b.value);
      b.checked = on;
      if (on) shownOn++;
      var tr = b.closest("tr");
      if (tr) tr.classList.toggle("table-active", on);
    });
    var all = root.querySelector("[data-gth-select-all]");
    if (all) {
      all.checked = shown.length > 0 && shownOn === shown.length;
      all.indeterminate = shownOn > 0 && shownOn < shown.length;
      all.disabled = shown.length === 0;
    }
    var bar = root.querySelector("[data-gth-bulk]");
    if (!bar) return;
    var n = s.ids.size;
    var hidden = n - shownOn;
    var text = n ? n + " selected" + (hidden ? " (" + hidden + " on other pages)" : "") : "";
    bar.hidden = n === 0;
    var count = bar.querySelector(".gth-table-bulk-count");
    if (count) count.textContent = text;
    // Announce changes only: not on page load, nor the same count again after
    // a swap re-rendered the (empty) live region.
    var status = document.getElementById(root.id + "-bulk-status");
    if (!status) return;
    var prev = status.getAttribute("data-text");
    status.setAttribute("data-text", text);
    if (prev !== null && prev !== text) status.textContent = text || "Selection cleared";
  }

  function syncWithin(scope) {
    var roots = [];
    var own = scope.closest && scope.closest("[data-gth-table-select]");
    if (own) roots.push(own);
    if (scope.querySelectorAll) {
      scope.querySelectorAll("[data-gth-table-select]").forEach(function (r) {
        if (roots.indexOf(r) === -1) roots.push(r);
      });
    }
    roots.forEach(sync);
  }

  function clear(root) {
    var s = state(root);
    s.ids.clear();
    s.last = null;
    sync(root);
  }

  document.addEventListener("click", function (evt) {
    var t = evt.target;
    if (!t.closest) return;
    var root = t.closest("[data-gth-table-select]");
    if (!root) return;
    if (t.matches("[data-gth-select-clear]")) {
      clear(root);
      var first = boxes(root)[0];
      if (first) first.focus();  // the bar (and the focused button) just hid
      return;
    }
    if (!t.matches("[data-gth-select]")) return;
    var s = state(root);
    var shown = boxes(root);
    var i = shown.indexOf(t);
    // Shift+click: give the whole range from the last clicked row this state.
    if (evt.shiftKey && s.last !== null && s.last < shown.length) {
      var lo = Math.min(s.last, i), hi = Math.max(s.last, i);
      for (var j = lo; j <= hi; j++) {
        if (t.checked) s.ids.add(shown[j].value);
        else s.ids.delete(shown[j].value);
      }
    } else if (t.checked) {
      s.ids.add(t.value);
    } else {
      s.ids.delete(t.value);
    }
    s.last = i;
    sync(root);
  });

  // Keyboard toggles (Space) arrive as click events too; select-all and any
  // programmatic change land here.
  document.addEventListener("change", function (evt) {
    var t = evt.target;
    if (!t.closest || !t.matches("[data-gth-select-all]")) return;
    var root = t.closest("[data-gth-table-select]");
    var s = state(root);
    boxes(root).forEach(function (b) {
      if (t.checked) s.ids.add(b.value);
      else s.ids.delete(b.value);
    });
    s.last = null;
    sync(root);
  });

  document.addEventListener("keydown", function (evt) {
    if (evt.key !== "Escape" || !evt.target.closest) return;
    var root = evt.target.closest("[data-gth-table-select]");
    if (!root || !state(root).ids.size) return;
    evt.preventDefault();
    clear(root);
    var active = document.activeElement;
    if (!active || active === document.body || active.closest("[data-gth-bulk]")) {
      var first = boxes(root)[0];
      if (first) first.focus();
    }
  });

  document.addEventListener("htmx:configRequest", function (evt) {
    var elt = evt.detail.elt;
    var bar = elt && elt.closest && elt.closest("[data-gth-bulk]");
    if (!bar) return;
    var root = bar.closest("[data-gth-table-select]");
    evt.detail.parameters[bar.getAttribute("data-name") || "ids"] = Array.from(state(root).ids);
  });

  document.addEventListener("htmx:afterRequest", function (evt) {
    var elt = evt.detail.elt;
    var bar = elt && elt.closest && elt.closest("[data-gth-bulk]");
    if (!bar || !evt.detail.successful) return;
    // The bar may be detached by now (a refresh_event swap), so go by id.
    var id = bar.getAttribute("data-table");
    var s = tables.get(id);
    if (s) {
      s.ids.clear();
      s.last = null;
    }
    var root = document.getElementById(id);
    if (root) sync(root);
  });

  document.addEventListener("htmx:load", function (evt) { syncWithin(evt.detail.elt); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { syncWithin(document); });
  else syncWithin(document);
})();
