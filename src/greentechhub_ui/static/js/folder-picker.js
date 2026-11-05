// gth-folder-picker — see gth_folder_picker in components/folder_picker.html
// (v0.21) and docs/components.md.
//
// Markup: [data-gth-folder-picker] (data-gth-folder-picker-url) holding the
// path input ([data-gth-folder-picker-input]), a Browse button
// ([data-gth-folder-picker-browse]) and a Bootstrap modal
// ([data-gth-folder-picker-modal], data-gth-folder-picker-for = the input's
// id) whose body ([data-gth-folder-picker-body]) holds the server-rendered
// gth_folder_browser. The browser navigates itself with hx-get; this file
// only opens the modal at the typed path, fills the input on "Choose this
// folder" ([data-gth-folder-choose]), and handles focus and arrow keys.
//
// The modal is moved to <body> on first open, so the browser's controls
// never sit inside the form the field is in (or a modal it's in).
//
// Keyboard: ↑/↓, Home/End move between folders; Enter opens one (it's a
// button); Backspace or Alt+↑ goes up a folder. After each navigation focus
// lands on the first folder (or the hidden-folders switch, when that was
// what changed). Closing returns focus to the input.
//
// Delegated from document, so it survives htmx swaps and 422 re-renders.
// Requires htmx (htmx.ajax) and Bootstrap's Modal.
(function () {
  var modals = new WeakMap(); // picker → its modal (wherever it now lives)

  function pickerOf(el) { return el && el.closest ? el.closest("[data-gth-folder-picker]") : null; }
  function modalOf(picker) {
    var modal = modals.get(picker);
    if (!modal) {
      modal = picker.querySelector("[data-gth-folder-picker-modal]");
      modals.set(picker, modal);
    }
    return modal;
  }
  function inputOf(picker) { return picker.querySelector("[data-gth-folder-picker-input]"); }
  function inputFor(modal) {
    return modal ? document.getElementById(modal.getAttribute("data-gth-folder-picker-for")) : null;
  }
  function bodyOf(modal) { return modal.querySelector("[data-gth-folder-picker-body]"); }

  function portal(picker) {
    var modal = modalOf(picker);
    if (modal.parentNode !== document.body) {
      // A re-rendered form (a 422) leaves the old picker's moved modal
      // behind with the same id: drop it.
      document.querySelectorAll("[data-gth-folder-picker-modal]").forEach(function (m) {
        if (m !== modal && m.id === modal.id) m.remove();
      });
      document.body.appendChild(modal);
    }
    return modal;
  }

  function open(picker) {
    var modal = portal(picker);
    var input = inputOf(picker);
    var url = picker.getAttribute("data-gth-folder-picker-url");
    var full = url + (url.indexOf("?") === -1 ? "?" : "&") +
      "path=" + encodeURIComponent(input.value.trim()) +
      "&target=" + encodeURIComponent(input.id);
    htmx.ajax("GET", full, { target: bodyOf(modal), swap: "innerHTML" });
    bootstrap.Modal.getOrCreateInstance(modal).show();
  }

  function choose(button) {
    var modal = button.closest("[data-gth-folder-picker-modal]");
    var input = inputFor(modal);
    if (!input) return;
    input.value = button.getAttribute("data-gth-folder-choose");
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    bootstrap.Modal.getOrCreateInstance(modal).hide();
  }

  function entries(container) {
    return Array.prototype.slice.call(container.querySelectorAll("[data-gth-folder-entry]"));
  }
  function focusFirst(modal, switchChanged) {
    var body = bodyOf(modal);
    var target = switchChanged ? body.querySelector("[role=switch]") : null;
    target = target || entries(body)[0] || body.querySelector(".gth-folder-choose:not([disabled])") ||
      body.querySelector(".gth-folder-up") || modal.querySelector(".btn-close");
    if (target) target.focus();
  }

  document.addEventListener("click", function (event) {
    var browse = event.target.closest("[data-gth-folder-picker-browse]");
    if (browse) {
      open(pickerOf(browse));
      return;
    }
    var chooseButton = event.target.closest("[data-gth-folder-choose]");
    if (chooseButton && !chooseButton.disabled) choose(chooseButton);
  });

  document.addEventListener("keydown", function (event) {
    var modal = event.target.closest ? event.target.closest("[data-gth-folder-picker-modal]") : null;
    if (!modal) return;
    var body = bodyOf(modal);
    var inField = event.target.matches("input[type=text], input[type=search]");
    if ((event.key === "Backspace" && !inField) || (event.key === "ArrowUp" && event.altKey)) {
      var up = body.querySelector(".gth-folder-up");
      if (up) {
        event.preventDefault();
        up.click();
      }
      return;
    }
    var list = entries(body);
    var index = list.indexOf(event.target);
    if (index === -1) return;
    var next = { ArrowDown: index + 1, ArrowUp: index - 1, Home: 0, End: list.length - 1 }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    list[Math.max(0, Math.min(list.length - 1, next))].focus();
  });

  document.addEventListener("htmx:afterSwap", function (event) {
    var body = event.detail.target;
    if (!body || !body.matches || !body.matches("[data-gth-folder-picker-body]")) return;
    var elt = event.detail.requestConfig && event.detail.requestConfig.elt;
    var modal = body.closest("[data-gth-folder-picker-modal]");
    if (modal && modal.classList.contains("show")) focusFirst(modal, !!(elt && elt.matches && elt.matches("[role=switch]")));
  });

  document.addEventListener("shown.bs.modal", function (event) {
    if (event.target.matches("[data-gth-folder-picker-modal]")) focusFirst(event.target, false);
  });

  document.addEventListener("hidden.bs.modal", function (event) {
    if (!event.target.matches("[data-gth-folder-picker-modal]")) return;
    var input = inputFor(event.target);
    if (input) input.focus();
  });
})();
