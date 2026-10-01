// gth-data-table view options — see gth_data_table(view_options=True) in
// components/table.html (v0.11).
// Each [data-gth-table-view] wrapper's hidden columns and density live in
// localStorage["gth-table-view:<pathname>#<table id>"] as {hidden: [keys],
// density}; with nothing stored, headers marked data-default-hidden start
// hidden. Columns are matched by <th data-gth-col> index and hidden with
// .gth-col-hidden on the header and on that cell of every body row (rows
// with a colspan cell — the empty state, load-more rows — are left alone).
// Re-applied on every htmx:load, so wrapper swaps and appended rows keep the
// view. At least one column always stays shown.
(function () {
  function storageKey(root) { return "gth-table-view:" + location.pathname + "#" + root.id; }
  function load(root) {
    try {
      var v = JSON.parse(localStorage.getItem(storageKey(root)));
      return v && Array.isArray(v.hidden) ? v : null;
    } catch (e) { return null; }
  }
  function save(root, v) {
    try { localStorage.setItem(storageKey(root), JSON.stringify(v)); } catch (e) { /* private mode */ }
  }
  function forget(root) {
    try { localStorage.removeItem(storageKey(root)); } catch (e) { /* private mode */ }
  }

  function table(root) { return root.querySelector("table.gth-table"); }
  function headerCells(root) {
    var t = table(root);
    return t && t.tHead ? Array.prototype.slice.call(t.tHead.rows[0].cells) : [];
  }
  function defaults(root) {
    return {
      hidden: headerCells(root).filter(function (th) { return th.hasAttribute("data-default-hidden"); })
        .map(function (th) { return th.getAttribute("data-gth-col"); }),
      // v0.12: the viewer's ui.density (<html data-gth-density>) when this
      // table has nothing stored; the table's own toggle still wins.
      density: document.documentElement.getAttribute("data-gth-density") === "compact"
        ? "compact" : "comfortable",
    };
  }
  function current(root) { return load(root) || defaults(root); }

  function apply(root, v) {
    var t = table(root);
    if (!t) return;
    var ths = headerCells(root);
    // Which header indexes to hide: stored keys, never a pinned column, and
    // never every column (a stale store could name them all).
    var hide = ths.map(function (th) {
      var col = th.getAttribute("data-gth-col");
      return col !== null && !th.hasAttribute("data-gth-pinned") && v.hidden.indexOf(col) !== -1;
    });
    var shownCols = ths.filter(function (th, i) { return th.hasAttribute("data-gth-col") && !hide[i]; });
    if (!shownCols.length) hide = hide.map(function () { return false; });

    ths.forEach(function (th, i) { th.classList.toggle("gth-col-hidden", hide[i]); });
    Array.prototype.forEach.call(t.tBodies, function (tbody) {
      Array.prototype.forEach.call(tbody.rows, function (tr) {
        var cells = tr.cells;
        for (var c = 0; c < cells.length; c++) if (cells[c].colSpan > 1) return;
        for (var i = 0; i < cells.length && i < hide.length; i++) cells[i].classList.toggle("gth-col-hidden", hide[i]);
      });
    });

    var compact = v.density === "compact";
    t.classList.toggle("table-sm", compact);
    t.classList.toggle("gth-table-compact", compact);
    // Under a compact page (ui.density), a table set to Comfortable keeps
    // comfortable cells (theme.css).
    t.classList.toggle("gth-table-comfortable", !compact);

    var menu = root.querySelector("[data-gth-view-menu]");
    if (!menu) return;
    menu.hidden = false;
    var visible = 0;
    ths.forEach(function (th, i) { if (th.hasAttribute("data-gth-col") && !hide[i]) visible++; });
    menu.querySelectorAll("[data-gth-col-toggle]").forEach(function (box) {
      var col = box.getAttribute("data-gth-col-toggle");
      var th = ths.filter(function (h) { return h.getAttribute("data-gth-col") === col; })[0];
      if (!th) return;
      var pinned = th.hasAttribute("data-gth-pinned");
      box.checked = !th.classList.contains("gth-col-hidden");
      // The last shown column can't be hidden.
      box.disabled = pinned || (box.checked && visible === 1);
    });
    menu.querySelectorAll("[data-gth-density]").forEach(function (r) { r.checked = r.value === (compact ? "compact" : "comfortable"); });
  }

  function rootOf(el) { return el && el.closest ? el.closest("[data-gth-table-view]") : null; }

  document.addEventListener("change", function (evt) {
    var t = evt.target;
    var root = rootOf(t);
    if (!root) return;
    var v = current(root);
    if (t.matches("[data-gth-col-toggle]")) {
      var col = t.getAttribute("data-gth-col-toggle");
      v.hidden = v.hidden.filter(function (k) { return k !== col; });
      if (!t.checked) v.hidden.push(col);
    } else if (t.matches("[data-gth-density]")) {
      v.density = t.value;
    } else {
      return;
    }
    save(root, v);
    apply(root, v);
  });

  document.addEventListener("click", function (evt) {
    var t = evt.target;
    if (!t.closest || !t.closest("[data-gth-view-reset]")) return;
    var root = rootOf(t);
    if (!root) return;
    forget(root);
    apply(root, defaults(root));
  });

  function init(scope) {
    var roots = [];
    var own = rootOf(scope);
    if (own) roots.push(own);
    if (scope.querySelectorAll) {
      scope.querySelectorAll("[data-gth-table-view]").forEach(function (r) {
        if (roots.indexOf(r) === -1) roots.push(r);
      });
    }
    roots.forEach(function (r) { apply(r, current(r)); });
  }

  document.addEventListener("htmx:load", function (evt) { init(evt.detail.elt); });
  // Loaded at the end of <body>: the tables above are already parsed, so
  // apply now rather than on DOMContentLoaded — no flash of hidden columns.
  init(document);
})();
