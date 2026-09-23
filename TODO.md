[← Back to README](README.md)

# ✅ TODO / Milestones

> This file is a living checklist — tick items off as they land instead of regenerating it. See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

## 🗺️ Milestones

### v0.1 — Theme + navigation shell
Enough for BottleBot to swap its navbar and for GreenTechHub to trial the theme-only path.

- [x] `theme/` — tokens, CSS vars, brand ([docs/theming.md](docs/theming.md))
- [x] `gth-navbar`
- [x] `gth-page-header` — `gth_page_header(title, subtitle=None, breadcrumbs=None, header_class="")`; `gth-breadcrumbs` folded in as the `breadcrumbs` param (`<nav aria-label="breadcrumb">`, last entry current/`aria-current="page"`) rather than shipped as its own macro. Snapshot-tested (bare/breadcrumbs/action variants) and demoed live in `playground/templates/index.html`, replacing its own hand-rolled `<h1>` + intro paragraph
- [x] Base `app.html` shell
- [x] `extra_head` / custom Jinja block extension points ([docs/extensibility.md](docs/extensibility.md))
- [x] Custom abstract logo (`static/logo/logo.png` + `logo-light.png`, green circuit/leaf mark) designed for `greentechhub-ui`'s own brand identity — intentionally decoupled from GreenTechHub production's current logo file (see `static/VENDORED.md`). Wired via `theme.brand_context(show_logo=True, static_url_prefix=...)`, opt-in so no existing consumer's output changes by default. `logo_url` (navbar, hardcoded dark background) uses the original; `favicon_url` (browser chrome, unpredictable background) uses the stronger-outlined `logo-light.png`

### v0.2 — Core content components
- [x] `gth-card`
- [x] `gth-stat-card`
- [x] `gth-table`
- [x] `gth-pagination`
- [x] `gth-empty-state`
- [x] Macro snapshot tests in CI ([docs/testing.md](docs/testing.md))
- [x] HTML validation in CI
- [x] Vendor Bootstrap Icons as the icon-font (`static/icons/`) — corrected from the original "SVG sprite, not icon-font" wording: measured on the wire (v1.13.1), the icon-font (CSS+woff2) is ~147.6 KB vs. the SVG sprite's ~211.7 KB, and upstream hasn't deprecated the icon-font method (both remain co-equal documented options). Also matches the icon-font markup (`bi bi-*`) `gth-navbar`/`gth-stat-card` already shipped with v0.2, so no macro changes were needed. First real consumer: BottleBot's navbar nav items.

### v0.3 — Forms, modals, feedback
- [x] `gth-form` — first real consumer: BottleBot's `/criteria` form, which also gained real per-field validation errors (mapped from Pydantic's `exc.errors()`) it didn't have before, not just a markup swap
- [x] `gth-modal` (with focus management) — built against Bootstrap's own native Modal JS (already vendored); focus-trap and runtime `aria-modal`/`aria-hidden` toggling come free from that JS, the macro itself only wires the static markup + `aria-labelledby`. `gth_modal(id, title, size=None, static_backdrop=False)`, body via `{% call %}`. Verified for real in `/playground` with Playwright: open → focus lands on the modal → Tab reaches the close button → Esc closes → focus returns to the trigger
- [x] `gth-confirm-delete` / `gth-danger-modal` — `gth_confirm_delete(id, target_url, item_label, hx_target=None)` = `gth_modal` + a danger button wired with `hx-delete`/`hx-target`, deliberately no `hx-confirm` (the modal itself is the confirmation). Demoed in `/playground` against a watchlist fixture — BottleBot's real motivating case (removing a watched item is destructive even though currently un-confirmed) — and covered by an e2e test that actually removes an item via a real HTMX round-trip
- [x] `gth-toast` — built around BottleBot's real, working `HX-Trigger`/`showToast` event mechanism (the only one with a real consumer), not the documented-but-nonexistent `greentechhub-core` flash module. Ships a `greentechhub_ui.toast()` helper (de-duplicating what was two copies of the same function in BottleBot) and a `gth_toast_flashes` render-only macro for the static `flashes` list the context contract already accepts — flash *production/storage* (session wiring, a Django-messages adapter, etc.) is owned by the framework adapter (`greentechhub_fastapi.flash` / a Django messages bridge), not built here or in `greentechhub-core`, which only owns the `FlashMessage` value type
- [x] ARIA pass across all components so far ([docs/accessibility.md](docs/accessibility.md)) — applied to `gth-navbar`/`gth-stat-card`/`gth-table`/`gth-empty-state` (decorative icons, `<th scope="col">`); `gth-card`/`gth-pagination` needed no changes. `gth-modal`'s ARIA pass is done now too (see above) — `docs/accessibility.md` updated to match

### v0.4 — Dark mode, playground, extension points
- [x] Dark mode — colors and mechanism extracted from the real green-tech-hub.com implementation (`GreenMachine582/GreenTechHub`, `addons/base/static/base/js/widgets/theme.js`), which is vanilla JS, not Alpine (corrected `docs/theming.md`/`docs/architecture.md`, which both claimed Alpine). `gth_theme_toggle` + `localStorage["gth-theme-mode"]` + a `data-bs-theme` anti-FOUC script in `app.html`. Opt-in (`gth_navbar(..., show_theme_toggle=False)`) so no existing consumer's rendered output changes by default — first real consumer: BottleBot, now with the toggle enabled live
- [x] `/playground` app — a minimal FastAPI app (`playground/app.py`) exercising every shipped component with generic fixture data (not BottleBot's domain). No `gth-modal`/`gth-confirm-delete` demo — they don't exist yet. Route-level regression coverage is via `tests/test_playground_smoke.py` at the Jinja-render level, plus `tests/test_playground_routes.py` at the real HTTP level (`httpx`/`ASGITransport` — see [docs/testing.md](docs/testing.md)); live-verified by running the app and curling every route
- [x] Playwright smoke tests wired into CI — `tests/e2e/test_playground.py` (`pytest-playwright`, installed cleanly) covers dark-mode toggle + persistence, form validation + success toast, the standalone toast trigger, and table filtering via real keyboard input. No `gth-modal` test — doesn't exist yet. Skips cleanly (`pytest.importorskip`) when `playwright` isn't installed, so the main CI job is unaffected; a separate `e2e` job installs it + Chromium and runs these for real. **Found two real bugs no snapshot test could have caught**: (1) `gth_form` needed `novalidate` — without it, native HTML5 `min`/`max` constraint validation silently blocked the browser from ever submitting an out-of-range value, so the server-side validation path (and `gth-form`'s whole custom error UI) was unreachable; (2) HTMX only swaps 2xx responses by default, so `gth-form`'s 422 validation-error responses were computed correctly server-side but never appeared in the DOM — fixed with the standard `htmx:beforeSwap` override, now in `app.html` for every consumer, not just the playground
- [x] `extra_css` / `extra_js` slots — data-driven context-list slots in `app.html` (`extra_css`/`extra_js`: URL lists; `extra_head`: trusted-HTML strings), distinct from the pre-existing block-based `extra_head`/`extra_js` Jinja blocks. Also finally wired `extra_head`'s context-list form — `docs/contract.md` documented it and the test fixture already accepted it, but nothing rendered it (the same "accepted but unused" gap `flashes` had before dark mode). No real BottleBot consumer yet; verified instead with a `/playground` demo using `data:` URIs (no external dependency) plus a Playwright test asserting the CSS's *computed style* actually applied and the JS actually mutated the DOM — not just markup presence
- [x] `nav_items` custom entries — `navigation.build_nav_items(custom_items, current_user=None, built_in_items=None)` is the real "built-in + consumer-registered, scope-filtered" merge `docs/components.md`'s catalogue already promised (previously only `NavItem`/`filter_by_scope` existed, and `filter_by_scope` itself was dead code — never called anywhere). `built_in_items` defaults to a new `DEFAULT_NAV_ITEMS` constant, empty today (no cross-service nav concept exists yet). First real consumer: BottleBot's `templating.py`, retrofitted to call it instead of assembling `nav_items` by hand — confirmed identical rendered output (same 4 items/icons/order). **v0.4 is now complete.**

### v0.5 — Local-first static assets
`app.html` hardcoded Bootstrap/HTMX CDN URLs directly, contradicting the "vendored"/"bundled per service" posture the rest of this package's own docs already claimed.

- [x] Vendor Bootstrap CSS/JS + HTMX (`static/css/`, `static/js/`, source URLs/versions/SHA256 in [static/VENDORED.md](src/greentechhub_ui/static/VENDORED.md)) — `app.html` resolves them via new `bootstrap_css_url`/`bootstrap_js_url`/`htmx_js_url` globals ([docs/contract.md](docs/contract.md#static-asset-globals)), defaulting to the previous CDN URLs for this release so no existing consumer's output changes
- [x] Remove Alpine.js from the README badge row and Scope prose — nothing shipped uses it (dark mode is vanilla JS; `gth-modal` doesn't exist yet); revisit vendoring once a real component needs it
- [ ] v0.6: drop the CDN-URL defaults on `bootstrap_css_url`/`bootstrap_js_url`/`htmx_js_url` once consumers have had a release to pick up the vendored globals — services will need to mount `greentechhub_ui.static` (already required for icons/theme) for `app.html` to keep working

### v0.7 — Components
- [x] `toast(..., events=[...])` — merge extra HX-Trigger events (`closeModal`, table-refresh events) into the one header
- [x] Modal host — `#gth-modal-host` in `app.html` + `modal-host.js`: server-rendered `gth_modal`s shown on swap, closed by the `closeModal` event (the "HTMX-loadable" `gth-modal` the catalogue always promised)
- [x] `gth_table_load_more` — `gth_pagination`'s table-row sibling (its fixed `hx-target="this"` can't append `<tr>`s)
- [x] `gth_busy_button` + `data-gth-start-toast` in `toast.js` — busy styling keyed on `:disabled` (see the htmx item below)
- [x] `gth_combobox` / `gth_combobox_option` / `gth_combobox_empty` + `combobox.js`
- [x] `gth_segmented` — `btn-check` radio group
- [x] `shell_globals()` — all `app.html` globals in one call, vendored asset URLs included; BottleBot, PyFinBot and the playground each hand-set ~10 of them
- [x] `next_url|e` in `gth_pagination`/`gth_table_load_more` — an unescaped `&` broke strict HTML parsing when autoescape is off
- [ ] Bump vendored htmx past 1.9.10: it shares one `requestCount` between the request-indicator class and `hx-disabled-elt`, so `.htmx-request` sticks on an element that is both (why `gth-busy-button` keys on `:disabled`). Confirm the fixing version in htmx's changelog; update `VENDORED.md` hash/size

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one real breaking (major) release

### Post-v1.0 — Deferred
- [ ] `gth-sidebar` — deferred: every current consumer fits a navbar; revisit when a consumer has >6 nav items (forces an `app.html` grid layout decision no one has asked for)

## 🔄 Migration Tracking

Per-service retrofit progress.

### BottleBot
- [x] Drop custom `static/style.css` overrides in favor of the shared theme (`.metric-card`/`.metric-label`/`.metric-value`/`.metric-delta` removed now that `gth-stat-card` covers them via `theme.css`; remaining rules — deal highlighting, watchlist pills, timeline — are genuinely BottleBot-specific business styling, not theme duplication, and are expected to stay)
- [x] Replace hand-rolled navbar with `gth-navbar`
- [x] Migrate remaining components one at a time (done: `deal.html`'s metric tiles → `gth-stat-card`; dashboard's deals table + both its empty states → `gth-table`/`gth-table_body`/`gth-empty-state`; watchlist pagination → `gth-pagination`; health tables (`_scrape_runs_table.html`, `_notification_log_table.html`) and criteria tables → `gth-table`/`gth-table_body`; other cards — done 2026-09-22, `deal.html`'s main product card and `_watchlist_product_card.html` → `gth-card`)
- [ ] Adopt `shell_globals()` in `web/templating.py` and `toast(..., events=)` where handlers set several HX-Trigger events (v0.7)

### PyFinBot
- [ ] Build directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start (greenfield, no retrofit needed)

### GreenTechHub
- [x] Wire Django's Jinja2 backend to validate the [template context contract](docs/contract.md) — `tests/test_contract_django.py` (optional `django` extra, `pytest.importorskip`) renders `app.html` through `django.template.backends.jinja2.Jinja2` pointed at `greentechhub_ui.templates_path`/`components_path` with the same minimal contract context `test_app_shell_renders.py` uses for FastAPI, proving the macros are genuinely framework-agnostic. This validates the contract itself, not a real GreenTechHub page — porting real pages is still separate work, below
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
