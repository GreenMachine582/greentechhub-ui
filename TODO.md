[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open. Sections are themes, not versions: release-please picks the version from the commits.

## 🗺️ Milestones

Cross-repo order (with greentechhub-core and greentechhub-fastapi): Accounts (M1) → Notifications & email (M2) →
consumers live (M3) → ui breaking release (M4) → display & data (M5) → v1.0.

### Navigation
- [ ] Tree-select form field — a `gth_tree` inside the record picker's panel, for picking from a hierarchy
- [ ] Drag-and-drop tree reordering (keyboard-accessible: a "move" mode with arrow keys, not drag-only)
- [ ] Command-palette actions — not just navigation (e.g. "New task", "Toggle theme"), registered like nav items
- [ ] Sidebar: pinned/favourite items

### Display & charts
- [ ] Server-rendered SVG charts, no JS — `gth_sparkline` (also a `gth_stat_card` slot), `gth_bar_chart`,
  `gth_line_chart`: axis labels, theme-token colours, a text summary for screen readers — PyFinBot's dashboard
  and reports until real Grafana panels exist
- [ ] `gth_timeline` — activity feed (sync runs, audit entries) fed by core's audit log (`AuditStore`, core v0.10); pairs with the
  notification centre
- [ ] `gth_embed_card` — iframe card with loading and error states, passing the current theme to Grafana panels —
  PyFinBot's Grafana slot
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

### Development
- [ ] `chore(dev): local GTH mode` — `scripts/use-local-gth.sh` and a CONTRIBUTING pointer, as in
  greentechhub-fastapi and PyFinBot (core's `scripts/local_gth.py` is on `dev`); links the sibling core and fastapi
  checkouts into `.venv`

### Leaner services — from the PyFinBot review (2026-10-07)
A review of PyFinBot's templates found markup it repeats that this package could own, and two adapter
assumptions. One PR each; PyFinBot's `todo.md` lists what it drops when it adopts them.

- [ ] U2. `fix(forms)`: `id=` on `gth_segmented` and `gth_switch`
  - **Why:** v0.15 added the `id=` prefix to `gth_select`/`gth_form_field` only; the others still hard-code
    `gth-field-{{ name }}` and collide when a page has two with the same name.
- [ ] U3. New macros for markup services repeat, ranked by how often PyFinBot repeats each:
  1. `gth_result_panel(heading, badges, problems=None, error=None, link=None)` — an operation's result: an error
     alert, or a card of count badges, a problems list (a `caller()` slot for a table) and a follow-up link.
     PyFinBot's `_import_result.html` and `_sync_result.html` are the same card; it pairs with `gth_timeline`
     later. Its `aria-live` target slot is repeated in 3 pages too.
  2. `gth_filter_bar(url, target, export_url=None)` with a `caller()` slot for fields, plus a public
     `gth_download_button(url, label="CSV")` — for panes that use a plain `gth_table`, not `TableState`.
     PyFinBot's three report panes repeat it; the download markup exists privately in `table.html`.
  3. `gth_form_actions(submit_label="Save", cancel=True, busy_label=None)`, and optionally
     `gth_modal_form(id, title, action, size=None)` (`gth_modal` + `gth_form` + the standard htmx attributes +
     actions). The Cancel/Save row is in PyFinBot's stock and transaction forms and in this package's own
     `confirm_delete.html`; `gth_modal` has no footer slot.
  4. A signed-amount tone — a `tone` filter or `gth_amount(value, kind="money")` adding `text-success`/
     `text-danger`, next to `formatting.py`'s `money` (PyFinBot hand-writes it 3×).
  5. A `fy` filter giving the same label as core's `fiscal_year_label` (ui doesn't import core at runtime, so a
     test pins the two together; PyFinBot registers its own today).
  6. `gth_stat_grid(cards, cols=…)` for the `row`/`col` wrappers around `gth_stat_card` (4 PyFinBot pages).

### Ideas — not scheduled
- App switcher — a navbar grid menu linking the gth apps (BottleBot, PyFinBot, Market Watch, hardware-ledger), set in
  config; with Authentik SSO, moving between them needs no extra sign-in
- Templates for greentechhub-fastapi's planned admin views — an Admin nav group, users admin, a system status page
  (a status badge per health check)
- First-run setup wizard on a new `gth_stepper` multi-step form — create the admin, name the site, pick a landing page
- Customisable dashboard — users arrange and resize stat cards and widgets; the layout saved in settings
- `gth_kanban` — columns by status, htmx drag between them, a keyboard move mode like the tree reorder
- `gth_calendar` — month and agenda views for scheduled jobs, dividends and due dates
- Keyboard shortcut overlay — `?` lists shortcuts; apps register their own, like command-palette actions
- `print.html` — a print/PDF base with clean typography for reports
- Undo toasts — "Deleted 3 items · Undo", a toast action over a soft delete
- Inline cell editing in `gth_data_table` — click to edit, htmx save, an undo toast
- `gth_notes` — a notes/comments panel for any record; and tag chips (coloured `gth_badge`) with filter-by-tag
- Global search — apps register search providers per model; results appear in the command palette beside nav items
- A published component gallery — the playground deployed as living docs, each component beside its macro call

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
Nothing open: it pins v0.15 and uses `gth_select(id=)` on the report panes. Its follow-ups (the "Leaner services"
macros above, and a few templates still hand-building markup an existing macro covers) are in PyFinBot's `todo.md`.

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
