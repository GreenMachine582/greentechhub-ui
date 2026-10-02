[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open. Sections are themes, not versions: release-please picks the version from the commits.

## 🗺️ Milestones

### Navigation
- [ ] Tree-select form field — a `gth_tree` inside the record picker's panel, for picking from a hierarchy
- [ ] Drag-and-drop tree reordering (keyboard-accessible: a "move" mode with arrow keys, not drag-only)
- [ ] Command-palette actions — not just navigation (e.g. "New task", "Toggle theme"), registered like nav items
- [ ] Sidebar: pinned/favourite items
- [ ] Notifications: a persisted notification centre — a navbar bell with a live `gth_nav_badge` unread count,
  a panel listing read/unread items, the `toast()` payload as the message shape so the same notice can be a
  toast now and an entry later — plus email delivery via the framework adapter (the "system notis/mail" idea);
  its user preferences (core settings) come with it

### Display & charts
- [ ] Server-rendered SVG charts, no JS — `gth_sparkline` (also a `gth_stat_card` slot), `gth_bar_chart`,
  `gth_line_chart`: axis labels, theme-token colours, a text summary for screen readers — PyFinBot's dashboard
  and reports until real Grafana panels exist
- [ ] `gth_timeline` — activity feed (sync runs, audit entries); pairs with the notification centre
- [ ] `gth_embed_card` — iframe card with loading and error states — PyFinBot's Grafana slot
- [ ] `gth_code` — a read-only code block for config snippets, API examples, JSON payloads and logs (a sync run's raw
  response)
  - `gth_code(code, language=None, filename=None, copy=True, line_numbers=False, highlight=(), max_height=None,
    wrap=False)`, plus an inline `gth_code_inline(text, copy=False)`.
  - A header strip with the filename and/or language and a Copy button (clipboard, a "Copied" tick, a toast as the
    fallback); the body an escaped `<pre><code>` with an optional line-number gutter (CSS counters, so copying skips
    them), highlighted lines and a `max_height` scroll box.
  - Syntax colours from server-side Pygments when an optional `[highlight]` extra is installed, else plain text;
    token colours from theme variables so light and dark both work.

### Data & forms
- [ ] `gth_query_builder` — an "Advanced filter" for `gth_data_table`, beyond the search box and chips
  - `gth_query_builder(name, fields, value=None, table=None, max_rows=10)`; fields are duck-typed
    `{"key", "label", "type": "text|number|date|choice|bool", "choices"?, "operators"?}`.
  - Rows of [field] [operator] [value]: the operator list follows the field's type, from greentechhub-core's
    `Operator` (eq, ne, gt…, in, contains, is_null), and the value input does too (text, number, date, a choice
    multiselect for `in`, nothing for `is_null`). Add/remove rows, an all/any (AND/OR) toggle, at most one level of
    nested groups.
  - Serialises to one hidden JSON field (`[{"field", "op", "value"}]`) that core's `Filter` can parse; a
    greentechhub-fastapi helper validates it against the allowed fields and operators (like `TableState`'s
    `filter_params` allow-list). The table re-request keeps it in the URL, so a filtered view is shareable.
  - A collapsible panel under `gth_table_filter`, summarised as chips when collapsed ("Stock < 50 · Category in
    Sensor, Motor"). Later: saved filters per user (core settings).

### From the PyFinBot review (next release, one PR each)
Hand-rolled markup PyFinBot repeats that belongs here, so it can drop its own copies:
- [ ] Row actions column — `gth_data_table(row_actions=True, row_actions_label="Actions")` adds a trailing header
  with a visually-hidden label, no `data-gth-col` (so `view_options` never lists or hides it) and one more colspan;
  rows end with `gth_table_actions_cell(items, label=None, inline=None)`, a `<td>` around `gth_action_menu`
  (`inline=None`: all icon buttons, as apps have today). Mirrors `bulk_actions` + `gth_table_select_cell`. Today a
  blank `""` header shows in the View menu as an unlabelled, hideable toggle
- [ ] `gth_busy_button(..., submit=True)` — a `type="submit"` busy button with optional `hx_attrs`, driven by the
  form's `hx-disabled-elt` (PyFinBot hand-copies the idle/busy spans on its import and dividend forms)
- [ ] `gth_alert(message, tone="info", heading=None, action=None, html=False, dismissible=False)` — an inline
  alert; shares `gth_alert_banner`'s tone → class/icon/role and safe-action rules via one internal macro
  (PyFinBot writes raw `<div class="alert">` in five places)
- [ ] `gth_select(..., hide_label=True)` — a visually-hidden label for filter bars, like `gth_date_range`'s
  (PyFinBot hand-builds every filter-bar select)
- [ ] `login_page.html` — a local-auth login page (`gth_form` + `gth_form_field`, the error as `gth_alert`) that
  greentechhub-fastapi's `LoginViews` defaults to, so apps stop owning `login.html`. After `gth_alert`; the
  fastapi half is in its TODO

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
