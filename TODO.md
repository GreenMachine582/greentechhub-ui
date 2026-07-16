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
- [ ] `gth-card`
- [ ] `gth-stat-card`
- [ ] `gth-table`
- [ ] `gth-pagination`
- [ ] `gth-empty-state`
- [ ] Macro snapshot tests in CI ([docs/testing.md](docs/testing.md))
- [ ] HTML validation in CI

### v0.3 — Forms, modals, feedback
- [ ] `gth-form`
- [ ] `gth-modal` (with focus management)
- [ ] `gth-confirm-delete` / `gth-danger-modal`
- [ ] `gth-toast` (paired with `greentechhub-core`'s `flash` module)
- [ ] ARIA pass across all components so far ([docs/accessibility.md](docs/accessibility.md))

### v0.4 — Dark mode, playground, extension points
- [ ] Dark mode
- [ ] `/playground` app
- [ ] Playwright smoke tests wired into CI
- [ ] `extra_css` / `extra_js` slots
- [ ] `nav_items` custom entries

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one real breaking (major) release

## 🧭 Open Decisions

- [ ] **Icon set** — pick one (Bootstrap Icons is the path of least resistance given the vendored CSS framework) rather than mixing icon libraries per service.
- [ ] **Logo/brand asset source of truth** — identify wherever green-tech-hub.com's current brand assets live as the canonical source `greentechhub-ui` packages.
- [ ] **Static hosting** — bundled-per-service now; revisit shared subdomain (`static.green-tech-hub.com`) later. See [docs/theming.md](docs/theming.md).
- [ ] **Theme/components split** — `theme/` is already structurally independent. Splitting it into a standalone `greentechhub-theme` package is deferred, not rejected — revisit once a real consumer wants branding without the component library (GreenTechHub's Django app is the most likely candidate to force this decision).
- [ ] **How far GreenTechHub's own migration goes** — theme-only vs. full component adoption. Not a blocking decision for v1.0.

## 🔄 Migration Tracking

Per-service retrofit progress — see [docs/migration.md](docs/migration.md) for rationale.

### BottleBot
- [ ] Drop custom `static/style.css` overrides in favor of the shared theme (audited: current overrides are all domain-specific — deal highlighting, watchlist pills, metric cards, timeline — none duplicate shared theme tokens yet, so nothing to drop until more components migrate)
- [x] Replace hand-rolled navbar with `gth-navbar`
- [ ] Migrate remaining components one at a time

### PyFinBot
- [ ] Build directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start (greenfield, no retrofit needed)

### GreenTechHub
- [ ] Wire Django's Jinja2 backend to validate the [template context contract](docs/contract.md) (before porting real pages)
- [ ] Adopt `theme/` for brand consistency
- [ ] Decide on further component adoption (see Open Decisions above)
