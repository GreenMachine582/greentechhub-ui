// gth-copy-button — see gth_copy_button in components/copy_button.html (v0.20).
// One delegated click listener, so buttons htmx swaps in need no setup. A
// button copies its data-gth-copy-text, or the text of its
// data-gth-copy-target (a field's value, otherwise its textContent). On
// success its label and icon show data-gth-copied-label and a tick for a
// moment, announced through one shared polite live region. Without the
// clipboard (an insecure origin, a denied permission) it selects the target
// field's text and a toast (toast.js's showToast event) says to press Ctrl+C.
(function () {
  var RESET_MS = 2000;
  var live = null;

  function announce(text) {
    if (!live) {
      live = document.createElement("div");
      live.className = "visually-hidden";
      live.id = "gth-copy-status";
      live.setAttribute("aria-live", "polite");
      document.body.appendChild(live);
    }
    // Clear first so the same message twice is still announced.
    live.textContent = "";
    window.setTimeout(function () { live.textContent = text; }, 50);
  }

  function targetOf(button) {
    var selector = button.getAttribute("data-gth-copy-target");
    if (!selector) return null;
    // "#<id>" by id first: field ids are setting keys like "gth-field-ui.theme",
    // whose dot a selector would read as a class.
    if (selector.charAt(0) === "#") {
      var byId = document.getElementById(selector.slice(1));
      if (byId) return byId;
    }
    try {
      return document.querySelector(selector);
    } catch (e) {
      return null;  // an invalid selector
    }
  }

  function textFor(button, target) {
    if (button.hasAttribute("data-gth-copy-text")) return button.getAttribute("data-gth-copy-text");
    if (!target) return null;
    return "value" in target && typeof target.value === "string" ? target.value : target.textContent;
  }

  function showCopied(button) {
    var label = button.querySelector(".gth-copy-label");
    var icon = button.querySelector(".bi");
    var copied = button.getAttribute("data-gth-copied-label") || "Copied";
    if (!button.hasAttribute("data-gth-copy-label")) {
      button.setAttribute("data-gth-copy-label", label ? label.textContent : "");
      button.setAttribute("data-gth-copy-icon", icon ? icon.className : "");
    }
    if (label) label.textContent = copied;
    if (icon) icon.className = "bi bi-check2";
    button.classList.add("is-copied");
    announce(copied);
    window.clearTimeout(button._gthCopyTimer);
    button._gthCopyTimer = window.setTimeout(function () {
      if (label) label.textContent = button.getAttribute("data-gth-copy-label");
      if (icon) icon.className = button.getAttribute("data-gth-copy-icon");
      button.classList.remove("is-copied");
    }, RESET_MS);
  }

  function fallback(target) {
    if (target && typeof target.select === "function") {
      target.focus();
      target.select();
    }
    document.body.dispatchEvent(new CustomEvent("showToast", {
      detail: { message: "Couldn't copy automatically. Press Ctrl+C to copy.", kind: "warning" }
    }));
  }

  document.addEventListener("click", function (evt) {
    var button = evt.target.closest && evt.target.closest("[data-gth-copy]");
    if (!button) return;
    var target = targetOf(button);
    var text = textFor(button, target);
    if (text === null) return;
    if (!navigator.clipboard || !window.isSecureContext) {
      fallback(target);
      return;
    }
    navigator.clipboard.writeText(text).then(function () { showCopied(button); },
                                             function () { fallback(target); });
  });
})();
