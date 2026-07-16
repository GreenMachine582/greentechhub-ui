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
- [x] `/playground` app — a minimal FastAPI app (`playground/app.py`) exercising every shipped component with generic fixture data (not BottleBot's domain). No `gth-modal`/`gth-confirm-delete` demo — they don't exist yet. Route-level regression coverage is via `tests/test_playground_smoke.py` at the Jinja-render level (not `fastapi.testclient`/httpx — that dependency chain hit a blocked package install this session, see below); live-verified by running the app and curling every route
- [ ] Playwright smoke tests wired into CI — still separate/deferred; also revisit the `httpx`/`httpx2` situation encountered while building the playground (starlette's `TestClient` in this environment requires `httpx2`, not `httpx` — installing it was blocked by a sandbox permission check this session; `tests/test_playground_smoke.py` currently tests at the Jinja-render level instead of via `TestClient`)
- [ ] `extra_css` / `extra_js` slots
- [ ] `nav_items` custom entries

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one real breaking (major) release

## 🧭 Open Decisions

- [ ] **Logo/brand asset source of truth** — partially resolved: brand *color* now sourced from `GreenMachine582/GreenTechHub`'s real SCSS variables (`#1FBE1E` primary, see `theme/tokens.py`). Still open: logo/favicon image assets exist there (`logo-light.png`/`logo-dark.png` pairs, `icon.png`) but aren't vendored into `greentechhub-ui` yet — `LOGO_URL` stays `None` until that's done.
- [ ] **Static hosting** — bundled-per-service now; revisit shared subdomain (`static.green-tech-hub.com`) later. See [docs/theming.md](docs/theming.md).
- [ ] **Theme/components split** — `theme/` is already structurally independent. Splitting it into a standalone `greentechhub-theme` package is deferred, not rejected — revisit once a real consumer wants branding without the component library (GreenTechHub's Django app is the most likely candidate to force this decision).
- [ ] **How far GreenTechHub's own migration goes** — theme-only vs. full component adoption. Not a blocking decision for v1.0.

## 🔄 Migration Tracking

Per-service retrofit progress — see [docs/migration.md](docs/migration.md) for rationale.

### BottleBot
- [x] Drop custom `static/style.css` overrides in favor of the shared theme (`.metric-card`/`.metric-label`/`.metric-value`/`.metric-delta` removed now that `gth-stat-card` covers them via `theme.css`; remaining rules — deal highlighting, watchlist pills, timeline — are genuinely BottleBot-specific business styling, not theme duplication, and are expected to stay)
- [x] Replace hand-rolled navbar with `gth-navbar`
- [ ] Migrate remaining components one at a time (done so far: `deal.html`'s metric tiles → `gth-stat-card`; dashboard's deals table + both its empty states → `gth-table`/`gth-table_body`/`gth-empty-state`. Remaining: watchlist pagination, other cards, health/criteria tables)

### PyFinBot
- [ ] Build directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start (greenfield, no retrofit needed)

### GreenTechHub
- [ ] Wire Django's Jinja2 backend to validate the [template context contract](docs/contract.md) (before porting real pages)
- [ ] Adopt `theme/` for brand consistency
- [ ] Decide on further component adoption (see Open Decisions above)
