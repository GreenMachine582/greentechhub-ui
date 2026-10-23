[← Back to README](README.md)

# ✅ TODO / Milestones

> Open work only: remove an item when it ships — its release note lands in CHANGELOG.md automatically (release-please). See [README.md](README.md) for context and [docs/](docs/) for the detailed design behind each item.

> Shipped work is recorded in [CHANGELOG.md](CHANGELOG.md) and on the [Releases page](https://github.com/GreenMachine582/greentechhub-ui/releases) — this file only tracks what's still open. Sections are themes, not versions: release-please picks the version from the commits.

## 🗺️ Milestones

Cross-repo order (with greentechhub-core and greentechhub-fastapi): consumers live (M3) → ui breaking release (M4)
→ PyFinBot ready (M6) → v1.0. M1, M2 and M5 shipped; see the CHANGELOG. The theme sections below are unscheduled
component work.

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
  - A header strip with the filename and/or language and a Copy button (`gth_copy_button`, under Settings & layout);
    the body an escaped `<pre><code>` with an optional line-number gutter (CSS counters, so copying skips them),
    highlighted lines and a `max_height` scroll box.
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

### Settings & layout
Settings sections are cards now, but setting groups are still only an `h3.h6` subheading
(`components/settings.html`), and every field is a stacked label-over-control.
- [ ] `gth_field_group` — a `<fieldset>`/`<legend>` wrapper that replaces the `h3.h6` group subheading
  - `gth_field_group(title, description=None, group_class="")` as a `{% call %}` block; a divider between groups.
  - Real grouping for screen readers, and usable on any form, not only settings.
- [ ] `gth_setting_row` — a two-column row: label and help text on the left, the control on the right; stacks on
  narrow screens
  - Used by `gth_setting_field` for switch, segmented, select and text, so labels and controls line up across
    sections.
  - `gth_settings_section(layout="rows"|"stacked")` keeps today's stacked form available.
- [ ] Settings page nav — an optional in-page section list (sticky on the side on wide screens, jump links on top on
  narrow) built from `settings_sections`, linking the existing `#gth-settings-<id>` anchors
- [ ] `api_tokens_section.html` — `gth_field_group` for the "New token" form instead of the hand-written `h3.h6`
- [ ] `gth_copy_button` — a shared copy-to-clipboard button
  - `gth_copy_button(target=None, text=None, label="Copy", icon="clipboard", copied_icon="check2", size="sm",
    button_class="")`: copies a target element's value or text (`target` selector) or a literal `text`.
  - Behaviour in a new `static/js/copy.js` (no inline script: CSP), exposed as `copy_js_url` in `shell.py`;
    `navigator.clipboard`, a "Copied" tick swap, a toast as the fallback, an `aria-live` announcement.
  - Fits `gth_form_field(suffix=...)` as an input-group add-on, for a "readonly field + Copy" pattern; a
    `copy=True` option on `gth_form_field` as sugar. Shared with `gth_code`'s header button.
- [ ] New API token: a Copy button on the readonly token field in `api_tokens_section.html`'s "created" alert (and
  drop the header comment saying there's no copy button); also for read-only `str` settings
- [ ] Playground: restructure `SETTINGS_DEMO` and `/settings` to show groups, rows, nav and the copy button; refresh
  `tests/test_settings_templates.py`, `tests/test_api_tokens_templates.py` and the e2e playground tests

### Ideas — not scheduled
- App switcher — a navbar grid menu linking the gth apps (BottleBot, PyFinBot, Market Watch, hardware-ledger), set in
  config; with Authentik SSO, moving between them needs no extra sign-in
- Templates for greentechhub-fastapi's admin view ideas — users admin (on `register_users` and core's `UserStore`:
  list and search accounts, sign-in source and last login, deactivate), a system status page (a status badge per
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
It pins v0.6. From v0.19 `app.html` has no CDN fallback, so the `install()` / `static_dirs()` migration below has to
land before it takes v0.19 or later.
- [ ] Adopt `shell_globals()` in `web/templating.py` and `toast(..., events=)` where handlers set several HX-Trigger events
- [ ] Adopt the setup helpers: `greentechhub_ui.install()` (replaces the hand-built `ChoiceLoader` + globals),
  `mount_static_dirs(app, greentechhub_ui.static_dirs())`, `Jinja2Templates(context_processors=[ui_context])` —
  **fixes the navbar never marking the active page** (BottleBot never passes `current_path`) — and
  `hx_response(toast(...))` for the six hand-built 204 + HX-Trigger responses in `routes/scrape.py` /
  `routes/watchlist.py`
- [ ] Decide on the navbar color-mode change — accept the light navbar in light mode, or pin `navbar_theme="dark"`

### PyFinBot
It pins v0.19 and already mounts `static_dirs()` and calls `install()`. It moves to this release (core v0.16,
fastapi v0.18) in its user-accounts PR (PyFinBot #114). That brings:
- htmx 2 only. Its templates use none of the 2.x changes ([docs/htmx2.md › Upgrading a
  service](docs/htmx2.md#upgrading-a-service)).
- `pluralise` for its `_plural` helpers.
- The read-only, typed profile fields for Authentik sign-ins.

What's left after that is adoption, each a PR tracked in PyFinBot's `todo.md`. `gth_timeline` is one example, for
an audit activity feed.

### GreenTechHub
- [ ] Adopt `theme/` for brand consistency
- [ ] Full component adoption beyond `theme/` — not blocking v1.0, decided based on real appetite once the theme-only step is live
