[← Back to README](../README.md)

# htmx 2 migration

gth-ui ships htmx **1.9.10** (`static/js/htmx.min.js`). htmx **2.0.11** is vendored beside it
(`static/js/htmx-2.min.js`, see [VENDORED.md](../src/greentechhub_ui/static/VENDORED.md)), and a service opts in
with `shell_globals(htmx=2)`, which sets `htmx_js_url` to it. The default stays 1 until the switch below lands.

The playground runs on 2.x with `PLAYGROUND_HTMX=2`. CI's `e2e-htmx2` job runs the whole e2e suite that way on
every PR, beside the usual `e2e` job on 1.9.10.

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
`:disabled`. **2.0.11 fixes it.** `test_busy_button_request_class_on_each_htmx` (e2e) asserts the class sticks on
1.x and clears on 2.x. After the switch, `gth-busy-button` and `theme.css` could key on `.htmx-request` again, but
`:disabled` keeps working, so that change is optional.

## The switch (a breaking release)

1. Make `htmx=2` the default: `js/htmx.min.js` becomes 2.0.x and `htmx-2.min.js` and its VENDORED.md row go.
   Keep `htmx=1` for one release if a consumer needs it.
2. Change the CDN default on `htmx_js_url` to the 2.x URL, or drop it with the planned "drop the CDN-URL
   defaults" item, which is the better order.
3. Release notes, as the `feat!:` PR's `BREAKING CHANGE:`: the service-side items above (`hx-delete` values in the
   query string, same-origin-only requests, and their own `hx-on` / extensions), with this table.
4. Drop the `e2e-htmx2` job once `e2e` itself runs on 2.x.
