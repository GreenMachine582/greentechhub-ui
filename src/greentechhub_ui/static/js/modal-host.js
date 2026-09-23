// Server-rendered modal host — see docs/components.md (gth-modal, v0.7).
// A consumer hx-get's a whole gth_modal / gth_confirm_delete into
// app.html's #gth-modal-host; this shows it once swapped in, and hides it
// when a response fires the closeModal HX-Trigger event
// (greentechhub_ui.toast(..., events=["closeModal"])).
//
// The host holds at most one modal: it's emptied once a modal finishes
// hiding, and a modal swapped in over an open one tears the old one down
// first. Removing a shown modal's element directly would leak Bootstrap's
// backdrop and the body's modal-open class/padding.
(function () {
  function host() { return document.getElementById("gth-modal-host"); }
  function modalEl() { return host() && host().querySelector(".modal"); }
  function currentModal() {
    var el = modalEl();
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
  }
  function teardown() {
    var el = modalEl();
    if (!el) return;
    var instance = bootstrap.Modal.getInstance(el);
    if (instance) instance.dispose();
    document.querySelectorAll(".modal-backdrop").forEach(function (b) { b.remove(); });
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }
  document.body.addEventListener("htmx:beforeSwap", function (evt) {
    if (evt.detail.target === host() && evt.detail.shouldSwap) teardown();
  });
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
  // Bootstrap fires hidden.bs.modal on the modal element; it bubbles.
  document.addEventListener("hidden.bs.modal", function (evt) {
    var h = host();
    if (h && h.contains(evt.target)) {
      teardown();
      h.innerHTML = "";
    }
  });
})();
