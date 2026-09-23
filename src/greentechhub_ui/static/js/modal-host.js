// Server-rendered modal host — see docs/components.md (gth-modal, v0.7).
// A consumer hx-get's a whole gth_modal / gth_confirm_delete into
// app.html's #gth-modal-host; this shows it once swapped in, and hides it
// when a response fires the closeModal HX-Trigger event
// (greentechhub_ui.toast(..., events=["closeModal"])).
(function () {
  function host() { return document.getElementById("gth-modal-host"); }
  function currentModal() {
    var el = host() && host().querySelector(".modal");
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
  }
  document.body.addEventListener("htmx:afterSwap", function (evt) {
    if (evt.detail.target === host()) {
      var modal = currentModal();
      if (modal) modal.show();
    }
  });
  document.body.addEventListener("closeModal", function () {
    var modal = currentModal();
    if (modal) modal.hide();
  });
})();
