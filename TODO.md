[← Back to README](README.md)

# ✅ TODO / Milestones

> This file is a living checklist — tick items off as they land instead of regenerating it. See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

## 🗺️ Milestones

### v0.1 — Theme + navigation shell
Enough for BottleBot to swap its navbar and for GreenTechHub to trial the theme-only path.

- [x] `theme/` — tokens, CSS vars, brand ([docs/theming.md](docs/theming.md))
- [x] `gth-navbar`
- [ ] `gth-sidebar`
- [ ] `gth-page-header`
- [x] Base `app.html` shell
- [x] `extra_head` / custom Jinja block extension points ([docs/extensibility.md](docs/extensibility.md))
- [ ] Vendor GreenTechHub's real logo/favicon assets (`logo-light.png`/`logo-dark.png`, `icon.png`) into `static/logo/`; wire `LOGO_URL`

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
- [ ] `gth-modal` (with focus management) — deferred: zero real consumer exists yet (confirmed no modal/delete flow anywhere in BottleBot), and its hardest requirement (focus trap, verified via Bootstrap 5's native Modal component) is runtime browser behavior pytest/html5lib can't verify. Needs the `/playground` app (v0.4) as the only reasonable way to click through and confirm it, rather than bolting a fake delete flow onto BottleBot just to have a consumer
- [ ] `gth-confirm-delete` / `gth-danger-modal` — same deferral as `gth-modal` (built on top of it)
- [x] `gth-toast` — built around BottleBot's real, working `HX-Trigger`/`showToast` event mechanism (the only one with a real consumer), not the documented-but-nonexistent `greentechhub-core` flash module. Ships a `greentechhub_ui.toast()` helper (de-duplicating what was two copies of the same function in BottleBot) and a `gth_toast_flashes` render-only macro for the static `flashes` list the context contract already accepts — flash *production/storage* (session wiring, a Django-messages adapter, etc.) remains an open dependency on `greentechhub-core`, not built here
- [x] ARIA pass across all components so far ([docs/accessibility.md](docs/accessibility.md)) — applied to `gth-navbar`/`gth-stat-card`/`gth-table`/`gth-empty-state` (decorative icons, `<th scope="col">`); `gth-card`/`gth-pagination` needed no changes. `gth-modal`'s ARIA needs its own pass once it ships (see above)

### v0.4 — Dark mode, playground, extension points
- [x] Dark mode — colors and mechanism extracted from the real green-tech-hub.com implementation (`GreenMachine582/GreenTechHub`, `addons/base/static/base/js/widgets/theme.js`), which is vanilla JS, not Alpine (corrected `docs/theming.md`/`docs/architecture.md`, which both claimed Alpine). `gth_theme_toggle` + `localStorage["gth-theme-mode"]` + a `data-bs-theme` anti-FOUC script in `app.html`. Opt-in (`gth_navbar(..., show_theme_toggle=False)`) so no existing consumer's rendered output changes by default — first real consumer: BottleBot, now with the toggle enabled live
- [x] `/playground` app — a minimal FastAPI app (`playground/app.py`) exercising every shipped component with generic fixture data (not BottleBot's domain). No `gth-modal`/`gth-confirm-delete` demo — they don't exist yet. Route-level regression coverage is via `tests/test_playground_smoke.py` at the Jinja-render level (not `fastapi.testclient`/httpx — see [docs/testing.md](docs/testing.md) for why); live-verified by running the app and curling every route
- [x] Playwright smoke tests wired into CI — `tests/e2e/test_playground.py` (`pytest-playwright`, installed cleanly — unrelated to the `httpx2` situation (see [docs/testing.md](docs/testing.md)), which is specific to `starlette.testclient`, a different HTTP-client dependency chain) covers dark-mode toggle + persistence, form validation + success toast, the standalone toast trigger, and table filtering via real keyboard input. No `gth-modal` test — doesn't exist yet. Skips cleanly (`pytest.importorskip`) when `playwright` isn't installed, so the main CI job is unaffected; a separate `e2e` job installs it + Chromium and runs these for real. **Found two real bugs no snapshot test could have caught**: (1) `gth_form` needed `novalidate` — without it, native HTML5 `min`/`max` constraint validation silently blocked the browser from ever submitting an out-of-range value, so the server-side validation path (and `gth-form`'s whole custom error UI) was unreachable; (2) HTMX only swaps 2xx responses by default, so `gth-form`'s 422 validation-error responses were computed correctly server-side but never appeared in the DOM — fixed with the standard `htmx:beforeSwap` override, now in `app.html` for every consumer, not just the playground
- [x] `extra_css` / `extra_js` slots — data-driven context-list slots in `app.html` (`extra_css`/`extra_js`: URL lists; `extra_head`: trusted-HTML strings), distinct from the pre-existing block-based `extra_head`/`extra_js` Jinja blocks. Also finally wired `extra_head`'s context-list form — `docs/contract.md` documented it and the test fixture already accepted it, but nothing rendered it (the same "accepted but unused" gap `flashes` had before dark mode). No real BottleBot consumer yet; verified instead with a `/playground` demo using `data:` URIs (no external dependency) plus a Playwright test asserting the CSS's *computed style* actually applied and the JS actually mutated the DOM — not just markup presence
- [x] `nav_items` custom entries — `navigation.build_nav_items(custom_items, current_user=None, built_in_items=None)` is the real "built-in + consumer-registered, scope-filtered" merge `docs/components.md`'s catalogue already promised (previously only `NavItem`/`filter_by_scope` existed, and `filter_by_scope` itself was dead code — never called anywhere). `built_in_items` defaults to a new `DEFAULT_NAV_ITEMS` constant, empty today (no cross-service nav concept exists yet). First real consumer: BottleBot's `templating.py`, retrofitted to call it instead of assembling `nav_items` by hand — confirmed identical rendered output (same 4 items/icons/order). **v0.4 is now complete.**

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one real breaking (major) release

## 🔄 Migration Tracking

Per-service retrofit progress.

### BottleBot
- [x] Drop custom `static/style.css` overrides in favor of the shared theme (`.metric-card`/`.metric-label`/`.metric-value`/`.metric-delta` removed now that `gth-stat-card` covers them via `theme.css`; remaining rules — deal highlighting, watchlist pills, timeline — are genuinely BottleBot-specific business styling, not theme duplication, and are expected to stay)
- [x] Replace hand-rolled navbar with `gth-navbar`
- [ ] Migrate remaining components one at a time (done so far: `deal.html`'s metric tiles → `gth-stat-card`; dashboard's deals table + both its empty states → `gth-table`/`gth-table_body`/`gth-empty-state`. Remaining: watchlist pagination, other cards, health/criteria tables)

### PyFinBot
- [ ] Build directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start (greenfield, no retrofit needed)

### GreenTechHub
- [ ] Wire Django's Jinja2 backend to validate the [template context contract](docs/contract.md) (before porting real pages)
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
