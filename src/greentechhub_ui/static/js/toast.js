// HTMX HX-Trigger toast handler — see greentechhub_ui.toast() (Python side).
// Value can be a plain string or {message, kind} where kind is "success"|"warning"|"danger"
document.body.addEventListener("showToast", function (e) {
  var val = e.detail;
  var msg = (typeof val === "object" && val.message) ? val.message : val;
  var kind = (typeof val === "object" && val.kind) ? val.kind : "success";
  var colorMap = { success: "text-bg-success", warning: "text-bg-warning", danger: "text-bg-danger" };
  var cls = colorMap[kind] || "text-bg-success";
  var el = document.createElement("div");
  el.className = "toast align-items-center " + cls + " border-0";
  el.setAttribute("role", "alert");
  el.setAttribute("aria-live", "assertive");
  el.innerHTML = '<div class="d-flex"><div class="toast-body">' + msg
    + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>';
  document.getElementById("gth-toast-container").appendChild(el);
  new bootstrap.Toast(el, { delay: 5000 }).show();
});
