[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open. Sections are themes, not versions: release-please picks the version from the commits.

## 🗺️ Milestones

### Components
- [ ] `gth_record_picker` third size — hand the pick off to the real list screen for full room (e.g. an "Open full page" link carrying `?pick_for=<field>&return=<url>`, the list screen offering a "Use this record" action that returns the pick)

### Navigation
- [ ] Tree-select form field — a `gth_tree` inside the record picker's panel, for picking from a hierarchy
- [ ] Drag-and-drop tree reordering (keyboard-accessible: a "move" mode with arrow keys, not drag-only)
- [ ] Command-palette actions — not just navigation (e.g. "New task", "Toggle theme"), registered like nav items
- [ ] Sidebar: pinned/favourite items (the footer-slot user menu moves to Settings & permissions #8)
- [ ] Notifications: a persisted notification centre — a navbar bell with a live `gth_nav_badge` unread count,
  a panel listing read/unread items, the `toast()` payload as the message shape so the same notice can be a
  toast now and an entry later — plus email delivery via the framework adapter (the "system notis/mail" idea)

### Settings & permissions
Rendering for `greentechhub-core`'s planned settings and role resolution (design:
[core docs/settings.md](https://github.com/GreenMachine582/greentechhub-core/blob/dev/docs/settings.md)). Everything is
opt-in: new behaviour turns on only when the optional context keys (`theme_save_url`, `granted`, `user_settings`)
are present, so it isn't breaking. Macros duck-type attributes, so there's no runtime import of core. Each PR updates
any doc it would otherwise contradict. The numbers are the cross-repo order: core #1–#4 and fastapi #5 come first.
- [ ] **#6 `feat(components): gth_select and settings field rendering`**
  - `gth_select`.
  - `gth_setting_field(setting, value, errors)`: bool → switch, choice with 4 or fewer options → segmented,
    other choices → select, int/str → form field.
  - `gth_settings_section`.
  - Snapshots, a playground `pages/settings.html`, and `docs/components.md`.
- [ ] **#7 `feat(theme): server-persisted theme preference`**
  - The optional `theme_mode` context seeds the anti-FOUC script.
  - `theme-toggle.js` POSTs to an optional `theme_save_url`.
  - localStorage stays as the fallback.
  - Docs: reword `docs/theming.md` (localStorage is no longer the only store); add the optional key to
    `docs/contract.md`.
- [ ] **#8 `feat(navigation): permission-aware nav and navbar user menu`**
  - `filter_by_scope(..., granted=None)` checks `required_permission`, with `required_scope` kept as an alias.
  - A navbar and sidebar-footer user menu (Settings, Logout) driven by `current_user`.
  - Docs: README Navigation row, `docs/extensibility.md`, `docs/components.md`, `navigation.py` docstring.
- [ ] **#10 `feat(formatting): honour timezone, date format and page size`**
  - `format_date`/`format_datetime` read `locale.timezone`/`locale.date_format`.
  - The `TableState` default page size comes from `ui.page_size`.
- [ ] **#12 `docs: scope additional shared settings`** (with core)
  - Compact density for forms and tables, reduced motion, number/currency format, landing page, sidebar default,
    notification preferences.
  - The outcome is newly registered items.

### Display & charts
- [ ] Server-rendered SVG charts, no JS — `gth_sparkline` (also a `gth_stat_card` slot), `gth_bar_chart`,
  `gth_line_chart`: axis labels, theme-token colours, a text summary for screen readers — PyFinBot's dashboard
  and reports until real Grafana panels exist
- [ ] `gth_action_menu` — a row "⋯" dropdown for secondary actions (edit / archive / delete) instead of icon-button
  pairs in table rows
- [ ] `gth_description_list` — key/value details for record pages
- [ ] `gth_timeline` — activity feed (sync runs, audit entries); pairs with the notification centre
- [ ] `gth_progress` — meter/progress bar with an accessible value (sync progress, quotas)
- [ ] `gth_alert_banner` — dismissible site-wide banner (maintenance, degraded service) with an `app.html` slot
- [ ] `gth_embed_card` — iframe card with loading and error states — PyFinBot's Grafana slot

### Resilience & security
- [ ] Top loading bar for htmx requests slower than ~300ms
- [ ] Error pages — `403.html` / `404.html` / `500.html` extending `page.html`, with FastAPI and Django
  exception-handler wiring in the docs
- [ ] CSP-ready shell — move `app.html`'s inline `<script>`s to static files (the pre-paint theme bootstrap
  stays inline behind a `csp_nonce` global) and document a recommended `Content-Security-Policy`
- [ ] **Breaking:** drop the CDN-URL defaults on `bootstrap_css_url`/`bootstrap_js_url`/`htmx_js_url` (overdue);
  services must mount `greentechhub_ui.static_dirs()` for `app.html` to keep working. Also required for a strict
  CSP. Blocked on BottleBot, which still loads Bootstrap/htmx from the CDN defaults — lands after its `install()`
  migration below
- [ ] htmx 2 migration plan — audit our usage against the 2.x breaking changes (`hx-on`, `htmx.config` defaults,
  extensions) and run the playground + e2e suite on 2.x behind a global. Also retires the 1.9.10 bug where one
  `requestCount` is shared between the request-indicator class and `hx-disabled-elt`, so `.htmx-request` sticks
  on an element that is both (why `gth-busy-button` keys on `:disabled`); 1.9.11/1.9.12 don't mention a fix.
  Update `VENDORED.md` hash/size when it lands

### v1.0 — Validated in production
- [ ] BottleBot retrofit shipped
- [ ] PyFinBot greenfield build shipped
- [ ] Django contract validated against GreenTechHub
- [ ] Semver policy held across at least one real minor release
- [ ] Semver policy held across at least one breaking pre-1.0 minor release

## 🔄 Migration Tracking

### BottleBot
- [ ] Adopt `shell_globals()` in `web/templating.py` and `toast(..., events=)` where handlers set several HX-Trigger events
- [ ] Adopt the setup helpers: `greentechhub_ui.install()` (replaces the hand-built `ChoiceLoader` + globals),
  `mount_static_dirs(app, greentechhub_ui.static_dirs())`, `Jinja2Templates(context_processors=[ui_context])` —
  **fixes the navbar never marking the active page** (BottleBot never passes `current_path`) — and
  `hx_response(toast(...))` for the six hand-built 204 + HX-Trigger responses in `routes/scrape.py` /
  `routes/watchlist.py`
- [ ] Decide on the navbar color-mode change — accept the light navbar in light mode, or pin `navbar_theme="dark"`

### PyFinBot
- [ ] Swap the hand-built From/To date inputs in `transactions.html`'s filter bar for `gth_date_range` (same
  `date_from`/`date_to` params, `fy_start_month=7`) once the release carrying it is tagged — `install()` already
  supplies `date_range_js_url`
- [ ] Swap `import.html`'s plain file field for `gth_file_drop("file", "File", accept=ACCEPTED_EXTENSIONS,
  max_size=…)` in the same release, giving drag-and-drop, the type/size check before upload and progress for big
  spreadsheets. The upload route's `File(None)` already avoids the empty-submit JSON 422
- [ ] Drop `templating.py`'s `_money` / `_qty` for the shared `money` / `number` filters that `install()` now
  registers (its own assignments after `install()` win until they're removed). `|string|qty` becomes `|number`, since
  floats are handled. **`money` now prints `$`** (`$1,234.50`), so check the stat cards and report columns and use
  `|money("")` where a `$` is already in the heading. `_fy` stays PyFinBot's own
- [ ] Pass `theme_save_url`/`granted`/`user_settings` (via fastapi's `register_settings` context) once #7/#8 ship, replacing any hand-rolled theme or nav gating

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
