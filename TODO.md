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
- [ ] Sidebar: pinned/favourite items
- [ ] Notifications: a persisted notification centre — a navbar bell with a live `gth_nav_badge` unread count,
  a panel listing read/unread items, the `toast()` payload as the message shape so the same notice can be a
  toast now and an entry later — plus email delivery via the framework adapter (the "system notis/mail" idea)

### Settings & permissions
Rendering for `greentechhub-core`'s settings and role resolution (design:
[core docs/settings.md](https://github.com/GreenMachine582/greentechhub-core/blob/dev/docs/settings.md)). Everything is
opt-in: new behaviour turns on only when the optional context keys (`theme_mode`/`theme_save_url`, `granted`,
`user_menu_items`/`logout_url`, `user_settings`) are present, so it isn't breaking. Macros duck-type attributes, so
there's no runtime import of core. Each PR updates any doc it would otherwise contradict.

Shipped, in cross-repo order: core #1–#4 and #13, fastapi #5, #9 and #11, and ui #6–#8, #10 and #15–#17 (density
and motion, sidebar default, number format), plus the ready-made settings and role-assignment page templates. ui's
half of #12 registered #15–#17, which make ui honour core #13's shared settings from `user_settings`. Open: #19
below (write-only secret fields). Core #14 (the landing page) stays on hold.

#### Secret settings
Settings whose value is a credential (an email app password, an API token) can't be plain settings: stores keep JSON
as-is, `effective()` returns values to templates, and `SettingsViews` echoes a `str` back into the form. These items
add an opt-in **secret** kind across the three packages. Order across repos: core #18 → ui #19 → fastapi #20, then
releases core v0.8.0, ui v0.13.0 and fastapi v0.10.0 (fastapi pins core v0.8.0 first). The first consumer is
PyFinBot's per-user email account for Commsec sync (its app password), registered in PyFinBot's `todo.md`.
- [ ] **#19 `feat(settings): write-only secret fields`**
  - `gth_setting_field` renders a `secret` setting as `type="password"` with an **empty value**, whatever the stored
    value, and `autocomplete="new-password"`. When set, it adds help text ("Saved. Leave blank to keep it.") and a
    "Remove" checkbox (`<key>.__clear`).
  - The value it gets is core's `SECRET_SET` marker or `None`, never the secret.
  - Snapshots, HTML validity, a playground demo (a fake "API token" preference) and `docs/components.md`.

Notes, not items:
- `locale.time_format` already shipped with #10 (`|datetime`).
- The landing page has no ui work. It waits on core #14 (on hold) plus a fastapi redirect.
- Notification preferences wait for the notification centre (Navigation, above).

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
- [ ] Pass `theme_save_url`/`granted`/`user_menu_items`/`logout_url` (via fastapi's `register_settings` context, #9), replacing any hand-rolled theme or nav gating; `user_settings` from the same context is all #15–#17 need

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
