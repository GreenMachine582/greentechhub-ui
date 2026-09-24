// gth-sidebar — see components/sidebar.html and docs/components.md (v0.8).
//
// - Group toggles ([data-gth-sidebar-group] buttons over the list named by
//   aria-controls). Open groups are remembered across pages
//   (localStorage["gth-sidebar-open"], by group label) on top of the ones
//   the server opens for the current page.
// - Filter box ([data-gth-sidebar-filter]): hides non-matching items, opens
//   the groups that hold matches, and restores the previous state when
//   cleared.
// - Icon rail ([data-gth-sidebar-rail] toggle; data-gth-sidebar="rail" on
//   <html>, persisted in localStorage["gth-sidebar-mode"] and applied
//   before first paint by app.html). ≥992px only. In the rail a top-level
//   group opens as a flyout beside its icon; Esc or a click elsewhere
//   closes it.
// - A link click inside the off-canvas drawer (below 992px) closes the
//   drawer, so same-page anchors don't leave it covering the page.
//
// Vanilla JS, delegated from document; Bootstrap's bundle provides the
// drawer (offcanvas-lg) itself.
(function () {
  var STORE_OPEN = "gth-sidebar-open";
  var STORE_MODE = "gth-sidebar-mode";
  var root = document.documentElement;
  var wide = window.matchMedia("(min-width: 992px)");

  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* private mode etc. */ }
  }
  function isRail() { return root.getAttribute("data-gth-sidebar") === "rail" && wide.matches; }
  function listOf(button) { return document.getElementById(button.getAttribute("aria-controls")); }
  function isTopLevel(button) {
    var li = button.closest(".gth-sidebar-item");
    return li && li.parentElement && li.parentElement.parentElement &&
      li.parentElement.parentElement.matches("[data-gth-sidebar]");
  }
  function setOpen(button, open) {
    button.setAttribute("aria-expanded", open ? "true" : "false");
    var list = listOf(button);
    if (list) list.hidden = !open;
  }
  function saveOpenGroups() {
    var open = [];
    document.querySelectorAll("[data-gth-sidebar-group][aria-expanded=true]").forEach(function (b) {
      if (!b.closest(".gth-flyout-open")) open.push(b.getAttribute("data-gth-sidebar-group"));
    });
    write(STORE_OPEN, JSON.stringify(open));
  }

  // ── rail flyouts ─────────────────────────────────────────────────────
  function closeFlyouts(except, restoreFocus) {
    document.querySelectorAll(".gth-sidebar-group.gth-flyout-open").forEach(function (li) {
      if (li === except) return;
      var button = li.querySelector(":scope > .gth-sidebar-toggle");
      li.classList.remove("gth-flyout-open");
      // Back to the group's own (non-flyout) state.
      setOpen(button, li.getAttribute("data-gth-was-open") === "true");
      li.removeAttribute("data-gth-was-open");
      if (restoreFocus) button.focus();
    });
  }
  function toggleFlyout(button) {
    var li = button.closest(".gth-sidebar-group");
    if (li.classList.contains("gth-flyout-open")) {
      closeFlyouts(null, false);
      return;
    }
    closeFlyouts(li, false);
    li.setAttribute("data-gth-was-open", button.getAttribute("aria-expanded"));
    li.classList.add("gth-flyout-open");
    setOpen(button, true);
  }

  function setRail(on) {
    closeFlyouts(null, false);
    if (on) root.setAttribute("data-gth-sidebar", "rail");
    else root.removeAttribute("data-gth-sidebar");
    write(STORE_MODE, on ? "rail" : "full");
    syncRailToggles();
  }
  function syncRailToggles() {
    var on = root.getAttribute("data-gth-sidebar") === "rail";
    document.querySelectorAll("[data-gth-sidebar-rail]").forEach(function (b) {
      b.setAttribute("aria-pressed", on ? "true" : "false");
      var label = on ? "Expand sidebar" : "Collapse sidebar";
      b.setAttribute("aria-label", label);
      b.title = label;
      var icon = b.querySelector(".bi");
      if (icon) icon.className = "bi bi-chevron-double-" + (on ? "right" : "left");
    });
  }

  // ── filter ───────────────────────────────────────────────────────────
  var saved = new WeakMap();  // nav → [[button, wasOpen], …] before filtering
  function ownLabel(li) {
    var own = li.querySelector(":scope > .gth-sidebar-link .gth-sidebar-label");
    return own ? own.textContent.toLowerCase() : "";
  }
  function showAll(list) {
    list.querySelectorAll(".gth-sidebar-item").forEach(function (li) { li.hidden = false; });
  }
  function filterList(list, q) {
    var any = false;
    Array.prototype.forEach.call(list.children, function (li) {
      var selfMatch = ownLabel(li).indexOf(q) !== -1;
      var childList = li.querySelector(":scope > ul");
      var childMatch = false;
      if (childList) {
        if (selfMatch) {
          showAll(childList);
        } else {
          childMatch = filterList(childList, q);
        }
        if (selfMatch || childMatch) setOpen(li.querySelector(":scope > .gth-sidebar-toggle"), true);
      }
      li.hidden = !(selfMatch || childMatch);
      any = any || selfMatch || childMatch;
    });
    return any;
  }
  function applyFilter(input) {
    var nav = document.getElementById(input.getAttribute("aria-controls"));
    if (!nav) return;
    var q = input.value.trim().toLowerCase();
    var empty = nav.querySelector("[data-gth-sidebar-empty]");
    if (!saved.has(nav) && q) {
      saved.set(nav, Array.prototype.map.call(nav.querySelectorAll("[data-gth-sidebar-group]"), function (b) {
        return [b, b.getAttribute("aria-expanded") === "true"];
      }));
    }
    if (!q) {
      showAll(nav);
      (saved.get(nav) || []).forEach(function (pair) { setOpen(pair[0], pair[1]); });
      saved.delete(nav);
      if (empty) empty.hidden = true;
      return;
    }
    var any = filterList(nav.querySelector(":scope > ul"), q);
    if (!empty) {
      empty = document.createElement("p");
      empty.className = "text-secondary small px-3 py-2 mb-0";
      empty.setAttribute("data-gth-sidebar-empty", "");
      empty.setAttribute("role", "status");
      empty.textContent = "No matches";
      nav.appendChild(empty);
    }
    empty.hidden = any;
  }

  // ── events ───────────────────────────────────────────────────────────
  document.addEventListener("click", function (evt) {
    var t = evt.target;
    var rail = t.closest && t.closest("[data-gth-sidebar-rail]");
    if (rail) {
      setRail(root.getAttribute("data-gth-sidebar") !== "rail");
      return;
    }
    var button = t.closest && t.closest("[data-gth-sidebar-group]");
    if (button) {
      if (isRail() && isTopLevel(button)) {
        toggleFlyout(button);
      } else {
        setOpen(button, button.getAttribute("aria-expanded") !== "true");
        saveOpenGroups();
      }
      return;
    }
    // Clicking anywhere outside an open flyout closes it.
    if (!(t.closest && t.closest(".gth-flyout-open"))) closeFlyouts(null, false);
    // A link inside the (below-992px) drawer closes the drawer.
    var link = t.closest && t.closest(".gth-sidebar a[href]");
    if (link && !wide.matches && window.bootstrap) {
      var drawer = bootstrap.Offcanvas.getInstance(link.closest(".gth-sidebar"));
      if (drawer) drawer.hide();
    }
  });

  document.addEventListener("keydown", function (evt) {
    if (evt.key !== "Escape") return;
    if (document.querySelector(".gth-flyout-open")) {
      evt.preventDefault();
      closeFlyouts(null, true);
    }
  });

  function onFilter(evt) {
    if (evt.target.matches && evt.target.matches("[data-gth-sidebar-filter]")) applyFilter(evt.target);
  }
  document.addEventListener("input", onFilter);
  document.addEventListener("search", onFilter, true);

  wide.addEventListener("change", function () { closeFlyouts(null, false); });

  // Initial state: remembered open groups, rail toggle labels.
  function init() {
    var open = [];
    try { open = JSON.parse(read(STORE_OPEN) || "[]"); } catch (e) { open = []; }
    document.querySelectorAll("[data-gth-sidebar-group]").forEach(function (b) {
      if (open.indexOf(b.getAttribute("data-gth-sidebar-group")) !== -1) setOpen(b, true);
    });
    syncRailToggles();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
