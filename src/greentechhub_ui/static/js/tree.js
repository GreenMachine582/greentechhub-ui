// gth-tree — see components/tree.html and docs/components.md (v0.8).
//
// WAI-APG tree view: roving tabindex over the visible treeitems;
// ↑/↓ move, → expands (or enters the first child), ← collapses (or goes to
// the parent), Home/End, Enter activates, Space selects/checks, a printable
// key jumps to the next node starting with it. Clicking the chevron
// toggles; clicking a row activates it.
//
// Lazy children: a has_children node's group ([data-gth-tree-lazy]) is
// hx-get'd on the "gth-tree-expand" event this dispatches on first expand.
// Selection: data-gth-tree-select="single" (aria-selected, one hidden
// input) or "multi" (tri-state aria-checked; hidden inputs for the
// top-most checked nodes — each stands for its subtree). A tree with
// data-gth-tree-detail loads a node's data-gth-node-url into that target
// when activated. Delegated from document; requires htmx for lazy/detail.
(function () {
  function treeOf(el) { return el && el.closest ? el.closest("[data-gth-tree]") : null; }
  function itemOf(el) { return el && el.closest ? el.closest("[role=treeitem]") : null; }
  function mode(tree) { return tree.getAttribute("data-gth-tree-select") || ""; }
  function groupOf(item) { return item.querySelector(":scope > [role=group]"); }
  function parentItem(item) {
    var group = item.parentElement;
    return group && group.getAttribute("role") === "group" ? group.closest("[role=treeitem]") : null;
  }
  function childItems(item) {
    var group = groupOf(item);
    return group ? Array.prototype.slice.call(group.querySelectorAll(":scope > [role=treeitem]")) : [];
  }
  function visibleItems(tree) {
    return Array.prototype.filter.call(tree.querySelectorAll("[role=treeitem]"), function (it) {
      var hidden = it.parentElement.closest("[hidden]");
      return !hidden || !tree.contains(hidden);
    });
  }
  function isExpandable(item) { return item.hasAttribute("aria-expanded"); }
  function isExpanded(item) { return item.getAttribute("aria-expanded") === "true"; }

  function focusItem(tree, item) {
    if (!item) return;
    tree.querySelectorAll("[role=treeitem][tabindex='0']").forEach(function (it) {
      if (it !== item) it.setAttribute("tabindex", "-1");
    });
    item.setAttribute("tabindex", "0");
    item.focus();
  }

  function setExpanded(item, open) {
    if (!isExpandable(item)) return;
    var group = groupOf(item);
    item.setAttribute("aria-expanded", open ? "true" : "false");
    if (!group) return;
    group.hidden = !open;
    if (open && group.hasAttribute("data-gth-tree-lazy") && !group.hasAttribute("data-gth-tree-loaded")) {
      group.setAttribute("data-gth-tree-loaded", "");
      group.dispatchEvent(new CustomEvent("gth-tree-expand"));
    }
  }

  // ── selection ──────────────────────────────────────────────────────────
  function syncValues(tree) {
    var wrap = tree.closest("[data-gth-tree-wrap]");
    var box = wrap && wrap.querySelector("[data-gth-tree-values]");
    var name = tree.getAttribute("data-gth-tree-name");
    if (!box || !name) return;
    var values = [];
    if (mode(tree) === "multi") {
      tree.querySelectorAll("[role=treeitem][aria-checked=true]").forEach(function (it) {
        var parent = parentItem(it);
        if (!parent || parent.getAttribute("aria-checked") !== "true") values.push(it.getAttribute("data-gth-node"));
      });
    } else {
      var sel = tree.querySelector("[role=treeitem][aria-selected=true]");
      if (sel) values.push(sel.getAttribute("data-gth-node"));
    }
    box.textContent = "";
    values.forEach(function (v) {
      var input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = v;
      box.appendChild(input);
    });
    tree.dispatchEvent(new Event("change", { bubbles: true }));
  }
  function select(tree, item) {
    tree.querySelectorAll("[role=treeitem][aria-selected=true]").forEach(function (it) {
      it.setAttribute("aria-selected", "false");
    });
    item.setAttribute("aria-selected", "true");
    syncValues(tree);
  }
  function setChecked(item, state) {
    item.setAttribute("aria-checked", state);
    item.querySelectorAll("[role=treeitem]").forEach(function (it) { it.setAttribute("aria-checked", state); });
  }
  // Recompute every ancestor of `item` from its children: all checked →
  // true, none → false, anything else → mixed.
  function recomputeUp(item) {
    var parent = parentItem(item);
    while (parent) {
      var states = childItems(parent).map(function (c) { return c.getAttribute("aria-checked"); });
      var next = states.every(function (s) { return s === "true"; }) ? "true"
        : states.every(function (s) { return s === "false"; }) ? "false" : "mixed";
      parent.setAttribute("aria-checked", next);
      parent = parentItem(parent);
    }
  }
  function toggleCheck(tree, item) {
    setChecked(item, item.getAttribute("aria-checked") === "true" ? "false" : "true");
    recomputeUp(item);
    syncValues(tree);
  }
  // Leaves up: make every loaded parent agree with its children.
  function recomputeAll(tree) {
    var items = Array.prototype.slice.call(tree.querySelectorAll("[role=treeitem][aria-checked]"));
    items.filter(function (it) { return childItems(it).length === 0; }).forEach(recomputeUp);
  }

  function activate(tree, item) {
    var m = mode(tree);
    var url = item.getAttribute("data-gth-node-url");
    var target = tree.getAttribute("data-gth-tree-detail");
    if (m === "multi") {
      if (url && target) htmx.ajax("GET", url, { target: target, swap: "innerHTML" });
      else toggleCheck(tree, item);
      return;
    }
    if (m === "single" || (url && target)) select(tree, item);
    if (url && target) htmx.ajax("GET", url, { target: target, swap: "innerHTML" });
  }

  // ── events ─────────────────────────────────────────────────────────────
  document.addEventListener("click", function (evt) {
    var row = evt.target.closest && evt.target.closest(".gth-tree-row");
    var tree = treeOf(row);
    if (!row || !tree) return;
    var item = itemOf(row);
    focusItem(tree, item);
    if (evt.target.closest(".gth-tree-twisty")) {
      setExpanded(item, !isExpanded(item));
    } else if (evt.target.closest(".gth-tree-check")) {
      toggleCheck(tree, item);
    } else {
      activate(tree, item);
    }
  });

  document.addEventListener("keydown", function (evt) {
    var item = evt.target;
    if (!item.matches || !item.matches("[role=treeitem]")) return;
    var tree = treeOf(item);
    if (!tree || evt.altKey || evt.ctrlKey || evt.metaKey) return;
    var items = visibleItems(tree);
    var i = items.indexOf(item);
    var handled = true;
    switch (evt.key) {
      case "ArrowDown": focusItem(tree, items[i + 1]); break;
      case "ArrowUp": focusItem(tree, items[i - 1]); break;
      case "Home": focusItem(tree, items[0]); break;
      case "End": focusItem(tree, items[items.length - 1]); break;
      case "ArrowRight":
        if (isExpandable(item) && !isExpanded(item)) setExpanded(item, true);
        else if (isExpanded(item)) focusItem(tree, childItems(item)[0]);
        break;
      case "ArrowLeft":
        if (isExpanded(item)) setExpanded(item, false);
        else focusItem(tree, parentItem(item));
        break;
      case "Enter": activate(tree, item); break;
      case " ":
        if (mode(tree) === "multi") toggleCheck(tree, item);
        else activate(tree, item);
        break;
      default:
        handled = false;
        if (evt.key.length === 1 && /\S/.test(evt.key)) {
          // Type-ahead: the next visible node whose label starts with it.
          var key = evt.key.toLowerCase();
          for (var n = 1; n <= items.length; n++) {
            var cand = items[(i + n) % items.length];
            if ((cand.getAttribute("data-label") || "").toLowerCase().indexOf(key) === 0) {
              focusItem(tree, cand);
              handled = true;
              break;
            }
          }
        }
    }
    if (handled) {
      evt.preventDefault();
      evt.stopPropagation();
    }
  });

  // Lazy children arrived: inherit a fully checked parent's state, then
  // recompute ancestors from whatever the server marked.
  document.body.addEventListener("htmx:afterSwap", function (evt) {
    var group = evt.detail.target;
    if (!group.matches || !group.matches("[data-gth-tree-lazy]")) return;
    var item = group.closest("[role=treeitem]");
    var tree = treeOf(group);
    if (!item || !tree) return;
    if (mode(tree) === "multi") {
      if (item.getAttribute("aria-checked") === "true") setChecked(item, "true");
      else {
        var first = childItems(item)[0];
        if (first) recomputeUp(first);
      }
      syncValues(tree);
    }
  });

  function init() {
    document.querySelectorAll("[data-gth-tree]").forEach(function (tree) {
      if (mode(tree) === "multi") recomputeAll(tree);
      var sel = tree.querySelector("[role=treeitem][aria-selected=true]");
      if (sel) {
        tree.querySelectorAll("[role=treeitem][tabindex='0']").forEach(function (it) { it.setAttribute("tabindex", "-1"); });
        sel.setAttribute("tabindex", "0");
      }
      syncValues(tree);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
  // Trees that arrive later (e.g. a re-rendered 422 form) need the same.
  document.body.addEventListener("htmx:load", function (evt) {
    var el = evt.detail.elt;
    if (el && el.querySelector && (el.matches("[data-gth-tree]") || el.querySelector("[data-gth-tree]"))) init();
  });
})();
