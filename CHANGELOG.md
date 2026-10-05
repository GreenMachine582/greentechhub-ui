# Changelog

All notable changes to `greentechhub-ui`. Versions follow [semver](docs/versioning.md) (pre-1.0: a breaking
change bumps the minor version). From v0.9.0 on, entries are written by
[release-please](https://github.com/googleapis/release-please) from conventional commits; the same notes are
published as [GitHub Releases](https://github.com/GreenMachine582/greentechhub-ui/releases).

## [0.15.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.14.0...v0.15.0) (2026-10-05)


### Features

* **forms:** a CSRF hidden field on the auth forms ([#78](https://github.com/GreenMachine582/greentechhub-ui/issues/78)) ([9b6a191](https://github.com/GreenMachine582/greentechhub-ui/commit/9b6a191f32e2cd3852bcca334a46d7f4701570b6))
* **forms:** id prefix for gth_select and gth_form_field ([#71](https://github.com/GreenMachine582/greentechhub-ui/issues/71)) ([d0ebdb4](https://github.com/GreenMachine582/greentechhub-ui/commit/d0ebdb4814f81f73bf14b21209687749072d38d3))
* **navbar:** display name and initials in the user menu ([#77](https://github.com/GreenMachine582/greentechhub-ui/issues/77)) ([6957c27](https://github.com/GreenMachine582/greentechhub-ui/commit/6957c27bc55f91c26437ea599e64756113cd5b11))
* **notifications:** a notification centre ([#75](https://github.com/GreenMachine582/greentechhub-ui/issues/75)) ([3d1bdf1](https://github.com/GreenMachine582/greentechhub-ui/commit/3d1bdf19837d0795f43460f67d95b38121342434))
* **templates:** a sign-up page and a "Create account" link ([#73](https://github.com/GreenMachine582/greentechhub-ui/issues/73)) ([57ce241](https://github.com/GreenMachine582/greentechhub-ui/commit/57ce24130c06965668f4d60ec0ccf3a14ab12c53))
* **templates:** password reset and email verification pages ([#76](https://github.com/GreenMachine582/greentechhub-ui/issues/76)) ([ede8406](https://github.com/GreenMachine582/greentechhub-ui/commit/ede8406d3dc889698c201dbe70ce5fbfb2c2a8be))


### Bug Fixes

* **action-menu:** danger actions shown as icon buttons are red ([#70](https://github.com/GreenMachine582/greentechhub-ui/issues/70)) ([82f9a07](https://github.com/GreenMachine582/greentechhub-ui/commit/82f9a07dac8575c5c72a6a842d62dec2a7177e82))


### Build

* **deps:** core v0.11.0 and fastapi v0.12.0 ([#74](https://github.com/GreenMachine582/greentechhub-ui/issues/74)) ([bdb81b0](https://github.com/GreenMachine582/greentechhub-ui/commit/bdb81b02ab2d0e0eab7dd2524bd7c602d238731e))
* **deps:** core v0.9.0 and fastapi v0.11.0; playground site banner from core ([#68](https://github.com/GreenMachine582/greentechhub-ui/issues/68)) ([e9b1d85](https://github.com/GreenMachine582/greentechhub-ui/commit/e9b1d8596212dbd414f6ecf88b7aaf563c72b0db))

## [0.14.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.13.0...v0.14.0) (2026-10-03)


### Features

* **busy-button:** submit buttons ([#62](https://github.com/GreenMachine582/greentechhub-ui/issues/62)) ([8a8e662](https://github.com/GreenMachine582/greentechhub-ui/commit/8a8e662d5cef96e989f7d54426a57c0dd0c9c513))
* **select:** hide_label for filter bars ([#64](https://github.com/GreenMachine582/greentechhub-ui/issues/64)) ([0270cf8](https://github.com/GreenMachine582/greentechhub-ui/commit/0270cf8eba3721995173cff0d5f55f13d165137c))
* **table:** a row actions column ([#61](https://github.com/GreenMachine582/greentechhub-ui/issues/61)) ([02f00cf](https://github.com/GreenMachine582/greentechhub-ui/commit/02f00cf9c3b74c38e4b3b13608af80c52eb1573c))
* **templates:** a branded sign-in page on a new auth layout ([#65](https://github.com/GreenMachine582/greentechhub-ui/issues/65)) ([ac3db7c](https://github.com/GreenMachine582/greentechhub-ui/commit/ac3db7c00e9751a6ebc84804bb2f3e6359f90346))
* **toast:** an inline gth_alert ([#63](https://github.com/GreenMachine582/greentechhub-ui/issues/63)) ([4de235e](https://github.com/GreenMachine582/greentechhub-ui/commit/4de235e4cfde6bd3f2c864cbb5a27c6499714e7e))

## [0.13.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.12.0...v0.13.0) (2026-10-02)


### Features

* **display:** gth_description_list for record details ([#54](https://github.com/GreenMachine582/greentechhub-ui/issues/54)) ([ad68831](https://github.com/GreenMachine582/greentechhub-ui/commit/ad6883110cc6758f10c62dd455b751d1cc3ca1c1))
* **display:** gth_progress for progress bars and meters ([#55](https://github.com/GreenMachine582/greentechhub-ui/issues/55)) ([6d07bc4](https://github.com/GreenMachine582/greentechhub-ui/commit/6d07bc45ec708170b0365b620e1efac52658b884))
* **record-picker:** open full page to pick from the list screen ([#52](https://github.com/GreenMachine582/greentechhub-ui/issues/52)) ([9b32493](https://github.com/GreenMachine582/greentechhub-ui/commit/9b324934bbe25e262ddc530e599d7b91c735650c))
* **settings:** write-only secret fields ([#50](https://github.com/GreenMachine582/greentechhub-ui/issues/50)) ([65b10ac](https://github.com/GreenMachine582/greentechhub-ui/commit/65b10acb74dae6f588db3a5a9cf3203af75a3607))
* **shell:** gth_alert_banner site-wide banners ([#56](https://github.com/GreenMachine582/greentechhub-ui/issues/56)) ([b72ecc7](https://github.com/GreenMachine582/greentechhub-ui/commit/b72ecc7d48381880b007cfe0c795bff98e154b3c))
* **table:** gth_action_menu row actions menu ([#53](https://github.com/GreenMachine582/greentechhub-ui/issues/53)) ([b4aa92d](https://github.com/GreenMachine582/greentechhub-ui/commit/b4aa92d1b7feae52fd111e1d5709fb40fca03044))


### Build

* **deps:** dev pins greentechhub-core v0.8.0 and greentechhub-fastapi v0.10.0 ([#51](https://github.com/GreenMachine582/greentechhub-ui/issues/51)) ([4dcae8a](https://github.com/GreenMachine582/greentechhub-ui/commit/4dcae8a9df57412e4da09c52dfd962219523fe2e))

## [0.12.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.11.0...v0.12.0) (2026-10-01)


### Features

* **components:** brand track style for gth_segmented ([#44](https://github.com/GreenMachine582/greentechhub-ui/issues/44)) ([90db22d](https://github.com/GreenMachine582/greentechhub-ui/commit/90db22ddb59ca3d9b7f5b47282f1267055ab23ba))
* **components:** gth_select and settings field rendering ([#31](https://github.com/GreenMachine582/greentechhub-ui/issues/31)) ([26d7bbd](https://github.com/GreenMachine582/greentechhub-ui/commit/26d7bbdddae34a9277873ec7eab9250995572f05))
* **formatting:** honour timezone, date format and page size ([#36](https://github.com/GreenMachine582/greentechhub-ui/issues/36)) ([5c9e2ea](https://github.com/GreenMachine582/greentechhub-ui/commit/5c9e2eaf5d6ed106be47697bacc647b29ec11213))
* **formatting:** number format preference ([#42](https://github.com/GreenMachine582/greentechhub-ui/issues/42)) ([d055091](https://github.com/GreenMachine582/greentechhub-ui/commit/d055091353c425978a542f3bdd8cdbf6084ca37f))
* **navigation:** permission-aware nav and navbar user menu ([#34](https://github.com/GreenMachine582/greentechhub-ui/issues/34)) ([4ff7d4c](https://github.com/GreenMachine582/greentechhub-ui/commit/4ff7d4c1faf2ae1fc10b2ec1fb09cd2d0b4d9b71))
* **navigation:** sidebar default from the user's settings ([#41](https://github.com/GreenMachine582/greentechhub-ui/issues/41)) ([f7f592a](https://github.com/GreenMachine582/greentechhub-ui/commit/f7f592a7c7e1aaa30eeff9b5d4733f91ba56f03f))
* **permissions:** ready-made role assignment templates ([#37](https://github.com/GreenMachine582/greentechhub-ui/issues/37)) ([d818fe6](https://github.com/GreenMachine582/greentechhub-ui/commit/d818fe68c0502fe3386b583cf0f60873ce02a933))
* **playground:** impersonate personas instead of a bare 403 ([#38](https://github.com/GreenMachine582/greentechhub-ui/issues/38)) ([d8973c3](https://github.com/GreenMachine582/greentechhub-ui/commit/d8973c344dc82c35daa9fc3342e740143e2b7ed3))
* **settings:** ready-made settings page templates ([#35](https://github.com/GreenMachine582/greentechhub-ui/issues/35)) ([a9542d8](https://github.com/GreenMachine582/greentechhub-ui/commit/a9542d8b7fa99fc75162e0291656925121cae43f))
* **theme:** density and motion preferences ([#40](https://github.com/GreenMachine582/greentechhub-ui/issues/40)) ([c6e014b](https://github.com/GreenMachine582/greentechhub-ui/commit/c6e014bf23f08a4f0ecb1b7c9b53cb1413a0e0f6))
* **theme:** one brand accent across Bootstrap and gth components ([#45](https://github.com/GreenMachine582/greentechhub-ui/issues/45)) ([d5677c8](https://github.com/GreenMachine582/greentechhub-ui/commit/d5677c844cb68c6207436c84bd6f705a4eea6103))
* **theme:** server-persisted theme preference ([#32](https://github.com/GreenMachine582/greentechhub-ui/issues/32)) ([6185995](https://github.com/GreenMachine582/greentechhub-ui/commit/6185995b0b99115fb033da579a1a57371fb68ead))


### Bug Fixes

* keep the sidebar's scroll position and give choice buttons a hover state ([#43](https://github.com/GreenMachine582/greentechhub-ui/issues/43)) ([0b8bf9c](https://github.com/GreenMachine582/greentechhub-ui/commit/0b8bf9c2db7ec3d5122be6ee8bdf52b948226a07))
* **theme:** apply a theme saved from the settings form ([#33](https://github.com/GreenMachine582/greentechhub-ui/issues/33)) ([85af794](https://github.com/GreenMachine582/greentechhub-ui/commit/85af79464768d228bf750d9d201f7755493cc817))
* **theme:** favicon fills the tab icon ([#22](https://github.com/GreenMachine582/greentechhub-ui/issues/22)) ([a25b4fe](https://github.com/GreenMachine582/greentechhub-ui/commit/a25b4fe4b655759fcccbe7656c6ca8e654d948ad))

## [0.11.0](https://github.com/GreenMachine582/greentechhub-ui/compare/v0.10.0...v0.11.0) (2026-09-30)


### Features

* **forms:** gth_date_range with preset chips ([#19](https://github.com/GreenMachine582/greentechhub-ui/issues/19)) ([1fbde73](https://github.com/GreenMachine582/greentechhub-ui/commit/1fbde7382e2183685d1e3c2589f536c0d2cb1629))
* **forms:** gth_file_drop with upload progress ([#20](https://github.com/GreenMachine582/greentechhub-ui/issues/20)) ([9e06c10](https://github.com/GreenMachine582/greentechhub-ui/commit/9e06c10be2f305ce4d70fe53e2882d851f901f70))
* **forms:** gth_form_field prefix/suffix, character counter, textarea ([#25](https://github.com/GreenMachine582/greentechhub-ui/issues/25)) ([5a36ed9](https://github.com/GreenMachine582/greentechhub-ui/commit/5a36ed98477c60d467c828e98c4dd1e46d8c9013))
* money, number and date template filters ([#26](https://github.com/GreenMachine582/greentechhub-ui/issues/26)) ([f2caedf](https://github.com/GreenMachine582/greentechhub-ui/commit/f2caedf1cbfbd59eaecf327b61baee01b6711c56))
* **table:** column visibility and density toggle ([#23](https://github.com/GreenMachine582/greentechhub-ui/issues/23)) ([985a8a8](https://github.com/GreenMachine582/greentechhub-ui/commit/985a8a8325c5e28cf07a523921044be1733ea95c))
* **table:** gth_data_table bulk selection ([#21](https://github.com/GreenMachine582/greentechhub-ui/issues/21)) ([32c7184](https://github.com/GreenMachine582/greentechhub-ui/commit/32c7184678c23796d345b27adb605455fdb64e2c))
* **table:** TableState.export_url and export button ([#24](https://github.com/GreenMachine582/greentechhub-ui/issues/24)) ([4af6957](https://github.com/GreenMachine582/greentechhub-ui/commit/4af69573eabbf6996d8ab6db238ab5f2460eb9a6))


### Bug Fixes

* **forms:** character counter handles any field name ([#27](https://github.com/GreenMachine582/greentechhub-ui/issues/27)) ([b285041](https://github.com/GreenMachine582/greentechhub-ui/commit/b28504185a54120bb2cd0d26c2ec2175646cf2ac))

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
