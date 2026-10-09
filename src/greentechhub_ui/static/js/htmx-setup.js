// gth htmx setup — app.html loads this right after htmx (htmx_setup_js_url,
// v0.17); without it app.html inlines the same handler.
//
// gth-form's validation-error responses use 422 (correct REST semantics), but
// htmx only swaps 2xx responses by default — this treats 422 as swappable
// too, htmx's own documented pattern for exactly this. Without it, gth-form's
// inline errors are computed server-side but never appear in the DOM.
document.addEventListener("htmx:beforeSwap", function (evt) {
  if (evt.detail.xhr.status === 422) {
    evt.detail.shouldSwap = true;
  }
});

// gth_table_filter: its search box's own `change` (fired on blur, e.g. by the
// mousedown of a click on a row) must not re-request the table — typing is
// already covered by the debounced `input`. Done here rather than as an
// hx-trigger filter (change[target.type!='search']), which htmx evaluates
// with eval and a Content-Security-Policy without 'unsafe-eval' blocks.
document.addEventListener("htmx:confirm", function (evt) {
  var e = evt.detail.triggeringEvent;
  if (e && e.type === "change" && e.target && e.target.type === "search" &&
      evt.detail.elt.classList && evt.detail.elt.classList.contains("gth-table-filter")) {
    evt.preventDefault();
  }
});
