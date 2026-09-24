// HTMX HX-Trigger toast handler — see greentechhub_ui.toast() (Python side).
// Value can be a plain string or {message, kind}. kind: "success" | "info" |
// "warning" | "danger" | "neutral" (aliases: warn, error; anything else is
// neutral). The message is TEXT: it's set with textContent, never parsed as
// HTML, so a message carrying user input can't inject markup.
(function () {
  var KINDS = { success: "success", info: "info", warning: "warning", warn: "warning",
                danger: "danger", error: "danger", neutral: "secondary" };
  // Light fills (warning/info) need the dark close button; the rest white.
  var DARK_CLOSE = { warning: true, info: true };

  document.body.addEventListener("showToast", function (e) {
    var val = e.detail;
    var msg = (typeof val === "object" && val !== null) ? val.message : val;
    var kind = KINDS[(typeof val === "object" && val !== null && val.kind) || "success"] || "secondary";
    var el = document.createElement("div");
    el.className = "toast align-items-center text-bg-" + kind + " border-0";
    el.setAttribute("role", "alert");
    el.setAttribute("aria-live", "assertive");
    el.setAttribute("aria-atomic", "true");
    var row = document.createElement("div");
    row.className = "d-flex";
    var body = document.createElement("div");
    body.className = "toast-body";
    body.textContent = msg == null ? "" : String(msg);
    var close = document.createElement("button");
    close.type = "button";
    close.className = "btn-close me-2 m-auto" + (DARK_CLOSE[kind] ? "" : " btn-close-white");
    close.setAttribute("data-bs-dismiss", "toast");
    close.setAttribute("aria-label", "Close");
    row.append(body, close);
    el.appendChild(row);
    document.getElementById("gth-toast-container").appendChild(el);
    new bootstrap.Toast(el, { delay: 5000 }).show();
  });

  // "Started" toast for long-running actions (gth_busy_button's start_toast):
  // any htmx element with data-gth-start-toast shows it the moment its request
  // goes out; the server's own HX-Trigger toast reports the result later.
  document.body.addEventListener("htmx:beforeRequest", function (e) {
    var message = e.detail.elt.getAttribute && e.detail.elt.getAttribute("data-gth-start-toast");
    if (message) {
      document.body.dispatchEvent(new CustomEvent("showToast", { detail: { message: message, kind: "warning" } }));
    }
  });
})();
