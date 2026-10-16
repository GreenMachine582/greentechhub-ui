[← Back to README](../README.md)

# htmx 2 migration

**Since v0.19 (breaking), gth-ui ships htmx 2.0.11** as `static/js/htmx.min.js` (see
[VENDORED.md](../src/greentechhub_ui/static/VENDORED.md)), and `shell_globals()` / `install()` load it by default.

v0.19 kept htmx **1.9.10** for one release as an opt-out (`shell_globals(htmx=1)`). **v0.20 removed it**
(breaking): `htmx=1` now raises a `ValueError`, and `static/js/htmx-1.min.js` is gone. CI's `e2e` job runs the whole
e2e suite on 2.x.

## Upgrading a service

gth-ui's own components need nothing: the audit below covers every one of them, and the e2e suite passes on 2.x. A service's **own** templates and scripts may, if they use any of these:

- **`hx-delete` inside a form:** 2.x sends its values as query parameters, not a body. Read them from the query
  string, send a CSRF token as a header (greentechhub-ui's shell already sends `X-CSRF-Token` through
  `hx-headers`), or set `htmx.config.methodsThatUseUrlParams = ["get"]`.
- **Cross-origin htmx requests** are refused (`selfRequestsOnly` is on). Keep htmx URLs on the service's own
  origin.
- **`hx-on="event: …"`** is gone. Use `hx-on:event` / `hx-on::event`, or better, no `hx-on` at all: the strict CSP
  rules it out.
- **Extensions** (`hx-ext`, `hx-ws`, `hx-sse`) are separate packages. Vendor the 2.x build of any you use.
- **`scrollBehavior`** defaults to `instant` (was `smooth`) for `show:` / `scroll:` swap modifiers and `hx-boost`.

There's no opt-out any more (v0.20). A service that needs more time stays on greentechhub-ui v0.19, where
`shell_globals(htmx=1)` still works.

## Status

**The full e2e suite passes on 2.0.11 unchanged** (133 tests, the same as on 1.9.10). That includes the
modal host, combobox, record picker, data tables (load more, infinite scroll, bulk, export), tree lazy loading,
file-drop upload progress, toasts and error toasts, notifications, the settings and roles pages, and the 422
form-error swaps.

## Audit: the 2.x breaking changes against gth-ui

The "2.0.11" column is from htmx 2.0.11's source (`htmx.config` defaults and event code). The "gth-ui" column is
from a search of every component, template and script here.

| Change in 2.x | 2.0.11 | gth-ui |
|---|---|---|
| `hx-on="event: …"` removed (now `hx-on:event` / `hx-on::event`) | — | **not used**. No component uses `hx-on` in either form. |
| Extensions (`hx-ext`, `hx-ws`, `hx-sse`) no longer in core | separate packages | **not used** |
| `scrollBehavior` default `smooth` → `instant` | `'instant'` | **no effect**: no component uses `show:` / `scroll:` swap modifiers or `hx-boost`. Instant is also what reduced motion wants. |
| `methodsThatUseUrlParams` adds `delete`: `hx-delete` sends its values as query params, not a body | `['get', 'delete']` | **no effect on components**: `gth_confirm_delete`'s DELETE button isn't inside a form, so it sends no values, and the playground's DELETE routes read only the path. **A service** whose `hx-delete` sits in a form and reads its body (e.g. a CSRF token field) must read query params, send the token as a header (greentechhub-fastapi's planned htmx CSRF uses `hx-headers`), or set `methodsThatUseUrlParams: ["get"]`. |
| `selfRequestsOnly` default `false` → `true`: cross-origin htmx requests refused | `true` | **no effect**: every component URL is the service's own. `gth_embed_card` is an iframe, not an htmx request. |
| `historyRestoreAsHxRequest: true`: a history-cache miss reload sends `HX-Request: true` | `true` | **already handled**: `greentechhub_ui.htmx.wants_fragment()` returns False when `HX-History-Restore-Request: true` is also sent (2.0.11 sends both), so the miss gets the whole page. |
| `responseHandling` replaces the 2xx-only swap rule; 4xx/5xx are `error: true, swap: false` | new | **same result**: app.html's `htmx:beforeSwap` handler still makes 422 swappable. 2.x still fires `htmx:responseError` for it, as 1.9.10 does, and toast.js already ignores 422. Later this could become a `responseHandling` entry instead of the handler. |
| `useTemplateFragments` removed (responses always parsed through `<template>`) | — | **no effect**: the e2e table-body (`<tr>`) swaps pass on 2.x. |
| `inlineStyleNonce` (new) | `''` | for the CSP-ready shell (greentechhub-ui#102): with it, htmx's indicator `<style>` could stay under a nonce rather than be turned off |
| `htmx:confirm` and its `triggeringEvent` (the CSP-ready shell, greentechhub-ui#102, uses it for `gth_table_filter`) | unchanged | unchanged |
| Events and API used by gth-ui: `htmx:load`, `beforeRequest`, `beforeSend`, `beforeSwap`, `afterSwap`, `afterSettle`, `afterRequest`, `configRequest`, `responseError`, `sendError`, `timeout`, `xhr:progress`; `htmx.ajax` | unchanged | unchanged. Each still exists with the same detail properties gth-ui reads. |

### The 1.9.10 `requestCount` bug

htmx 1.9.10 shares one `requestCount` per element between the request-indicator class and `hx-disabled-elt`, so
`.htmx-request` sticks on an element that is both. That's why `gth-busy-button` keys its busy styling on
`:disabled`. **2.0.11 fixes it.** `test_busy_button_request_class_clears` (e2e) asserts the class clears on 2.x.
`gth-busy-button` and `theme.css` could key on `.htmx-request` again now, but `:disabled` keeps working, so that
change is optional.

## The switch (a breaking release, v0.19: done)

1. ~~Make `htmx=2` the default~~: done. `js/htmx.min.js` is 2.0.11, and 1.9.10 moved to `js/htmx-1.min.js` for the
   one-release `htmx=1` opt-out.
2. ~~Change the CDN default on `htmx_js_url`~~: done. v0.19 drops the CDN-URL defaults, so `htmx_js_url` only
   ever comes from `shell_globals()`.
3. ~~Release notes~~: done. They're the `feat!:` PR's `BREAKING CHANGE:` and "Upgrading a service" above.
4. ~~Drop the `e2e-htmx2` job~~: done. `e2e` runs on 2.x, and the job became `e2e-htmx1` for the opt-out.
5. ~~Drop the `htmx=1` opt-out~~: done in v0.20. `htmx=1` raises, and `js/htmx-1.min.js`, the `e2e-htmx1` job
   and the 1.x half of the busy-button e2e test are gone.
