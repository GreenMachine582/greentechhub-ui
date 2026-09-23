// gth-combobox — see components/combobox.html and docs/components.md (v0.7).
//
// Markup (rendered by gth_combobox): [data-gth-combobox] wrapping a text
// input ([data-gth-combobox-input]), a hidden value input
// ([data-gth-combobox-value]) and a results panel
// ([data-gth-combobox-results]). Results are server-rendered by the
// consumer's endpoint (data-gth-combobox-url, called with ?q=) using
// gth_combobox_option, so each option carries data-value/data-label.
//
// Delegated from document, so it survives htmx swaps and 422 re-renders of
// the form it lives in. Requires htmx (htmx.ajax).
(function () {
  var DEBOUNCE_MS = 250;
  var timers = new WeakMap();

  function boxOf(el) { return el && el.closest ? el.closest("[data-gth-combobox]") : null; }
  function parts(box) {
    return {
      input: box.querySelector("[data-gth-combobox-input]"),
      value: box.querySelector("[data-gth-combobox-value]"),
      panel: box.querySelector("[data-gth-combobox-results]"),
    };
  }
  function isInput(box, el) { return box && el === parts(box).input; }
  function options(box) {
    return Array.prototype.slice.call(parts(box).panel.querySelectorAll("[data-value]"));
  }
  function isOpen(box) { return !parts(box).panel.classList.contains("d-none"); }
  function open(box) {
    var p = parts(box);
    p.panel.classList.remove("d-none");
    p.input.setAttribute("aria-expanded", "true");
  }
  // Closing also cancels a pending debounced search and marks the panel
  // dismissed, so a response still in flight can't pop it back open (e.g.
  // type then Esc within the debounce window). Only a fresh user-initiated
  // load (typing, focusing, arrow keys) clears the flag.
  function close(box) {
    clearTimeout(timers.get(box));
    box.setAttribute("data-gth-combobox-dismissed", "");
    var p = parts(box);
    p.panel.classList.add("d-none");
    p.input.setAttribute("aria-expanded", "false");
    p.input.removeAttribute("aria-activedescendant");
  }
  function activeIndex(box) {
    return options(box).findIndex(function (o) { return o.classList.contains("active"); });
  }
  function setActive(box, index) {
    var opts = options(box);
    opts.forEach(function (o) {
      o.classList.remove("active");
      o.setAttribute("aria-selected", "false");
    });
    if (!opts.length) return;
    var opt = opts[(index + opts.length) % opts.length];
    opt.classList.add("active");
    opt.setAttribute("aria-selected", "true");
    opt.scrollIntoView({ block: "nearest" });
    if (opt.id) parts(box).input.setAttribute("aria-activedescendant", opt.id);
  }
  // With a value already picked the input holds its label, not a search
  // term — search for everything instead.
  function currentQuery(box) {
    var p = parts(box);
    return p.value.value ? "" : p.input.value;
  }
  function load(box, query) {
    box.removeAttribute("data-gth-combobox-dismissed");
    var url = box.getAttribute("data-gth-combobox-url");
    var sep = url.indexOf("?") === -1 ? "?" : "&";
    htmx.ajax("GET", url + sep + "q=" + encodeURIComponent(query),
      { target: parts(box).panel, swap: "innerHTML" });
  }
  function pick(box, opt) {
    var p = parts(box);
    p.value.value = opt.getAttribute("data-value");
    p.input.value = opt.getAttribute("data-label");
    p.input.classList.remove("is-invalid");
    close(box);
    p.value.dispatchEvent(new Event("change", { bubbles: true }));
  }

  document.addEventListener("focusin", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    if (parts(box).value.value) evt.target.select();  // typing replaces the label
    load(box, currentQuery(box));
  });

  document.addEventListener("input", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    // Any edit invalidates the previous pick: only a value chosen from the
    // list is ever submitted.
    parts(box).value.value = "";
    clearTimeout(timers.get(box));
    box.removeAttribute("data-gth-combobox-dismissed");
    timers.set(box, setTimeout(function () { load(box, parts(box).input.value); }, DEBOUNCE_MS));
  });

  document.addEventListener("keydown", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    if (evt.key === "ArrowDown" || evt.key === "ArrowUp") {
      evt.preventDefault();
      if (!isOpen(box)) { load(box, currentQuery(box)); return; }
      setActive(box, activeIndex(box) + (evt.key === "ArrowDown" ? 1 : -1));
    } else if (evt.key === "Enter" && isOpen(box)) {
      evt.preventDefault();  // pick, don't submit the surrounding form
      var opts = options(box);
      var opt = opts[activeIndex(box)] || (opts.length === 1 ? opts[0] : null);
      if (opt) pick(box, opt);
    } else if (evt.key === "Escape" && isOpen(box)) {
      evt.preventDefault();
      evt.stopPropagation();  // close the panel, not an enclosing modal
      close(box);
    } else if (evt.key === "Tab") {
      close(box);
    }
  }, true);

  document.addEventListener("click", function (evt) {
    var opt = evt.target.closest && evt.target.closest("[data-gth-combobox-results] [data-value]");
    if (opt) { pick(boxOf(opt), opt); return; }
    document.querySelectorAll("[data-gth-combobox]").forEach(function (box) {
      if (!box.contains(evt.target)) close(box);
    });
  });

  document.body.addEventListener("htmx:afterSwap", function (evt) {
    var box = boxOf(evt.detail.target);
    if (!box || evt.detail.target !== parts(box).panel) return;
    // Option ids come from the panel's (unique) id, not the option value:
    // two comboboxes can list the same value, and values may not be valid
    // ids. aria-activedescendant points at these.
    options(box).forEach(function (o, i) { o.id = parts(box).panel.id + "-opt-" + i; });
    // A slow response shouldn't pop the list back open after the user moved
    // on (left the field, or dismissed it with Esc/Tab/a pick).
    if (document.activeElement !== parts(box).input) return;
    if (box.hasAttribute("data-gth-combobox-dismissed")) return;
    open(box);
    var picked = parts(box).value.value;
    var current = options(box).findIndex(function (o) { return o.getAttribute("data-value") === picked; });
    setActive(box, current >= 0 ? current : 0);
  });
})();
