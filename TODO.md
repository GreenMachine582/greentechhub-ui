[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open.

## 🗺️ Milestones

### v0.5 — Local-first static assets
- [ ] v0.6: drop the CDN-URL defaults on `bootstrap_css_url`/`bootstrap_js_url`/`htmx_js_url` once consumers have had a release to pick up the vendored globals — services will need to mount `greentechhub_ui.static` (already required for icons/theme) for `app.html` to keep working

### v0.7 — Components
- [ ] `gth_record_picker` third size — hand the pick off to the real list screen for full room (e.g. an "Open full page" link carrying `?pick_for=<field>&return=<url>`, the list screen offering a "Use this record" action that returns the pick)
- [ ] Bump vendored htmx past 1.9.10: it shares one `requestCount` between the request-indicator class and `hx-disabled-elt`, so `.htmx-request` sticks on an element that is both (why `gth-busy-button` keys on `:disabled`). Checked 2026-09-24: the 1.9.11/1.9.12 changelogs don't mention a fix, so the 1.9.x line can't be assumed to fix it — needs a repro against 1.9.12 (or a 2.x migration plan) before bumping; update `VENDORED.md` hash/size when it lands

### v0.8 — Navigation
- [ ] Tree-select form field — a `gth_tree` inside the record picker's panel, for picking from a hierarchy
- [ ] Drag-and-drop tree reordering (keyboard-accessible: a "move" mode with arrow keys, not drag-only)
- [ ] Command-palette actions — not just navigation (e.g. "New task", "Toggle theme"), registered like nav items
- [ ] Sidebar: pinned/favourite items and a user menu in the footer slot, once a consumer has auth
- [ ] Notifications: a persisted notification centre — a navbar bell with a live `gth_nav_badge` unread count,
  a panel listing read/unread items, the `toast()` payload as the message shape so the same notice can be a
  toast now and an entry later — plus email delivery via the framework adapter (the "system notis/mail" idea)

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one real breaking (major) release

## 🔄 Migration Tracking

### BottleBot
- [ ] Adopt `shell_globals()` in `web/templating.py` and `toast(..., events=)` where handlers set several HX-Trigger events (v0.7)
- [ ] Adopt the v0.9 setup: `greentechhub_ui.install()` (replaces the hand-built `ChoiceLoader` + globals),
  `mount_static_dirs(app, greentechhub_ui.static_dirs())`, `Jinja2Templates(context_processors=[ui_context])` —
  **fixes the navbar never marking the active page** (BottleBot never passes `current_path`) — and
  `hx_response(toast(...))` for the six hand-built 204 + HX-Trigger responses in `routes/scrape.py` /
  `routes/watchlist.py`
- [ ] Decide on the v0.7 navbar color-mode change — accept the light navbar in light mode, or pin `navbar_theme="dark"`

### PyFinBot
- [ ] Build directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start (greenfield, no retrofit needed)
- [ ] Adopt the v0.9 setup: `greentechhub_ui.install()` in `web/templating.py`, `mount_static_dirs` in
  `pyfinbot.py`, `ui_context` (the navbar never marks the active page today — no `current_path`), and replace
  `web/htmx.py`'s `hx_response` with `greentechhub_fastapi.htmx.hx_response(greentechhub_ui.toast(...))`

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
