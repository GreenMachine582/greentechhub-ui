// gth-date-range — see components/date_range.html (v0.11).
// Shows each [data-gth-date-range]'s preset chips (rendered hidden so they
// only appear when they can work). A chip fills the From/To inputs from the
// browser's local date and fires one bubbling `change` on To, so a
// gth_table_filter form re-queries once. aria-pressed tracks whichever chip
// matches the inputs, whether a chip or the user set them. Fiscal years start
// on the 1st of data-fy-start-month (1-12, default 7) and run twelve months.
(function () {
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  // Local date parts, not toISOString (UTC would be a day off east of GMT).
  function iso(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }

  function fy(today, startMonth, back) {
    var y = today.getFullYear() - (today.getMonth() + 1 >= startMonth ? 0 : 1) - back;
    return [new Date(y, startMonth - 1, 1), new Date(y + 1, startMonth - 1, 0)];
  }

  function range(root, preset) {
    var t = new Date();
    var today = new Date(t.getFullYear(), t.getMonth(), t.getDate());
    var startMonth = parseInt(root.getAttribute("data-fy-start-month"), 10);
    if (!(startMonth >= 1 && startMonth <= 12)) startMonth = 7;
    var r;
    if (preset === "today") r = [today, today];
    else if (preset === "month") r = [new Date(t.getFullYear(), t.getMonth(), 1), new Date(t.getFullYear(), t.getMonth() + 1, 0)];
    else if (preset === "fy") r = fy(today, startMonth, 0);
    else if (preset === "last_fy") r = fy(today, startMonth, 1);
    else return null;
    return [iso(r[0]), iso(r[1])];
  }

  function inputs(root) {
    return [root.querySelector("[data-gth-date-from]"), root.querySelector("[data-gth-date-to]")];
  }

  function sync(root) {
    var io = inputs(root);
    if (!io[0] || !io[1]) return;
    root.querySelectorAll("[data-preset]").forEach(function (chip) {
      var r = range(root, chip.getAttribute("data-preset"));
      var on = !!r && io[0].value === r[0] && io[1].value === r[1];
      chip.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function init(scope) {
    var roots = [];
    if (scope.matches && scope.matches("[data-gth-date-range]")) roots.push(scope);
    if (scope.querySelectorAll) roots = roots.concat(Array.prototype.slice.call(scope.querySelectorAll("[data-gth-date-range]")));
    roots.forEach(function (root) {
      var presets = root.querySelector(".gth-date-range-presets");
      if (presets) presets.hidden = false;
      sync(root);
    });
  }

  document.addEventListener("click", function (evt) {
    var chip = evt.target.closest && evt.target.closest("[data-gth-date-range] [data-preset]");
    if (!chip) return;
    var root = chip.closest("[data-gth-date-range]");
    var r = range(root, chip.getAttribute("data-preset"));
    var io = inputs(root);
    if (!r || !io[0] || !io[1]) return;
    io[0].value = r[0];
    io[1].value = r[1];
    sync(root);
    io[1].dispatchEvent(new Event("change", { bubbles: true }));
  });

  function onEdit(evt) {
    var root = evt.target.closest && evt.target.closest("[data-gth-date-range]");
    if (root) sync(root);
  }
  document.addEventListener("input", onEdit);
  document.addEventListener("change", onEdit);

  // Swapped-in content (modals, table partials) gets its chips shown too.
  document.addEventListener("htmx:load", function (evt) { init(evt.detail.elt); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(document); });
  else init(document);
})();
