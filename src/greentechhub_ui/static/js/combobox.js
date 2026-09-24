// gth-combobox / gth-multiselect — see components/combobox.html,
// components/multiselect.html and docs/components.md (v0.7).
//
// Markup (rendered by gth_combobox): [data-gth-combobox] wrapping a text
// input ([data-gth-combobox-input]), a hidden value input
// ([data-gth-combobox-value]) and a results panel
// ([data-gth-combobox-results]). Results are server-rendered by the
// consumer's endpoint (data-gth-combobox-url, called with ?q=) using
// gth_combobox_option, so each option carries data-value/data-label.
//
// Multi mode (gth_multiselect, [data-gth-combobox-multi]): picks become
// removable chips ([data-gth-combobox-chips]), each carrying a hidden input
// named data-gth-combobox-name, instead of filling one hidden value. The
// panel stays open for more picks and hides options already chosen.
// [data-gth-combobox-create] (tags) turns Enter/comma on unmatched text into
// a chip whose value is the text; without a url that's the only way in.
// [data-gth-combobox-max] caps the chip count; going over it pops a
// warning toast (showToast, see toast.js) with
// [data-gth-combobox-max-message]. Text typed but never turned into a chip
// is cleared when focus leaves the box, and removing a chip moves focus to
// a neighbouring chip without reopening the list — clicking into the input
// does that.
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
      chips: box.querySelector("[data-gth-combobox-chips]"),
      live: box.parentNode.querySelector("[data-gth-combobox-live]"),
    };
  }
  function isMulti(box) { return box.hasAttribute("data-gth-combobox-multi"); }
  function canCreate(box) { return box.hasAttribute("data-gth-combobox-create"); }
  function isInput(box, el) { return box && el === parts(box).input; }
  // Options still pickable: in multi mode, already-chosen ones are hidden.
  function options(box) {
    return Array.prototype.slice.call(parts(box).panel.querySelectorAll("[data-value]"))
      .filter(function (o) { return !o.hidden; });
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
  // clearOnly: just remove the highlight (no option active).
  function setActive(box, index, clearOnly) {
    var opts = options(box);
    parts(box).panel.querySelectorAll("[data-value]").forEach(function (o) {
      o.classList.remove("active");
      o.setAttribute("aria-selected", "false");
    });
    if (!opts.length || clearOnly) {
      parts(box).input.removeAttribute("aria-activedescendant");
      return;
    }
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
    return p.value && p.value.value ? "" : p.input.value;
  }
  function load(box, query) {
    var url = box.getAttribute("data-gth-combobox-url");
    if (!url) return;  // tags without suggestions
    box.removeAttribute("data-gth-combobox-dismissed");
    var sep = url.indexOf("?") === -1 ? "?" : "&";
    htmx.ajax("GET", url + sep + "q=" + encodeURIComponent(query),
      { target: parts(box).panel, swap: "innerHTML" });
  }
  function announce(box, message) {
    var live = parts(box).live;
    if (live) live.textContent = message;
  }

  // ── multi mode ─────────────────────────────────────────────────────────
  function chips(box) {
    return Array.prototype.slice.call(parts(box).chips.querySelectorAll("[data-gth-combobox-chip]"));
  }
  function chosenValues(box) {
    return chips(box).map(function (c) { return c.getAttribute("data-value"); });
  }
  function atMax(box) {
    var max = parseInt(box.getAttribute("data-gth-combobox-max"), 10);
    return max > 0 && chips(box).length >= max;
  }
  function hideChosen(box) {
    var chosen = chosenValues(box);
    parts(box).panel.querySelectorAll("[data-value]").forEach(function (o) {
      o.hidden = chosen.indexOf(o.getAttribute("data-value")) !== -1;
    });
  }
  // Same markup as gth_multiselect_chip; built with textContent/value so a
  // label or a typed tag can't inject HTML.
  function addChip(box, value, label) {
    if (chosenValues(box).indexOf(value) !== -1) {
      announce(box, label + " is already added");
      return false;
    }
    if (atMax(box)) {
      // Visible feedback too: the live region is screen-reader-only.
      var message = box.getAttribute("data-gth-combobox-max-message") || "Limit reached";
      announce(box, message);
      document.body.dispatchEvent(new CustomEvent("showToast", {
        detail: { message: message, kind: "warning" },
      }));
      return false;
    }
    var chip = document.createElement("span");
    chip.className = "badge rounded-pill gth-chip-token";
    chip.setAttribute("data-gth-combobox-chip", "");
    chip.setAttribute("data-value", value);
    var text = document.createElement("span");
    text.textContent = label;
    var hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = box.getAttribute("data-gth-combobox-name");
    hidden.value = value;
    var remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn-close ms-1";
    remove.setAttribute("data-gth-combobox-remove", "");
    remove.setAttribute("aria-label", "Remove " + label);
    chip.append(text, hidden, remove);
    parts(box).chips.appendChild(chip);
    announce(box, "Added " + label);
    hidden.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }
  function removeChip(box, chip) {
    var label = chip.textContent.trim();
    chip.remove();
    announce(box, "Removed " + label);
    hideChosen(box);
    box.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function pick(box, opt) {
    var p = parts(box);
    if (isMulti(box)) {
      addChip(box, opt.getAttribute("data-value"), opt.getAttribute("data-label"));
      p.input.value = "";
      p.input.classList.remove("is-invalid");
      box.querySelector(".gth-multiselect-control").classList.remove("is-invalid");
      p.input.focus();
      load(box, "");  // refresh the list; stays open for the next pick
      return;
    }
    p.value.value = opt.getAttribute("data-value");
    p.input.value = opt.getAttribute("data-label");
    p.input.classList.remove("is-invalid");
    close(box);
    p.value.dispatchEvent(new Event("change", { bubbles: true }));
  }
  function createFromInput(box) {
    var p = parts(box);
    var text = p.input.value.replace(/,+$/, "").trim();
    if (!text) return;
    if (addChip(box, text, text)) {
      p.input.value = "";
      load(box, "");
    } else if (chosenValues(box).indexOf(text) !== -1) {
      p.input.value = "";  // a duplicate: nothing to keep
    }
  }

  document.addEventListener("focusin", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    // Focus handed back after removing the last chip: don't pop the list.
    if (box.hasAttribute("data-gth-combobox-quiet")) {
      box.removeAttribute("data-gth-combobox-quiet");
      return;
    }
    var p = parts(box);
    if (p.value && p.value.value) evt.target.select();  // typing replaces the label
    load(box, currentQuery(box));
  });

  // Multi mode: leaving the box discards text that was never picked or
  // turned into a tag, so it can't read as a selection it isn't.
  document.addEventListener("focusout", function (evt) {
    var box = boxOf(evt.target);
    if (!box || !isMulti(box)) return;
    if (evt.relatedTarget && box.contains(evt.relatedTarget)) return;
    clearTimeout(timers.get(box));
    parts(box).input.value = "";
    close(box);
  });

  // Clicking results mustn't move focus off the input: the option still
  // gets its click, and the focusout above (or a browser that doesn't
  // focus buttons on click) can't close the panel under the pointer.
  // Also note whether the input already had focus, for the click below.
  var focusedAtMousedown = null;
  document.addEventListener("mousedown", function (evt) {
    var box = boxOf(evt.target);
    focusedAtMousedown = document.activeElement;
    if (box && evt.target.closest("[data-gth-combobox-results]")) evt.preventDefault();
  });

  document.addEventListener("input", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    // Any edit invalidates the previous pick: only a value chosen from the
    // list is ever submitted.
    var p = parts(box);
    if (p.value) p.value.value = "";
    clearTimeout(timers.get(box));
    box.removeAttribute("data-gth-combobox-dismissed");
    timers.set(box, setTimeout(function () { load(box, p.input.value); }, DEBOUNCE_MS));
  });

  document.addEventListener("keydown", function (evt) {
    var box = boxOf(evt.target);
    if (!isInput(box, evt.target)) return;
    var input = evt.target;
    if (evt.key === "ArrowDown" || evt.key === "ArrowUp") {
      evt.preventDefault();
      if (!isOpen(box)) { load(box, currentQuery(box)); return; }
      var down = evt.key === "ArrowDown";
      var i = activeIndex(box);  // -1: nothing highlighted yet (tags mode)
      setActive(box, i === -1 ? (down ? 0 : -1) : i + (down ? 1 : -1));
    } else if (evt.key === "Enter" && (isOpen(box) || (canCreate(box) && input.value.trim()))) {
      evt.preventDefault();  // pick, don't submit the surrounding form
      var opts = isOpen(box) ? options(box) : [];
      var opt = opts[activeIndex(box)];
      if (!opt && canCreate(box)) {
        // Tags: an exact label match picks the existing option (its value);
        // anything else becomes a new tag.
        var typed = input.value.trim().toLowerCase();
        opt = opts.find(function (o) { return o.getAttribute("data-label").toLowerCase() === typed; });
      } else if (!opt && opts.length === 1) {
        opt = opts[0];
      }
      if (opt) pick(box, opt);
      else if (isMulti(box) && canCreate(box)) createFromInput(box);
    } else if (evt.key === "," && isMulti(box) && canCreate(box)) {
      evt.preventDefault();
      createFromInput(box);
    } else if (evt.key === "Backspace" && isMulti(box) && input.value === "") {
      var all = chips(box);
      if (all.length) removeChip(box, all[all.length - 1]);
    } else if (evt.key === "Escape" && isOpen(box)) {
      evt.preventDefault();
      evt.stopPropagation();  // close the panel, not an enclosing modal
      close(box);
    } else if (evt.key === "Tab") {
      close(box);
    }
  }, true);

  document.addEventListener("click", function (evt) {
    var cbox = boxOf(evt.target);
    // Clicking an input that already has focus (after Esc, a pick or a
    // removal) reopens the list; a first click is handled by focusin.
    if (isInput(cbox, evt.target) && !isOpen(cbox) && focusedAtMousedown === evt.target) {
      load(cbox, currentQuery(cbox));
      return;
    }
    var remove = evt.target.closest && evt.target.closest("[data-gth-combobox-remove]");
    if (remove) {
      // Focus moves to a neighbouring chip (or quietly back to the input),
      // never reopening the list: clicking into the input does that.
      var rbox = boxOf(remove);
      var chip = remove.closest("[data-gth-combobox-chip]");
      var all = chips(rbox);
      var neighbour = all[all.indexOf(chip) + 1] || all[all.indexOf(chip) - 1];
      close(rbox);
      removeChip(rbox, chip);
      if (neighbour) {
        neighbour.querySelector("[data-gth-combobox-remove]").focus();
      } else if (document.activeElement !== parts(rbox).input) {
        // (Already focused — e.g. Safari doesn't focus a clicked button —
        // means no focusin will come to consume the flag.)
        rbox.setAttribute("data-gth-combobox-quiet", "");
        parts(rbox).input.focus();
      }
      return;
    }
    var opt = evt.target.closest && evt.target.closest("[data-gth-combobox-results] [data-value]");
    if (opt) { pick(boxOf(opt), opt); return; }
    // A click on a multiselect's chip area focuses its input.
    var control = evt.target.closest && evt.target.closest(".gth-multiselect-control");
    if (control && evt.target === control) parts(boxOf(control)).input.focus();
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
    parts(box).panel.querySelectorAll("[data-value]").forEach(function (o, i) {
      o.id = parts(box).panel.id + "-opt-" + i;
    });
    if (isMulti(box)) hideChosen(box);
    // A slow response shouldn't pop the list back open after the user moved
    // on (left the field, or dismissed it with Esc/Tab/a pick).
    if (document.activeElement !== parts(box).input) return;
    if (box.hasAttribute("data-gth-combobox-dismissed")) return;
    open(box);
    // Tags mode highlights nothing until an arrow key: Enter should create
    // what was typed, not silently take the first suggestion.
    if (canCreate(box)) {
      setActive(box, -1, true);
      return;
    }
    var picked = parts(box).value ? parts(box).value.value : null;
    var current = options(box).findIndex(function (o) { return o.getAttribute("data-value") === picked; });
    setActive(box, current >= 0 ? current : 0);
  });
})();
