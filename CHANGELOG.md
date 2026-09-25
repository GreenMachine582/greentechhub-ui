# Changelog

All notable changes to `greentechhub-ui`. Versions follow [semver](docs/versioning.md) (pre-1.0: a breaking
change bumps the minor version). From v0.9.0 on, entries are written by
[release-please](https://github.com/googleapis/release-please) from conventional commits; the same notes are
published as [GitHub Releases](https://github.com/GreenMachine582/greentechhub-ui/releases).

## [0.10.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.9.0...v0.10.0) (2026-09-25)


### Features

* **table:** gth_data_table refresh_event re-queries after saves ([#13](https://github.com/GreenMachine582/greentechhub-ui/issues/13)) ([98e6bb7](https://github.com/GreenMachine582/greentechhub-ui/commit/98e6bb7c9800280feccd1c578a9d141f65ee6941))
* **toast:** automatic toasts for failed htmx requests ([#12](https://github.com/GreenMachine582/greentechhub-ui/issues/12)) ([60e1942](https://github.com/GreenMachine582/greentechhub-ui/commit/60e1942647e0a28ad22c1ef7b692d4edca78ef49))

## [0.9.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.8.0...v0.9.0) (2026-09-24)

### Features

* **setup:** framework-neutral wiring helpers — `install(env, …)`, `template_dirs()`, `static_dirs()` (one source
  of truth with `shell_globals`' prefixes), `render_macro()`, `htmx.is_htmx / wants_fragment / hx_target /
  trigger`, `TableState.is_own_swap()`, and an optional `templates/page.html` base. Runtime deps stay `jinja2`
  only; the Django Jinja2 backend path is tested. The FastAPI halves live in `greentechhub-fastapi` v0.8.0.

### Miscellaneous

* **playground:** adopts the shared helpers; demo data can be reset (`POST /demo/reset`); `/v07-demo/*` → `/demo/*`.

## [0.8.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.7.0...v0.8.0) (2026-09-24)

### Features

* **navigation:** nested `nav_items` (`children`, `badge`, `badge_url` + `badge_event`, `match`), active trail,
  breadcrumbs (`nav_breadcrumbs`) and `flatten`.
* **layout:** `app.html` `layout="sidebar"` with `gth_sidebar` — groups along the active trail, filter, icon rail
  with flyouts, off-canvas drawer below 992px; nested navbar dropdowns in the default layout.
* **navigation:** live nav badges (`gth_nav_badge`), refreshed by an HX-Trigger event.
* **components:** `gth_command_palette` (Ctrl/⌘+K, native `<dialog>`, optional server search).
* **components:** `gth_tree` — APG tree view with lazy children, single / tri-state selection, detail pane.
* **toast:** richer toasts — title, icon, action link, duration/sticky, `surface`/`solid` variants, countdown bar.
* **layout:** `gth_back_to_top`.

### Bug Fixes

* **toast:** messages render as text — the old `innerHTML` let a toast built from user input inject markup;
  `info`/`neutral` kinds; a readable close button on every kind (incl. dark mode on light fills).
* **components:** self-loading elements (lazy tree groups, live badges, infinite rows, lazy tabs) pin their own
  `hx-target` — inside a `gth_form` their responses landed in the form.
* **components:** record picker keeps search + pager in view (only the table scrolls) and makes page room near
  the end of a page.

### ⚠ Visual changes

* Toasts default to the new "surface" look (`variant="solid"` for the old style); the navbar logo doubles to 48px
  (override `--gth-logo-height`).

## [0.7.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.6.0...v0.7.0) (2026-09-24)

### Features

* **toast:** `toast(..., events=[...])` merges extra HX-Trigger events into one header.
* **shell:** `shell_globals()` — every `app.html` global in one call.
* **components:** modal host (`#gth-modal-host`), `gth_table_load_more`, `gth_busy_button`, `gth_combobox`,
  `gth_segmented`, `gth_badge`, `gth_tabs`, `gth_chips`, `gth_switch`, `gth_multiselect` (+ tags mode),
  `gth_record_picker` (expands to a modal-sized popover).
* **table:** config-driven navigation — `TableState` + `gth_data_table` (pages / load more / infinite / none),
  sortable headers, filter bar, skeletons.

### Bug Fixes

* **theme:** the navbar follows the colour mode; higher-contrast dark-mode secondary buttons; brand-coloured switch.
* **components:** escaping of `next_url`, busy-button and form attributes; combobox ids; modal-host backdrop leak;
  multiselect blur/limit/remove behaviour; infinite-scroll box overflow; record-picker click race.

### ⚠ Visual changes

* `gth_navbar` is light in light mode (was always dark) — `navbar_theme="dark"` keeps the old look.

## [0.6.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.5.0...v0.6.0) (2026-09-13)

### Features

* **components:** `gth_page_header` (breadcrumbs folded in), `gth_modal`, `gth_confirm_delete`.
* **theme:** original logo artwork, opt-in `brand_context(show_logo=True)`, light-tuned favicon variant.

### Tests

* Django Jinja2-backend contract test; ASGI-level playground route tests.

## [0.5.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.4.0...v0.5.0) (2026-09-11)

### Features

* Vendored Bootstrap and htmx for a local-first `app.html` (`bootstrap_css_url` / `bootstrap_js_url` /
  `htmx_js_url` globals; CDN defaults kept for one release).

## [0.4.0](https://github.com/GreenMachine582/greentechhub-ui/releases/tag/v0.4.0) (2026-09-11)

### Features

* Theme tokens, `gth_navbar` and the base `app.html` shell (v0.1).
* `gth_card`, `gth_stat_card`, `gth_table`, `gth_pagination`, `gth_empty_state`; Bootstrap Icons vendored (v0.2).
* `gth_form`, toasts (`toast()` + `gth_toast_flashes`), ARIA pass (v0.3).
* Dark mode with a persisted toggle, the `/playground` app with Playwright smoke tests, `extra_css` / `extra_js` /
  `extra_head` slots, `navigation.build_nav_items` (v0.4).
