// HTMX HX-Trigger toast handler — see greentechhub_ui.toast() (Python side),
// which documents every option. The value can be a plain string or
// {message, kind, title?, icon?, action?: {label, url}, duration?, variant?,
// html?}. The message is TEXT (textContent) unless html is true — the server
// opts in, only for markup it produced itself — so user input can't inject
// markup. gth_toast_flashes (components/toast.html) renders the same markup.
(function () {
  var KINDS = { success: "success", info: "info", warning: "warning", warn: "warning",
                danger: "danger", error: "danger", neutral: "neutral" };
  var BS = { success: "success", info: "info", warning: "warning", danger: "danger", neutral: "secondary" };
  var ICONS = { success: "check-circle-fill", info: "info-circle-fill", warning: "exclamation-triangle-fill",
                danger: "x-octagon-fill", neutral: "bell-fill" };
  var URGENT = { warning: true, danger: true };  // role=alert / assertive
  var DEFAULT_DURATION = 5000;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function build(d) {
    var kind = KINDS[d.kind || "success"] || "neutral";
    var variant = d.variant === "solid" ? "solid" : "surface";
    var duration = typeof d.duration === "number" && d.duration >= 0 ? d.duration : DEFAULT_DURATION;
    var toast = el("div", "toast gth-toast gth-toast-" + kind + " gth-toast-" + variant +
      (variant === "solid" ? " text-bg-" + BS[kind] : ""));
    toast.setAttribute("role", URGENT[kind] ? "alert" : "status");
    toast.setAttribute("aria-live", URGENT[kind] ? "assertive" : "polite");
    toast.setAttribute("aria-atomic", "true");

    var inner = el("div", "gth-toast-inner");
    var icon = el("i", "bi bi-" + (d.icon || ICONS[kind]) + " gth-toast-icon");
    icon.setAttribute("aria-hidden", "true");
    var content = el("div", "gth-toast-content");
    if (d.title) content.appendChild(el("div", "gth-toast-title", d.title));
    var message = el("div", "gth-toast-message");
    if (d.html) message.innerHTML = d.message;  // server-vouched markup only
    else message.textContent = d.message == null ? "" : String(d.message);
    content.appendChild(message);
    // Action links only to http(s)/relative URLs — never javascript: etc.
    if (d.action && d.action.url && !/^\s*[a-z][a-z0-9+.-]*:/i.test(d.action.url.replace(/^https?:/i, ""))) {
      var link = el("a", "gth-toast-action", d.action.label || "Open");
      link.href = d.action.url;
      content.appendChild(link);
    }
    var close = el("button", "btn-close gth-toast-close" +
      (variant === "solid" && !(kind === "warning" || kind === "info") ? " btn-close-white" : ""));
    close.type = "button";
    close.setAttribute("data-bs-dismiss", "toast");
    close.setAttribute("aria-label", "Close");
    inner.append(icon, content, close);
    toast.appendChild(inner);

    if (duration > 0) {
      var bar = el("div", "gth-toast-progress");
      var fill = el("span");
      fill.style.animationDuration = duration + "ms";
      bar.appendChild(fill);
      toast.appendChild(bar);
      // Bootstrap pauses the hide timer while hovered/focused and restarts
      // the FULL delay afterwards; the bar pauses via CSS and restarts here.
      var restart = function () {
        fill.style.animation = "none";
        void fill.offsetWidth;
        fill.style.animation = "";
        fill.style.animationDuration = duration + "ms";
      };
      toast.addEventListener("mouseleave", restart);
      toast.addEventListener("focusout", function (evt) {
        if (!toast.contains(evt.relatedTarget)) restart();
      });
    }
    return { el: toast, duration: duration };
  }

  document.body.addEventListener("showToast", function (e) {
    var val = e.detail;
    var d = (typeof val === "object" && val !== null) ? val : { message: val };
    var built = build(d);
    document.getElementById("gth-toast-container").appendChild(built.el);
    built.el.addEventListener("hidden.bs.toast", function () { built.el.remove(); });
    new bootstrap.Toast(built.el, { autohide: built.duration > 0, delay: built.duration || DEFAULT_DURATION }).show();
  });

  // "Started" toast for long-running actions (gth_busy_button's start_toast):
  // any htmx element with data-gth-start-toast shows it the moment its request
  // goes out; the server's own HX-Trigger toast reports the result later.
  document.body.addEventListener("htmx:beforeRequest", function (e) {
    var message = e.detail.elt.getAttribute && e.detail.elt.getAttribute("data-gth-start-toast");
    if (message) {
      document.body.dispatchEvent(new CustomEvent("showToast", { detail: { message: message, kind: "info" } }));
    }
  });

  // Automatic toasts for failed htmx requests — otherwise a 4xx/5xx (which
  // htmx doesn't swap), a network failure or a timeout does nothing visible.
  // Stands down when the response already carries its own showToast (htmx
  // processes HX-Trigger for every status), for 422 (gth_form's inline
  // validation errors, swapped by app.html), and inside an element marked
  // data-gth-error-toast="off" (on <body>: app-wide). A 401 with HX-Redirect
  // never gets here — htmx navigates first.
  var STATUS = {
    401: { title: "Signed out", message: "Sign in again to continue.", kind: "warning" },
    403: { title: "Not allowed", message: "You don't have permission to do that.", kind: "warning" },
    404: { title: "Not found", message: "It may have been deleted." },
    409: { title: "Conflict", kind: "warning" }
  };
  var DEDUPE_MS = 4000;
  var recent = {};

  function optedOut(elt) {
    return !!(elt && elt.closest && elt.closest('[data-gth-error-toast="off"]'));
  }

  function errorToast(title, message, kind) {
    var key = title + "\n" + message;
    var now = Date.now();
    if (recent[key] && now - recent[key] < DEDUPE_MS) return;  // e.g. a failing poll or several lazy loads
    recent[key] = now;
    document.body.dispatchEvent(new CustomEvent("showToast", {
      detail: { title: title, message: message, kind: kind || "danger" }
    }));
  }

  // FastAPI's HTTPException body: {"detail": "Stock not found"} — shown as
  // text (toast.js never renders it as HTML), only when short and a string.
  function serverDetail(xhr) {
    if (!/json/i.test(xhr.getResponseHeader("Content-Type") || "")) return null;
    try {
      var detail = JSON.parse(xhr.responseText).detail;
      return typeof detail === "string" && detail.trim() && detail.length <= 200 ? detail.trim() : null;
    } catch (err) {
      return null;
    }
  }

  document.body.addEventListener("htmx:responseError", function (e) {
    var xhr = e.detail.xhr;
    if (xhr.status === 422 || optedOut(e.detail.elt)) return;
    if (/showToast/.test(xhr.getResponseHeader("HX-Trigger") || "")) return;
    var known = STATUS[xhr.status] || {};
    var fallback = xhr.status >= 500
      ? { title: "Server error", message: "Something went wrong on the server (" + xhr.status + ")." }
      : { title: "Request failed", message: "The request failed (" + xhr.status + ")." };
    errorToast(known.title || fallback.title, serverDetail(xhr) || known.message || fallback.message,
      known.kind);
  });

  document.body.addEventListener("htmx:sendError", function (e) {
    if (optedOut(e.detail.elt)) return;
    if (navigator.onLine === false) errorToast("You're offline", "Reconnect and try again.", "warning");
    else errorToast("Can't reach the server", "Check your connection and try again.");
  });

  document.body.addEventListener("htmx:timeout", function (e) {
    if (optedOut(e.detail.elt)) return;
    errorToast("Request timed out", "The server took too long to respond.");
  });
})();
