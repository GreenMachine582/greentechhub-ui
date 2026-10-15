[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open. Sections are themes, not versions: release-please picks the version from the commits.

## 🗺️ Milestones

Cross-repo order (with greentechhub-core and greentechhub-fastapi): consumers live (M3) → ui breaking release (M4)
→ PyFinBot ready (M6) → v1.0. M1, M2 and M5 shipped; see the CHANGELOG. The theme sections below are unscheduled
component work.

### M6 PyFinBot ready — ui's share
What PyFinBot still needs from this package beyond v0.17. One PR each; PyFinBot's `todo.md` holds the adoption PR for
each once it ships.

- [ ] 1. `feat(components): gth_timeline`
  - **Why:** PyFinBot's audit log item ends with an activity feed (sign-ins, role and settings changes, its sync runs
    and imports), and the audit page (v0.17) is a filterable table, not a feed.
  - **Scope:**
    - `gth_timeline(entries, ...)` over the shape greentechhub-fastapi's `AuditViews` passes (`at`, `actor`,
      `action`, `target`, `summary`);
    - grouped by day, with an icon and tone per action prefix (`auth.`, `roles.`, `settings.`, or a service's own,
      e.g. `sync.`), configurable;
    - relative times inside `<time datetime>`, with "System" for no actor;
    - an optional "Load older" through `gth_pagination`, and an empty state.
  - **Done when:** it renders `AuditViews` rows, and the playground shows a feed from its `/audit` store.
- [ ] 2. `docs: register_csp in the CSP contract` (after greentechhub-fastapi M6.1 ships `register_csp`)
  - Replace the hand-written FastAPI recipe in docs/contract.md › Content-Security-Policy with `register_csp`, and
    have the playground send its policy through it, so the e2e suite runs under the helper PyFinBot uses.
- [ ] 3. `feat(playground): Admin nav group` (after greentechhub-fastapi M6.2 ships `register_admin`)
  - Move the playground's Roles and Audit log links under `register_admin`'s group, showing what PyFinBot's nav
    gets; the route test keeps every link reachable as the admin persona.
- [ ] 4. `feat(formatting): pluralise filter`
  - **Why:** PyFinBot hand-rolls `_plural` for its import toast and pluralises inline in its email and dividend sync
    toasts ("1 transaction" / "3 transactions").
  - **Scope:** `{{ count|pluralise("transaction") }}` → "3 transactions", with an irregular plural
    (`pluralise("entry", "entries")`) and a bare-noun form for when the number is shown elsewhere. Also exported as a
    Python function for toasts built in route code.
  - **Done when:** PyFinBot's `_plural` and inline plurals are gone.
- [ ] 5. `docs: register_error_pages in the error pages section` (after greentechhub-fastapi M6.4 ships it)
  - Replace the hand-written FastAPI recipe in docs/components.md › Error pages with `register_error_pages`, and have
    the playground wire its pages through it.

### Navigation
- [ ] Tree-select form field — a `gth_tree` inside the record picker's panel, for picking from a hierarchy
- [ ] Drag-and-drop tree reordering (keyboard-accessible: a "move" mode with arrow keys, not drag-only)
- [ ] Command-palette actions — not just navigation (e.g. "New task", "Toggle theme"), registered like nav items
- [ ] Sidebar: pinned/favourite items

### Display & charts
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
- [ ] **Breaking:** drop the CDN-URL defaults on `bootstrap_css_url`/`bootstrap_js_url`/`htmx_js_url` (overdue);
  services must mount `greentechhub_ui.static_dirs()` for `app.html` to keep working. Also required for a strict
  CSP. Blocked on BottleBot, which still loads Bootstrap/htmx from the CDN defaults — lands after its `install()`
  migration below
- [ ] **Breaking:** switch to htmx 2 by default. The audit is done and the full e2e suite passes on 2.0.11 behind
  `shell_globals(htmx=2)`, with CI's `e2e-htmx2` job running it on every PR. What's left is the switch itself:
  [docs/htmx2.md › The switch](docs/htmx2.md#the-switch-a-breaking-release). Best after the CDN-defaults removal
  above, so `htmx_js_url` loses its 1.9.10 CDN default at the same time

### Ideas — not scheduled
- App switcher — a navbar grid menu linking the gth apps (BottleBot, PyFinBot, Market Watch, hardware-ledger), set in
  config; with Authentik SSO, moving between them needs no extra sign-in
- Templates for greentechhub-fastapi's admin view ideas — users admin, a system status page (a status badge per
  health check). Its Admin nav group (M6.2) is plain nav items and needs none
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
It pins v0.16, already mounts `static_dirs()` and calls `install()`, so ui's breaking CDN removal (M4) won't touch
it. What's left is adoption, each a PR tracked in PyFinBot's `todo.md`:
- v0.16's macros (`gth_result_panel`, `gth_filter_bar`, `gth_download_button`, `gth_form_actions` /
  `gth_modal_form`, `gth_amount`, `|tone`, `|fy`) where its templates still hand-build the markup;
- v0.17's charts: sparklines in the dashboard's stat tiles (`gth_stat_card(chart=)`), gains and dividends charts on
  the reports, and `gth_embed_card` for the Grafana panel;
- v0.17's CSRF shell, with greentechhub-fastapi's `register_csrf`, and the audit page, with `AuditViews`; then
  `gth_timeline` once M6.1 above ships;
- a strict CSP once greentechhub-fastapi ships `register_csp` (the shell is ready since v0.17);
- optionally, htmx 2 through `shell_globals(htmx=2)` ahead of ui's breaking switch.

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
