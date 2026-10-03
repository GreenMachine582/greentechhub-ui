[← Back to README](../README.md)

# 🧱 Component Catalogue

All macros are prefixed `gth-` and are the only public surface consumers should touch — see [docs/architecture.md](architecture.md#public-api-vs-implementation-details) for why.

| Macro | Purpose |
|---|---|
| `gth-page-header` | Title + breadcrumb + action-button slot, top of every page |
| `gth-card` | Standard bordered content container |
| `gth-stat-card` | Dashboard KPI tile (label, value, delta, icon) |
| `gth-table` | Table shell + body with a built-in empty state; the `<tbody>` can be swapped by an HTMX partial (filter/sort controls are the consumer's own — headers render as plain text) |
| `gth-form` | Form wrapper with consistent label/validation-error layout; `gth_form_field` adds prefix/suffix add-ons, a character counter and textarea (v0.11) |
| `gth-modal` | Generic modal, focus-trapped (see [docs/accessibility.md](accessibility.md)); server-rendered whole into `#gth-modal-host` for HTMX flows (v0.7) |
| `gth-confirm-delete` / `gth-danger-modal` | Pre-built destructive-action confirmation modal |
| `gth-toast` | Toasts over `HX-Trigger` (`greentechhub_ui.toast()`) and server-side `flashes` in one markup: kinds, title, icon, action link, duration/sticky, surface or solid (v0.8 look) |
| `gth-back-to-top` | Floating "back to top" button past a scroll threshold (v0.8) |
| `gth-pagination` | Renders page controls from `greentechhub-core`'s pagination envelope |
| `gth-table-load-more` | Trailing "load more" row for tables — `gth-pagination`'s `<tr>` sibling (v0.7) |
| `gth-busy-button` | Button for long-running requests: disabled + spinner while in flight, optional "started" toast (v0.7) |
| `gth-combobox` | Server-backed searchable single-select ("autocomplete") (v0.7) |
| `gth-segmented` | Radio choices for 2–4 mutually exclusive options (v0.7): a brand-green "track" with the checked option as a raised thumb, or the joined Bootstrap button group when options carry a `style` (v0.12); help text and errors (v0.12) |
| `gth-select` | Labelled native `<select>` with the form-field help/error layout (v0.12) |
| `gth-setting-field` / `gth-settings-section` | Renders `greentechhub-core` setting definitions: each type picks its widget, grouped into a titled section with an optional form (v0.12) |
| `gth-data-table` | Table whose navigation is config: `TableState(mode="pages"\|"load_more"\|"infinite"\|"none")`, plus sortable headers — one template for the page and every partial (v0.7); bulk selection with a sticky action bar, column visibility and density, CSV export link (v0.11) |
| `gth-table-filter` | Debounced search box + filter-control slot that re-requests a `gth-data-table` from page 1 (v0.7) |
| `gth-skeleton` | Loading placeholders — lines, or table rows (v0.7) |
| `gth-badge` | Status pill with good/bad/warn/info/neutral/brand tones, contrast-safe in both modes (v0.7) |
| `gth-tabs` | Bootstrap tabs; panes static (`{% call(key) %}`) or htmx-loaded once on first show (v0.7) |
| `gth-multiselect` | Searchable multi-select with removable chips; tags mode for free text (v0.7) |
| `gth-record-picker` | Field that opens a floating, searchable, sortable, paged table to pick one record (v0.7) |
| `gth-alert-banner` | Site-wide maintenance/degraded-service strip above the navbar (`site_banners`), dismissal remembered per message (v0.13) |
| `gth-progress` | Progress bar (task) or meter (level) with an accessible value, auto warn/bad tones for meters, and self-polling live progress (v0.13) |
| `gth-description-list` | Key/value details for record pages: escaped values or trusted markup, "—" for empty, 1–4 columns that stack on phones (v0.13) |
| `gth-action-menu` | Row actions as icon buttons and/or a "⋯" dropdown, `inline` choosing how many lead as icons (v0.13) |
| `gth-chips` / `gth-switch` | Multi-select filter pills (with a hover tint, like `gth-segmented`'s options); brand-colored on/off switch (v0.7), both on the shared brand accent (v0.12, see [docs/theming.md](theming.md)); the switch takes errors and an `off_value` (v0.12) |
| `gth-date-range` | From/To date inputs plus Today / This month / This FY / Last FY preset chips (v0.11) |
| `gth-file-drop` | Drop zone over a real file input: accept/size hint, per-file errors, htmx upload progress (v0.11) |
| `gth-empty-state` | "Nothing here yet" placeholder for empty tables/lists |
| `gth-sidebar` / `gth-navbar` | Renders `nav_items` (built-in + consumer-registered, see [docs/extensibility.md](extensibility.md)), permission-filtered per request against `current_user`/`granted` (v0.12). `gth-navbar` shows a user menu when signed in (v0.12). `gth-sidebar` (v0.8): nested groups along the active trail, filter, icon rail, drawer on phones — `app.html`'s `layout="sidebar"` |
| `gth-command-palette` | Ctrl/⌘+K quick navigation over every nav item, optional server search (v0.8) |
| `gth-tree` | APG tree view: keyboard, lazy children, single or tri-state selection, detail pane (v0.8) |

## Shipped signatures (v0.1)

```jinja
{# page_header.html — breadcrumbs param folds in what would've been a separate
   gth-breadcrumbs macro (last entry is always the current/non-link page,
   aria-current="page"); action slot via {% call %} is optional — unlike
   gth-card/gth-table's mandatory body slot, most pages have no action button #}
gth_page_header(title, subtitle=None, breadcrumbs=None, header_class="")
```

## Shipped signatures (v0.2)

The table above describes intent; these are the actual macro signatures as implemented, each in its own file under `components/`:

```jinja
{# card.html — body via {% call %} #}
gth_card(title=None, footer=None, card_class="", body_class="")

{# stat_card.html #}
gth_stat_card(label, value, delta=None, delta_tone="neutral", value_tone="neutral", icon=None, card_class="")
{# label/value/delta are trusted HTML (| safe) — same trust model as gth-card's
   title/footer. delta_tone/value_tone are "good"|"bad"|"neutral" — deliberately
   not sign-inferred, since "lower is better" is a per-consumer judgment call. #}

{# table.html — two composable macros, not one, so a table can be split across
   a full-page render and an HTMX partial that only swaps the <tbody> #}
gth_table(headers, table_class="", tbody_id=None)          {# shell: <table><thead>+<tbody>, body via {% call %} #}
gth_table_body(rows, empty_message="Nothing here yet.", colspan=1)  {# tbody rows via {% call(row) %}; renders gth_empty_state automatically when rows is empty #}

{# empty_state.html — optional {% call %} action-slot (e.g. a retry button) #}
gth_empty_state(message, icon=None, empty_class="")

{# pagination.html — matches an HTMX "load more" pattern: hx-target="this",
   hx-swap="outerHTML" are fixed, not parameterized #}
gth_pagination(next_url, label="Load more", wrapper_class="text-center py-2")
```

## Shipped signatures (v0.3a)

```jinja
{# form.html — two macros, mirroring table.html's shell+piece pattern #}
gth_form(action, method="post", error=None, error_heading="Please fix the errors below", form_class="")
gth_form_field(name, label, value=None, type="text", step=None, min=None, max=None,
                errors=None, help_text=None, field_class="mb-3", input_attrs=None)
{# id/for/aria-describedby get a gth-field- prefix; name stays unprefixed so
   FastAPI's Form(...) (or equivalent) still binds by name. input_attrs is a
   plain-dict escape hatch for anything not modeled as a named param. #}

{# toast.py (Python, not a template) #}
greentechhub_ui.toast(message: str, kind: str = "success") -> str
{# Builds an HX-Trigger header value that fires the client showToast event —
   see static/js/toast.js (loaded via the toast_js_url global, same pattern
   as theme_css_url/icons_css_url) and the #gth-toast-container div app.html
   already provides. #}

{# toast.html — renders the OTHER delivery mechanism: a static `flashes` list
   (from the template context contract) as dismissible Bootstrap toasts.
   Rendering only — flash production/storage (session wiring, a Django
   messages adapter, etc.) is owned by the framework adapter
   (greentechhub_fastapi.flash / a Django messages bridge), not
   greentechhub-core, which only owns the FlashMessage value type. #}
gth_toast_flashes(flashes)
{# flashes: list of {message, kind} dicts or greentechhub_core.types.FlashMessage
   instances — the same shape toast() produces; f.kind/f.message use Jinja
   attribute lookup, so both render identically with no conversion #}
```

## Shipped signatures (v0.4)

```jinja
{# navigation.py (Python, not a template) #}
greentechhub_ui.navigation.build_nav_items(custom_items, current_user=<unset>, built_in_items=None,
                                           granted=None) -> list[NavItem]
{# The "built-in + consumer-registered" merge the gth-sidebar/gth-navbar row
   above promises. built_in_items defaults to DEFAULT_NAV_ITEMS (empty today).
   Built-ins are placed before custom_items. Without current_user (the usual
   startup call for install()'s global nav_items) nothing is filtered: since
   v0.12 app.html filters per request (the nav_visible global). Passing
   current_user (even None) filters here via filter_by_scope, as before. A
   future addition to DEFAULT_NAV_ITEMS becomes visible to every consumer
   through this helper without any of them changing their own code. #}
```

## Shipped signatures (v0.6)

```jinja
{# modal.html — built against Bootstrap's own native Modal JS (already vendored);
   focus-trap and runtime aria-modal/aria-hidden toggling come free from that JS,
   this macro only wires the static markup + aria-labelledby. Body via {% call %} #}
gth_modal(id, title, size=None, static_backdrop=False)
{# size: None|"sm"|"lg"|"xl" -> modal-{{ size }}. static_backdrop only blocks
   backdrop-click-to-close (data-bs-backdrop="static") - Esc still closes,
   that's a separate Bootstrap option (data-bs-keyboard), deliberately untouched #}

{# confirm_delete.html — gth_modal + a danger button wired with hx-delete/hx-target.
   Deliberately no hx-confirm: the modal itself is the confirmation step #}
gth_confirm_delete(id, target_url, item_label, hx_target=None)
```

## Shipped signatures (v0.7)

Extracted from PyFinBot's Stocks/Transactions pages. Each JS-backed piece is a vanilla script under `static/js/`, loaded through its own `*_js_url` global ([docs/contract.md](contract.md#static-asset-globals)); `shell_globals()` sets all of them.

```jinja
{# Modal host — app.html now renders <div id="gth-modal-host">. hx-get a
   route that returns a whole gth_modal / gth_confirm_delete into it
   (hx-target="#gth-modal-host"); modal-host.js (modal_host_js_url) shows it.
   A response closes it by firing the closeModal event:
   greentechhub_ui.toast("Saved", events=["closeModal"]) #}

{# table.html #}
gth_table_load_more(next_url, label="Load more", colspan=99, total=None)
{# Last thing in a gth_table_body partial. Replaces its own <tr>
   (hx-target="closest tr") with the next page's rows. Renders nothing when
   next_url is None. Pair with greentechhub_fastapi.query.next_page_url. #}

{# busy_button.html #}
gth_busy_button(label, busy_label, hx_attrs, icon=None, btn_class="btn-outline-secondary", start_toast=None)
{# hx_attrs: dict of hx-* attributes. Disabled (hx-disabled-elt="this") with
   busy_label + spinner while the request runs; start_toast pops at once
   (toast.js, data-gth-start-toast). Busy styling keys on :disabled, not
   .htmx-request — see theme.css for the htmx 1.9.10 bug that forces it.
   Still guard the action server-side: this only stops double-clicks in one tab. #}

{# combobox.html — behaviour in static/js/combobox.js (combobox_js_url) #}
gth_combobox(name, label, url, value=None, value_label=None, errors=None,
             placeholder="Search…", help_text=None, field_class="mb-3")
gth_combobox_option(value, label)        {# optional {% call %} body for richer row markup #}
gth_combobox_empty(message="No matches")
{# Focusing/typing GETs `url?q=<text>`; the endpoint returns
   gth_combobox_option rows (they carry data-value/data-label). Picking fills
   hidden input `name`; typing clears it, so only a picked value is ever
   submitted. The visible input is `<name>_search` — echo it back as
   value_label on a 422. Keyboard: ↑/↓ move, Enter picks (never submits the
   form), Esc closes the panel (not an enclosing modal), Tab closes. #}

{# segmented.html #}
gth_segmented(name, options, value=None, label=None, field_class="mb-3", help_text=None, errors=None,
              variant=None)
{# options: [{"value", "label", "style"?, "icon"?}]. Checked = value, or the
   first option. Submits name=<value> like any radio group (arrow keys move
   the selection).
   variant (v0.12): "track" — a muted rounded track sized to its content, the
   checked option a raised thumb in the brand colour, with hover and a brand
   focus ring — or "buttons", the joined full-width Bootstrap group where each
   option's style (a btn-outline-* class, default btn-outline-primary) applies.
   None picks "buttons" when any option sets a style, so per-option colours
   (e.g. Buy/Sell) keep their meaning, and "track" otherwise. #}
```

```python
# toast.py
greentechhub_ui.toast(message, kind="success", *, events=())
# events: extra HX-Trigger events merged into the same header, e.g.
# ["closeModal", "stocksChanged"] — a response can only carry one HX-Trigger.
# A mapping sends each event with a detail value instead of true, e.g.
# {"gth:theme": "light"} to apply a theme a settings form just saved.

# shell.py
greentechhub_ui.shell_globals(*, service_name, nav_items, assets_prefix="/gth-assets",
                              theme_prefix="/gth-static", theme_toggle=True, show_logo=False,
                              navbar_theme=None) -> dict
# Every app.html global in one call (brand, nav_items, all asset URLs pointing at
# the vendored copies). The consumer still mounts static_path/theme_path at those prefixes.
```

### Data tables (v0.7)

A table's navigation is a **config choice**, not a different template. Build a `TableState` from the request's query, fetch with its `offset`/`limit`/`sort`/`direction`/`filters`, hand it the result, and render one `gth_data_table` call — for the full page *and* for every htmx partial:

```python
# table.py
state = greentechhub_ui.TableState.from_query(
    request.query_params,            # any Mapping: FastAPI query_params, Django request.GET
    id="stocks", base_url="/stocks",
    mode="pages",                    # "pages" | "load_more" | "infinite" | "none"
    page_size=25, page_sizes=(25, 50, 100),   # page_sizes: allow-list for ?size= (+ a select)
    sortable=("name", "price"), default_sort="name", default_direction="asc",
    filter_params=("q", "exchange"), # query params that are filters (kept in every URL)
    push_url=False,                  # hx-push-url on sort/filter/page changes
    window=2,                        # pages either side of the current one in the pager
    max_height=None,                 # e.g. "24rem": scroll box + sticky header;
                                     #   infinite mode then observes that box
    user_settings=None,              # v0.12: the viewer's settings; their ui.page_size
)                                    #   becomes the default size (added to page_sizes)
rows, total = repo.list(offset=state.offset, limit=state.limit, sort=state.sort,
                        direction=state.direction, **state.filters)
state = state.with_result(total=total)   # or has_next=... when the count is unknown
template = "_stocks_table.html" if is_htmx_swap(request) else "stocks.html"
```

`user_settings` (v0.12) is the viewer's effective settings, e.g. greentechhub-fastapi's `get_effective_settings`.
Their greentechhub-core `ui.page_size` becomes this table's default size; if `page_sizes` restricts sizes and theirs
isn't one, it's added. A `?size=` in the URL still wins, and the URL omits `size` at the viewer's own default.

Query parameters are fixed: `page`, `size`, `sort`, `dir`, `partial=rows`, plus each `filter_params` name. Anything not allow-listed (an unsortable column, an off-list size, a negative page) is ignored, not trusted. Return the table fragment for htmx swaps — `HX-Request: true` *without* `HX-History-Restore-Request: true` (a history restore needs the whole page) — and the full page otherwise.

```jinja
{# table.html #}
gth_data_table(state, headers, rows, empty_message="Nothing here yet.", table_class="",
               load_more_label="Load more", refresh_event=None)   {# rows via {% call(row) %} #}
{# headers: "Name" or {"label": "Name", "sort_key": "name", "class": "text-end"} —
   a sort_key in state.sortable renders a sort button with aria-sort + caret.
   Renders <div id="{{ state.id }}"> wrapping the table; sort buttons, pager,
   page-size select and gth_table_filter all hx-get into it (outerHTML).
   state.rows_only (a load-more/infinite append, ?partial=rows) renders only
   the rows + the next trailing row. Per mode:
     pages     — "11–20 of 120" summary, optional page-size select, gth_table_pager
     load_more — trailing gth_table_load_more row
     infinite  — trailing row that loads itself on intersect (skeleton + a
                 focus-visible "Load more" fallback button for keyboard users)
     none      — nothing; pass every row
   refresh_event (v0.10): e.g. "stocksChanged" — the table re-requests itself
   (page 1, current sort + filters, no history entry) whenever that event
   fires on <body>, typically from a save's
   HX-Trigger: toast("Saved", events=["stocksChanged"]). #}

gth_table_pager(state, label="Table pages")
{# Bootstrap .pagination in <nav aria-label>: prev, first/last + a window with
   ellipses, next. Real hrefs, so it works without htmx. Prev/next only when
   the total is unknown (with_result(has_next=...)). #}

gth_table_filter(state, placeholder="Search…", search_param="q", label="Search", filter_class="mb-3")
{# A <form role="search"> OUTSIDE the table (so the input keeps focus across
   swaps): typing (300ms debounce) or changing any control in the optional
   {% call %} slot — e.g. gth_segmented, gth_chips — re-requests the table from
   page 1. Slot controls' names must be listed in filter_params. #}

gth_table_load_more(next_url, label="Load more", colspan=99, total=None, infinite=False, root=None)
{# Low-level trailing row (gth_data_table uses it). infinite=True: fetches on
   intersect, observed within the `root` selector's scroll box if given. #}

{# skeleton.html #}
gth_skeleton(lines=3, skeleton_class="")     {# placeholder-glow lines, aria-hidden #}
gth_skeleton_rows(rows=3, colspan=1)         {# placeholder <tr>s #}
```

### Badges, tabs, chips, switch (v0.7)

```jinja
{# badge.html #}
gth_badge(label, tone="neutral", icon=None, pill=True, badge_class="")
{# tone: "good"|"bad"|"warn"|"info"|"neutral"|"brand" (unknown → neutral). Bootstrap's
   *-subtle/*-emphasis pairs, plus a brand pair from theme.css. The label carries
   the meaning — color is reinforcement, not the signal. #}

{# tabs.html #}
gth_tabs(id, tabs, active=None, tabs_class="mb-3")      {# optional {% call(key) %} body #}
{# tabs: [{"key", "label", "icon"?, "url"?}]; active defaults to the first key.
   Bootstrap's data-bs-toggle="tab" does the ARIA + arrow keys (no gth JS).
   With a url the pane is hx-get'd — on page load if active, else on its first
   shown.bs.tab (once) — showing gth_skeleton until then. Without one the pane
   renders caller(key). #}

{# chips.html #}
gth_chips(name, options, values=(), label=None, field_class="mb-3", id=None)
# id (v0.12): element-id prefix, default "gth-field-<name>" — set it when several chip groups
# share a field name (e.g. one per table row) so ids stay unique.
{# options: [{"value", "label", "icon"?}]; btn-check checkboxes as pills, a check
   icon on checked ones. Submits name=<value> per checked chip (FastAPI
   list[str]; Django getlist). #}
gth_switch(name, label, checked=False, value="on", help_text=None, field_class="mb-3",
           input_attrs=None)
{# form-switch with role="switch" in the brand color. Unchecked submits nothing.
   input_attrs: extra attributes, e.g. {"hx-post": "/prefs"} to save on change. #}
```

### Multi-select and tags (v0.7)

```jinja
{# multiselect.html — behaviour is combobox.js's multi mode (combobox_js_url) #}
gth_multiselect(name, label, url=None, values=(), allow_create=False, max_items=None,
                max_message=None, errors=None, placeholder="Search…", help_text=None,
                field_class="mb-3")
gth_multiselect_chip(name, value, label)    {# one picked value; combobox.js builds the same markup #}
{# url: a gth_combobox endpoint (gth_combobox_option rows); picked options are
   hidden from its results and the panel stays open for the next pick. Each
   chip carries a hidden `name` input, so the form submits name=<value> per
   pick (FastAPI list[str] = Form([]); Django getlist). values: current picks,
   [{"value", "label"}] — echo them back on a 422. allow_create=True, or no url,
   is a tags input: Enter or comma adds the typed text (an exact label match
   takes the existing option instead); nothing is highlighted until ↑/↓, so
   Enter never silently takes the first suggestion. Backspace on the empty
   input removes the last chip; max_items caps the count, and trying to go over
   it pops a warning toast (max_message, default "You can choose up to N." —
   needs toast_js_url). Typed text that was never picked or made a tag is
   cleared when focus leaves the field. Removing a chip moves focus to the next
   chip without reopening the list; clicking into the input opens it (also
   after Esc). Adds/removals are announced in a polite live region. Chips are
   built with textContent, so a typed tag can't inject HTML. #}
```

### Record picker (v0.7)

```jinja
{# record_picker.html — behaviour in static/js/record-picker.js (record_picker_js_url) #}
gth_record_picker(name, label, url, value=None, value_label=None, errors=None,
                  placeholder="Select…", help_text=None, field_class="mb-3",
                  panel_width="40rem", clearable=True, size="panel", expandable=True,
                  full_page_url=None)                 {# v0.13: see "Record picker: full page" #}
gth_record_picker_row(value, label, row_class="")    {# a pickable <tr>, cells via {% call %} #}
{# For records too rich for a combobox row. Clicking the field (or ↓ on it) opens
   a floating panel and loads `url` into it once. That endpoint returns
   gth_table_filter + gth_data_table (any TableState mode; give the state an id
   unique on the page) with rows wrapped in gth_record_picker_row — the table's
   own sort/filter/pager swaps then work inside the panel unchanged. Those swaps
   target the table, so return only the table when HX-Target is the table's id
   (the first load targets the panel body, which has none):

       with_filter = request.headers.get("HX-Target") != state.id

   Picking fills hidden `name` and `<name>_label` (echo the latter back as
   value_label on a 422), updates the field, fires `change`, closes the panel
   and returns focus to the field. While open the panel lives in <body> — or the
   enclosing .modal, inside Bootstrap's focus trap — positioned under the field
   (above it if there's no room; full-width under 576px). That keeps the panel's
   filter <form> out of your form and stops a modal body clipping it. Keyboard:
   focus starts in the search box; ↓ enters the rows; ↑/↓/Home/End move;
   Enter/Space pick; Esc closes the panel only (not an enclosing modal).
   Not a Bootstrap Popover: its sanitizer strips tables and inputs.
   Two sizes: "panel" (floating under the field) and "modal" (a centred,
   modal-sized popover over a backdrop — fullscreen under 576px — dismissed by
   the backdrop, its ✕ or Esc). The header's Expand/Shrink toggle
   (expandable=True) switches between them without reloading the content;
   `size` is the one each open starts at — size="modal" for big tables. It's
   the same panel restyled, not a second Bootstrap modal, so it works inside
   one. At modal size Tab wraps inside it. An open picker takes Esc first,
   wherever focus is. #}
```

### Record picker: full page (v0.13)

The third size: for a pick that needs the whole list screen (its filters, columns, bulk tools), the panel header can
link to it. The list screen opens **in a new tab**, so nothing typed into the form is lost, and its "Use this record"
buttons send the pick back.

```jinja
{# record_picker.html #}
gth_record_picker(..., full_page_url=None)       {# "Open full page" (↗) in the panel header #}
gth_record_pick_banner(pick_for, label="a form")  {# on the list screen: what's going on, plus a status line #}
gth_record_pick_button(pick_for, value, label, button_class="btn btn-sm btn-primary")  {# "Use this record" #}
```

- `full_page_url` is the list screen's URL. When the panel is about to open, the JS adds `?pick_for=<token>`
  (a random token per picker, other query params kept), so a middle-click carries it too. Opening it closes the panel.
- The list screen reads `pick_for` from the query and passes it to the banner and to one button per row. Both render
  nothing without it, so the same templates serve the normal list. Keep `pick_for` in the `TableState`'s `base_url`
  so the table's own sort, filter and pager swaps keep the buttons:

```python
pick_for = request.query_params.get("pick_for", "")
state = TableState.from_query(request.query_params, id="parts",
                              base_url="/parts?" + urlencode({"pick_for": pick_for} if pick_for else {}), ...)
```

- "Use this record" posts `{value, label}` on a same-origin `BroadcastChannel`. The picker holding the token fills its
  field (the same as picking a row: hidden `name` and `<name>_label`, and a `change` event) and acknowledges, and the
  list tab closes itself. If the browser won't close it, the banner says it was sent. With no reply within a second
  (the form tab was closed), it says the form couldn't be found and the button stays usable.
- Without `BroadcastChannel` the link is hidden. Nothing leaves the origin, and there's no `return=` URL to redirect
  through.

### Action menu (v0.13)

Row actions (edit, archive, delete…) as icon buttons, a "⋯" dropdown, or both. `inline` is the knob, so a table
can keep its icon buttons or fold them away without changing the item list.

```jinja
{# action_menu.html — Bootstrap's dropdown, no JS of its own #}
gth_action_menu(items, label=None, inline=0, menu_class="", button_class="btn btn-sm btn-link text-body", align="end")
```

| Item key | Meaning |
|---|---|
| `label`, `url` | Required (except for a divider). A `javascript:` / `data:` / `vbscript:` url drops the item |
| `method` | None: a link (`<a href=url>`). `get`/`post`/`put`/`patch`/`delete`: a button with `hx-<method>=url` and `hx-swap="none"`, unless `attrs` sets `hx-target`/`hx-swap` |
| `icon` | Bootstrap icon name; inline buttons show only the icon (named "`label` `row label`") |
| `confirm` | `hx-confirm` text (htmx items only) |
| `danger`, `disabled` | Red text; a disabled button, or a link with no href and `aria-disabled` |
| `attrs` | Extra attributes, e.g. `{"hx-target": "#gth-modal-host"}` to load an edit modal |
| `divider` | `{"divider": True}`: a separator inside the menu (dropped when it would lead or trail) |

- `inline`: how many leading actions show as icon buttons before the "⋯" (dividers don't count). `0` (default) puts
  everything in the menu, `None` shows them all as buttons and no menu.
- `label` is the row's name: the toggle is "Actions for `label`" and an icon button "Edit `label`".
- htmx items follow the bulk-action contract: answer with `HX-Trigger` (a toast, plus the table's `refresh_event`)
  rather than HTML. `greentechhub_fastapi.htmx.hx_response(toast(..., events=["recordsChanged"]))` does both.
- The menu uses Popper's fixed strategy, so a `.table-responsive` or scroll-box table never clips it; keyboard
  (Enter/↓/Esc) and click-away come from Bootstrap.

In a `gth_data_table`, use its row actions column instead of a hand-built `<td>` (see
[Row actions](#row-actions)). The macro also works on its own, e.g. in a card header or a plain `gth_table`:

```jinja
<td class="text-end text-nowrap">
  {{ gth_action_menu([
      {"label": "Edit", "icon": "pencil", "method": "get", "url": "/stocks/" ~ s.id ~ "/edit",
       "attrs": {"hx-target": "#gth-modal-host"}},
      {"label": "Archive", "icon": "archive", "method": "post", "url": "/stocks/" ~ s.id ~ "/archive"},
      {"divider": True},
      {"label": "Delete", "icon": "trash", "method": "delete", "url": "/stocks/" ~ s.id,
       "confirm": "Delete " ~ s.code ~ "?", "danger": True},
    ], label=s.code, inline=1) }}
</td>
```

### Description list (v0.13)

Key/value details for a record page, e.g. inside a `gth_card`.

```jinja
{# description_list.html #}
gth_description_list(items, columns=1, label_width="10rem", empty="—", dl_class="")
```

- `items`: a mapping (label → value), `(label, value)` pairs, or mappings `{"label", "value", "help"?, "mono"?}`,
  rendered in order. `help` adds a small line under the value; `mono` sets `font-monospace` (ids, SKUs).
- Values are text and are escaped. Another macro's output, or a `{% set x %}…{% endset %}` capture, is `Markup` and
  passes through (the caller vouches for it, as with `gth_card`'s title), so a status can be a `gth_badge`.
- `None` and `""` show `empty` in secondary text; `0` and `False` are values.
- A `<dl>` on a CSS grid: `columns` label/value pairs per row from 768px (1–4), one pair per row below that, and the
  label stacked above its value under 576px. `label_width` caps the label column.

```jinja
{% set status %}{{ gth_badge(part.status, "info") }}{% endset %}
{% call gth_card(title=part.name) %}
  {{ gth_description_list([
      {"label": "SKU", "value": part.sku, "mono": True},
      {"label": "Status", "value": status},
      {"label": "Price", "value": part.price|money, "help": "Excludes GST."},
      {"label": "Supplier", "value": part.supplier},
    ], columns=2) }}
{% endcall %}
```

### Progress (v0.13)

A progress bar for a task, or a meter for a level, on Bootstrap's `.progress` with the brand accent.

```jinja
{# progress.html #}
gth_progress(value, max=100, label=None, kind="progress", tone=None, show_value=True, value_text=None,
             size=None, striped=False, warn_at=None, bad_at=None, poll_url=None, poll_every="2s",
             id=None, progress_class="")
```

- `kind="progress"` (a sync, an upload) is `role="progressbar"`; `kind="meter"` (a quota, storage) is
  `role="meter"`. Both carry `aria-valuenow`/`min`/`max`, `aria-valuetext` and `aria-label` (`label`, else
  "Progress"). `value` is clamped to 0–`max`.
- The header shows `label` and the value text (`value_text`, else "42%"); `show_value=False` hides it and keeps the
  aria. `value=None` on a progress bar is indeterminate: a full animated striped bar, no `aria-valuenow`, "Working…".
- `tone`: `good|bad|warn|info|neutral|brand` (default brand). A meter given `warn_at`/`bad_at` (fractions of `max`)
  and no `tone` turns warn/bad by itself. The value text always says the number, so colour is never the only cue.
- `size="sm"` is a slim bar; `striped` adds stripes (animated while polling). Under `ui.motion="reduce"` (or the OS's
  reduced motion) the stripes stand still.

**Live progress.** Give the bar an `id` and a `poll_url`: it re-fetches itself every `poll_every` (`hx-get`,
`outerHTML`). The endpoint returns a fresh bar, still with `poll_url` while running and without it once done
(or answers 286), so polling stops:

```python
@app.get("/sync/progress")
async def sync_progress(request: Request):
    done, total = await sync_status()
    return templates.TemplateResponse(request, "_sync_progress.html", {
        "done": done, "total": total,                     # gth_progress(done, max=total, id="sync",
        "poll_url": "/sync/progress" if done < total else None,  #   poll_url=poll_url, value_text=...)
    }, headers={} if done < total else {"HX-Trigger": toast("Sync complete")})
```

### Alert banner (v0.13)

Site-wide strips for maintenance or degraded service, above the navbar on every page.

```jinja
{# alert_banner.html — dismissal in static/js/alert-banner.js (alert_banner_js_url) #}
gth_alert_banner(message, tone="info", id=None, dismissible=True, icon=None, action=None, html=False)
```

- `tone`: `info|warn|bad|good|neutral`, each with a default icon (or `icon=`). `bad`/`warn` announce as
  `role="alert"`, the rest as `role="status"`.
- `message` is text and escaped; `html=True` is for trusted, server-built markup only (as with `toast`).
  `action={"label", "url"}` adds a link; only http(s) and relative URLs are kept.
- **The slot.** `app.html` renders the optional `site_banners` context key (a list of these kwargs) inside its
  `{% block banner %}`, so a page can still override the block. Nothing renders without it.
- **Dismissing** needs `alert_banner_js_url` (`shell_globals()` sets it); without it there's no close button.
  A banner with an `id` remembers the dismissal in `localStorage` against a hash of its message: it stays hidden on
  every page, from before first paint (a small script in `app.html`'s head), and shows again once the message
  changes. Without an `id` it only closes for that page view.

Feeding it from greentechhub-core's settings, e.g. an APP setting `site.banner` an admin edits on `/settings`:

```python
from greentechhub_fastapi.settings import settings_context

def banners_context(request):                    # another Jinja2Templates context processor
    text = settings_context(request).get("user_settings", {}).get("site.banner")
    return {"site_banners": [{"message": text, "tone": "warn", "id": "site"}]} if text else {}
```

Editing the text brings the banner back for everyone who dismissed the old one.

## Shipped signatures (v0.8)

### Navigation model

```python
# navigation.py — NavItem gains optional keys; flat v0.4 lists are unchanged
{"label": "Data", "icon": "table", "url": "/data",        # url optional on a group
 "children": [...],                                          # a group
 "badge": {"label": "3", "tone": "warn"},                    # static count (gth_badge tones)
 "badge_url": "/nav-badges/health", "badge_event": "healthChanged",  # live count
 "match": "exact"}                                           # default "prefix"

greentechhub_ui.navigation.nav_trail(items, current_path) -> list        # ancestors → best match
greentechhub_ui.navigation.mark_active(items, current_path) -> list      # copies with active/expanded
greentechhub_ui.navigation.breadcrumbs_for(items, current_path) -> list  # gth_page_header format
greentechhub_ui.navigation.flatten(items) -> list                        # {label, path, url, icon}
# Matching: an exact path beats the longest prefix; "/" and match="exact" only match exactly; an
# in-page anchor child (/forms#x) never beats its page. filter_by_scope recurses and drops emptied groups.

greentechhub_ui.shell_globals(..., layout="navbar")
# layout="sidebar" moves nav_items into gth_sidebar. Also installs the globals
# nav_breadcrumbs(path), nav_mark_active, nav_flatten, and sidebar/tree/command-palette JS URLs.
```

### Sidebar layout

```jinja
{# sidebar.html — app.html renders it for layout="sidebar"; usable standalone #}
gth_sidebar(nav_items, current_path=None, show_filter=True, label="Main", id="gth-sidebar-nav")
gth_sidebar_rail_toggle()
{# A <nav> of lists with disclosure buttons — the APG navigation pattern, NOT
   role="tree". Groups open along the active trail (nav_mark_active); a group's
   own url becomes an "Overview" first child. The filter hides non-matches and
   opens the groups holding matches; clearing restores. From 992px the rail
   toggle collapses it to icons (tooltips; badges as dots; groups open as
   flyouts, closed by Esc / a click elsewhere), remembered in localStorage and
   applied before first paint. Until this browser toggles it, the starting
   state is the viewer's ui.sidebar_default from user_settings (v0.12;
   "rail" or "expanded"). Below 992px it's Bootstrap's offcanvas-lg drawer
   (a link click closes it). sidebar.js also remembers which groups were
   opened by hand, and keeps the list's scroll position across page loads
   (per tab), always bringing the current page's link into view — without
   moving focus, which stays with the page. {% block sidebar_extra %} fills the footer. #}

{# navbar.html #}
gth_navbar(..., sidebar=False, show_search=False)
{# sidebar=True: drawer button, brand, search, theme toggle — no items. In the
   default mode an item with children renders as a dropdown. #}

{# badge.html #}
gth_nav_badge(item, badge_class="")
{# A NavItem's badge (static) or badge_url (hx-get on load and on badge_event
   from <body>; the endpoint returns a gth_badge, or nothing to hide it). #}
```

### Command palette

```jinja
{# command_palette.html — app.html includes it when command_palette_js_url is set
   (always in layout="sidebar"; show_command_palette in the default layout) #}
gth_command_palette(nav_items, search_url=None, placeholder="Jump to…", id="gth-command")
gth_command_item(label, url, icon=None, hint=None)   {# a search_url result row #}
{# A native <dialog> (showModal: top layer, backdrop, inert page, Esc). Nav
   entries (nav_flatten) are embedded as JSON and filtered client-side, ranked
   label-starts-with > label-contains > path-contains; search_url (?q=, 200ms
   debounce, 2+ chars) adds server results. Ctrl/⌘+K or [data-gth-command-open]
   opens it; ↑/↓, Enter goes, Esc/backdrop close and return focus. #}
```

### Tree

```jinja
{# tree.html — behaviour in static/js/tree.js (tree_js_url) #}
gth_tree(id, nodes, label, select=None, name=None, lazy_url=None, detail_target=None, tree_class="")
gth_tree_nodes(nodes, level, tree_id, select=None, lazy_url=None)   {# a lazy_url response #}
{# nodes: [{"id", "label", "icon"?, "children"?, "has_children"? (lazy),
   "expanded"?, "selected"?/"checked"?, "badge"?, "url"? (detail)}]
   select="single": aria-selected, hidden `name` = the selected id.
   select="multi": tri-state aria-checked; a node checks its whole subtree,
   ancestors recompute to true/mixed/false, lazy children inherit a checked
   parent; `name` gets the TOP-MOST checked ids, each standing for its subtree
   (so unloaded children are covered).
   lazy_url: GET <lazy_url>?parent=<id>&level=<n> on a node's first expand —
   return gth_tree_nodes(children, level, tree_id, select, lazy_url).
   detail_target: activating a node with a url loads it there.
   Keyboard (APG): ↑/↓, → expand/first child, ← collapse/parent, Home/End,
   Enter activate, Space select/check, letters jump. #}
```

### Toasts (v0.8)

```python
# toast.py
greentechhub_ui.toast(message, kind="success", *, title=None, icon=None, action=None,
                      duration=5000, variant="surface", html=False, events=()) -> str
# kind: success | info | warning | danger | neutral (aliases warn, error; unknown → neutral).
# action: {"label", "url"} (http(s)/relative only — javascript: etc. are dropped).
# duration: ms; 0 = stays until closed. variant: "surface" (default — theme background,
# kind-coloured accent + icon; readable in both colour modes) or "solid" (coloured fill,
# contrast-matched close). Options at their defaults are omitted from the payload, so
# toast("Saved") is still just {"showToast": {"message", "kind"}}.
# The message is TEXT. html=True renders it as HTML — only for markup the server itself
# produced and escaped (a template render), NEVER for anything holding user input.
# events: names (each sent as true) or a {name: detail} mapping, e.g. {"gth:theme": "light"}.
```

```jinja
{# toast.html — the same markup, server-side, for a `flashes` list #}
gth_toast_flashes(flashes)
{# Each flash: {message, kind, title?, icon?, action?, variant?, html?} — dict or object
   (greentechhub_core FlashMessage renders identically). Rendered visible, no auto-hide. #}
```

Warning/danger toasts are `role="alert"` (assertive); the rest `role="status"` (polite). An auto-hiding
toast shows a countdown bar that pauses while hovered or focused, in step with Bootstrap's own timer.
Before v0.8 the message was injected as HTML (`innerHTML`) — a toast built from user input could inject
markup; it's text now.

### Back to top (v0.8)

```jinja
{# back_to_top.html — app.html renders it when back_to_top_js_url is set (shell_globals sets it) #}
gth_back_to_top(threshold=400, label="Back to top")
{# Appears past `threshold` px of scroll; scrolls to the top (instantly under
   prefers-reduced-motion) and moves focus to <main>. The toast stack lifts above it. #}
```

### Record picker panel layout (v0.8)

The panel is layered at both sizes: its header, the endpoint's `gth_table_filter` and the data table's
footer (summary, page size, pager) stay put, and only the table scrolls. That relies on the endpoint
returning `gth_table_filter` + `gth_data_table` as the panel body's direct children (anything else still
scrolls as a whole). Near the end of a page the picker scrolls the page — adding room inside `<main>` if
needed, removed on close — so the whole panel fits below its field.

## Shipped signatures (v0.9) — wiring helpers

Framework-neutral (jinja2 + stdlib only); see [docs/contract.md](contract.md#setup-fastapi-and-django) for the
FastAPI and Django halves side by side.

```python
greentechhub_ui.template_dirs() -> list[Path]                     # app.html + component dirs
greentechhub_ui.static_dirs(assets_prefix="/gth-assets", theme_prefix="/gth-static") -> dict[str, Path]
greentechhub_ui.install(env, **shell_globals_kwargs) -> env        # loaders after the app's; idempotent
greentechhub_ui.render_macro(env, template, macro, *args, **kwargs) -> str   # env globals in scope
greentechhub_ui.htmx.is_htmx(headers) / wants_fragment(headers) / hx_target(headers)
greentechhub_ui.htmx.trigger(*events, **detail_events) -> str    # HX-Trigger for bare events
TableState.is_own_swap(headers) -> bool                           # HX-Target is this table
```

```jinja
{# templates/page.html — optional page base #}
{% extends "page.html" %}   {# context: page_title, page_subtitle?, current_path #}
{% block header_actions %}<button class="btn btn-sm btn-primary">New</button>{% endblock %}
{% block page %}…{% endblock %}
```

## Shipped signatures (v0.10)

### Automatic error toasts

`toast.js` (already loaded through `toast_js_url`) toasts any htmx request that fails, so a 4xx/5xx
(which htmx doesn't swap), a dropped connection or a timeout is never silent:

| Failure | Title | Message |
|---|---|---|
| 401 / 403 / 409 | Signed out / Not allowed / Conflict (warning) | a JSON `detail`, else a default |
| 404 | Not found | a JSON `detail` (e.g. FastAPI's `HTTPException`), else "It may have been deleted." |
| other 4xx / 5xx | Request failed / Server error | a JSON `detail`, else "…(status)." |
| `htmx:sendError` | Can't reach the server — or You're offline when `navigator.onLine` is false | |
| `htmx:timeout` | Request timed out | |

- **A server toast wins.** A response whose `HX-Trigger` already carries `showToast` (e.g.
  `hx_response(toast("Reports unavailable", "danger"), status_code=503)`) shows only that one.
- **422 is left alone** — it's `gth_form`'s inline validation errors, which `app.html` swaps in.
- **Opt out** with `data-gth-error-toast="off"` on the element or any ancestor (on `<body>`: app-wide), e.g.
  for a background poll whose failure the page already shows another way.
- The `detail` is shown as text, and only when it's a short string. The same title and message within 4s
  shows once, so a failing poll or a burst of lazy loads doesn't stack toasts.
- A 401 carrying `HX-Redirect` (gth-fastapi's `require_page_identity`) never toasts: htmx navigates to the
  login page first.

## Shipped signatures (v0.11)

### Date range

```jinja
{# date_range.html — behaviour in static/js/date-range.js (date_range_js_url) #}
gth_date_range(name_from="date_from", name_to="date_to", value_from=None, value_to=None,
               label="Date range", hide_label=False, presets=("today", "month", "fy", "last_fy"),
               fy_start_month=7, errors=None, help_text=None, field_class="mb-3")
{# Two native <input type="date">s submitting YYYY-MM-DD (empty = open end).
   presets picks and orders the chips; unknown keys are skipped, () renders
   none. fy_start_month (1-12) sets the financial year: 7 = 1 Jul – 30 Jun.
   The chips render hidden and date-range.js shows them, so without JS the
   inputs still work. A chip fills both inputs from the browser's local date
   and fires one bubbling `change`; the chip matching the current inputs is
   aria-pressed. errors/help_text describe both inputs. #}
```

Inside a `gth_table_filter` slot it re-queries the table from page 1 on a chip click or a date edit; add both
names to `filter_params` and parse them yourself (`TableState` keeps filters as strings):

```jinja
{% call gth_table_filter(table) %}
  {{ gth_date_range(value_from=table.filters.get("date_from"), value_to=table.filters.get("date_to"),
      hide_label=True, field_class="mb-0") }}
{% endcall %}
```

### File drop

```jinja
{# file_drop.html — behaviour in static/js/file-drop.js (file_drop_js_url) #}
gth_file_drop(name, label, accept=None, max_size=None, multiple=False, errors=None,
              help_text=None, prompt=None, field_class="mb-3", input_attrs=None)
{# A dashed drop zone labelling a real <input type="file"> (visually hidden, still
   focusable — its focus ring is drawn on the zone). accept: ".csv,.xlsx" or a
   sequence; max_size: bytes. Both become the hint ("CSV, XLSX · up to 5 MB") and
   the client-side check on every pick or drop: a rejected file is removed from
   the input and gets its own line in the error list ("big.csv — larger than
   5 MB"). Without multiple, extra dropped files are rejected the same way.
   errors: server messages, shown in the same list until the next pick. #}
```

The enclosing form sends the upload, so give it `hx-encoding="multipart/form-data"` (or `enctype`). While
that request runs, the progress bar follows `htmx:xhr:progress`. htmx 1.9 fires that event for the response
download as well, so once the upload reaches 100% the bar switches to an indeterminate "Processing…" and
stays there until `htmx:afterRequest`.

**The server still has to check type and size**, because the client check is only a convenience. When
nothing was chosen, the browser still sends an empty file part. Starlette parses that as a `str`, so
`list[UploadFile] = File()` answers with FastAPI's JSON 422. Instead, take `UploadFile | None = File(None)`
or read `await request.form()` and keep only the parts with a filename, as the playground's `/demo/upload`
does. Then return the form re-rendered with `errors` and a 422, which `app.html` swaps in:

```jinja
{% call gth_form("/import", form_attrs={"hx-post": "/import", "hx-encoding": "multipart/form-data",
    "hx-target": "this", "hx-swap": "outerHTML"}) %}
  {{ gth_file_drop("file", "File", accept=(".csv", ".xlsx"), max_size=5 * 1024 * 1024, errors=errors) }}
  <button type="submit" class="btn btn-primary">Import</button>
{% endcall %}
```

### Bulk selection

```jinja
{# table.html — behaviour in static/js/table-select.js (table_select_js_url) #}
gth_data_table(state, headers, rows, ..., bulk_actions=None, select_name="ids")
gth_table_select_cell(value, label)    {# first <td> of each row: a checkbox for `value`, "Select <label>" #}
{# bulk_actions: [{"label", "url", "icon"?, "style"? (default "btn-outline-secondary"),
                   "confirm"? (hx-confirm), "attrs"? (extra attributes)}]
   A non-empty list adds a checkbox column (a tri-state select-all in the header,
   headers and colspans shift by one) and a bar under the table that sticks to the
   viewport bottom while anything is selected: "3 selected (1 on other pages)",
   one button per action, and "Clear selection". Each button hx-posts every
   selected value as `select_name` (repeated) with hx-swap="none". #}
```

The selection is a set of row values that table-select.js keeps per table id. It lasts through sorting, the
pager, the page size, load-more and infinite appends, and `refresh_event` re-queries. It's cleared when the
filters change, so an action never reaches rows the current filter hides. It's also cleared after an action
succeeds, by "Clear selection", and by Esc. It isn't kept across a full page reload. Shift+click selects a
range of the rows shown.

Answer the action with an `HX-Trigger`, since nothing is swapped. Usually that's a toast carrying the table's
`refresh_event`, so the table re-queries with its sort and filters:

```python
@app.post("/stocks/archive")
async def archive(request: Request):
    ids = (await request.form()).getlist("ids")
    n = await repo.archive(ids)
    return hx_response(toast(f"Archived {n} stocks.", events=["stocksChanged"]))
```

```jinja
{% call(s) gth_data_table(table, headers, stocks, refresh_event="stocksChanged",
    bulk_actions=[{"label": "Archive", "url": "/stocks/archive", "icon": "archive"},
                  {"label": "Delete", "url": "/stocks/delete", "style": "btn-outline-danger",
                   "confirm": "Delete the selected stocks?"}]) %}
<tr>{{ gth_table_select_cell(s.id, s.symbol) }}<td>{{ s.symbol }}</td>…</tr>
{% endcall %}
```

### Row actions

```jinja
{# table.html — gth_action_menu in a column of its own #}
gth_data_table(state, headers, rows, ..., row_actions=False, row_actions_label="Actions")
gth_table_actions_cell(items, label=None, inline=None, button_class="btn btn-sm btn-link text-body", align="end")
{# row_actions=True adds a trailing column for per-row actions; end each row with
   gth_table_actions_cell. Its header is visually hidden (row_actions_label, for
   screen readers) and the empty-state and load-more rows span it. #}
```

`items`, `label` and `inline` are [`gth_action_menu`](#action-menu-v013)'s. Here `inline` defaults to `None`, so every
action is an icon button; pass `0` to fold them into the "⋯" menu or `N` to keep the first `N` as buttons. Don't
add a `""` header for the column yourself: with [view options](#column-visibility-and-density) a blank header
would be listed in the View menu as an unlabelled toggle. The row-actions column is never listed and never hidden.

```jinja
{% call(s) gth_data_table(table, headers, stocks, refresh_event="stocksChanged", view_options=True, row_actions=True) %}
<tr>
  <td>{{ s.symbol }}</td>…
  {{ gth_table_actions_cell([
      {"label": "Edit", "icon": "pencil", "method": "get", "url": "/stocks/" ~ s.id ~ "/edit",
       "attrs": {"hx-target": "#gth-modal-host"}},
      {"label": "Delete", "icon": "trash", "method": "get", "url": "/stocks/" ~ s.id ~ "/delete",
       "attrs": {"hx-target": "#gth-modal-host"}, "danger": True},
    ], label=s.symbol) }}
</tr>
{% endcall %}
```

### Column visibility and density

```jinja
{# table.html — behaviour in static/js/table-view.js (table_view_js_url) #}
gth_data_table(state, headers, rows, ..., view_options=False)
{# view_options=True adds a "View" menu above the table: a checkbox per column,
   Comfortable/Compact density (Bootstrap's table-sm), and "Reset view".
   Header dicts gain:
     "key"       the column's stored name (default: sort_key, then label)
     "hideable"  False pins the column: always shown, its checkbox disabled
     "hidden"    True hides it until the user shows it #}
```

The choice is stored in `localStorage["gth-table-view:<pathname>#<table id>"]`, so it's per browser, per page and
per table. With nothing stored, density starts from the viewer's `ui.density` (`<html data-gth-density>`, v0.12), and
Comfortable on a compact page keeps comfortable cells. It's re-applied to every swap of the table (sort, pager, filters, `refresh_event`) and to every
load-more or infinite append, so hidden columns stay hidden. A column is hidden by index: its `<th>` and the same
cell of every body row. Rows with a `colspan` cell, such as the empty state or the load-more row, are left alone,
so **keep one `<td>` per header in your rows**. The bulk-selection checkbox column and the [row actions](#row-actions) column are never listed or hidden. At least one
column always stays shown. Without JS the menu stays hidden and every column shows.

### Export

```python
TableState.from_query(..., export_base_url=None)   # the consumer's CSV endpoint, e.g. "/stocks/export.csv"
TableState.export_url -> str | None                # that endpoint + the current filters and sort; never page/size
```

```jinja
gth_data_table(state, headers, rows, ..., export_label="Export CSV")
{# With state.export_url set, an `export_label` download link sits in the toolbar above
   the table (next to the View menu). It's inside the table's wrapper, so every sort,
   filter and refresh_event swap re-renders it with the current URL. It's a plain
   <a download>, so it works without JS. #}
```

gth-ui builds the URL, and the consumer writes the CSV. Build the export's state with **the same
`from_query` arguments** as the table, so it takes the same allow-listed filters and sort. Then fetch every
matching row and ignore `offset`/`limit`:

```python
def _stocks_state(query, **kw):
    return TableState.from_query(query, id="stocks", base_url="/stocks", sortable=("symbol", "price"),
                                 filter_params=("q", "market"), export_base_url="/stocks/export.csv", **kw)

@app.get("/stocks/export.csv")
async def export_stocks(request: Request):
    state = _stocks_state(request.query_params, mode="none")
    rows = await repo.list(sort=state.sort, direction=state.direction, **state.filters)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Symbol", "Name", "Price"])
    writer.writerows((r.symbol, r.name, r.price) for r in rows)
    return Response(out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="stocks.csv"'})
```

For very large tables, stream the rows with `StreamingResponse` instead of building one string.

### Form field extras

```jinja
{# form.html — the counter's behaviour in static/js/char-counter.js (char_counter_js_url) #}
gth_form_field(name, label, value=None, type="text", ..., help_text=None, errors=None, input_attrs=None,
               prefix=None, suffix=None, maxlength=None, counter=None, rows=3)
{# prefix / suffix: Bootstrap input-group add-ons — "$", "%", "AUD", "kg". They're in the
   field's aria-describedby, so they're read with it; errors stay below the group.
   maxlength: the native limit. With it, counter defaults on: an "N / max" line under the
   field (right without JS — the server renders the starting count), amber from 90% and
   red at the limit. counter=False keeps the limit without the line.
   type="textarea": a <textarea rows=rows> with the same label, ids, help, errors and
   counter; step/min/max don't apply. #}
```

```jinja
{{ gth_form_field("budget", "Budget", value=budget, type="number", step="0.01", prefix="$", suffix="AUD") }}
{{ gth_form_field("notes", "Notes", value=notes, type="textarea", maxlength=140, help_text="Optional.") }}
```

A call without the new arguments renders exactly as before. `maxlength` only stops the browser, so the server must
still check the length and answer with `errors`. The counter measures what the browser measures, UTF-16 units,
so an emoji counts as 2, the same as `maxlength` does.

### Formatting filters

`install()` registers four filters from `greentechhub_ui.formatting`. **It never replaces a filter of the same name
that the app already registered**, so an app's own `money` wins.

```jinja
{{ value|money(symbol="$", places=2) }}   {# 1234.5 → $1,234.50 · -1234.5 → -$1,234.50 · |money("") → 1,234.50 #}
{{ value|number(places=None) }}           {# Decimal("100.500") → 100.5 · 100 → 100 (never 1E+2) · 1234567.891 → 1,234,567.891 #}
{{ value|date(fmt=None) }}                {# date / datetime / ISO string → 5 Feb 2025 · |date("%Y-%m-%d") → 2025-02-05 #}
{{ value|datetime(fmt=None) }}            {# → 5 Feb 2025 13:45 (v0.12); a plain date has no time #}
```

- **Empty in, empty out:** `None` and `""` render nothing, and a value that can't be parsed renders as-is. A
  filter never raises and breaks the page.
- **Floats are safe:** values go through `str()` before `Decimal`, so `0.1|number` is `0.1`, not the float's
  binary expansion. There's no need for PyFinBot's old `|string|qty` dance.
- **`money`:** rounds half-up (`2.675` → `$2.68`), puts the sign before the symbol, and never shows `-$0.00`.
  `number(places=n)` gives fixed decimals the same way.
- **`date`:** the default `5 Feb 2025` reads the same to AU and US readers. Use `fmt` for anything else. It
  avoids `%-d`, which Windows doesn't support.
- **The viewer's preferences (v0.12):** with `user_settings` in the template context (greentechhub-fastapi's
  `settings_context` supplies it), `date` and `datetime` follow greentechhub-core's:
  - `locale.date_format`: `iso` (2025-02-05), `dmy` (05/02/2025), `mdy` (02/05/2025), `long` (5 Feb 2025);
  - `locale.timezone`: an *aware* datetime is converted first, so 23:30 UTC shows as the next morning in Sydney.
    Naive datetimes and plain dates are left alone, and an unknown zone is ignored;
  - `locale.time_format`: `24h` (13:45) or `12h` (1:45 pm).

  `money` and `number` follow `locale.number_format`: `comma_dot` (1,234.56), `dot_comma` (1.234,56) or
  `space_comma` (1 234,56, with a non-breaking space so a number never wraps). Only the digits change; the sign and
  symbol stay put (`-$1.234,50`).

  Without `user_settings` they render as before. An explicit `fmt`, or keyword (`|date(date_format="iso")`,
  `|datetime(time_format="12h", tz="UTC")`, `|money(number_format="comma_dot")`), wins.

They're plain functions too, e.g. for a CSV export:

```python
from greentechhub_ui.formatting import format_date, format_datetime, money, number

format_date(value, fmt=None, *, date_format=None, tz=None)
format_datetime(value, fmt=None, *, date_format=None, time_format=None, tz=None)
money(value, symbol="$", places=2, *, number_format=None)
number(value, places=None, *, number_format=None)
```

The plain functions never read `user_settings`, so a CSV export keeps `1,234.56` unless you pass `number_format`.

## Shipped signatures (v0.12)

### Select

```jinja
{# select.html #}
gth_select(name, label, options, value=None, errors=None, help_text=None, placeholder=None,
           field_class="mb-3", input_attrs=None)
{# options: {"value", "label"} dicts, (value, label) pairs (core Setting.choices' shape), or bare
   values. value is compared as a string, so 25 selects "25". placeholder adds an empty first
   option. Same ids, aria-describedby and error layout as gth_form_field. #}
```

`gth_segmented` gains `help_text=None, errors=None` and `gth_switch` gains `errors=None, off_value=None`.
Without them both render exactly as before. With `off_value`, the switch adds a hidden input carrying it ahead of the
checkbox, so an unchecked switch still submits a value. Starlette's and Django's form `get()` both return the last
value, so a checked switch reads as its own `value`.

### Settings

Rendering for [greentechhub-core's settings](https://github.com/GreenMachine582/greentechhub-core/blob/dev/docs/settings.md).
The macros duck-type: a setting is anything with `key`, `type`, `label`, `default` and optionally `help_text`,
`choices`, `min`, `max`, `group`, `secret`. Core's `Setting` works as-is, and so does a plain dict. gth-ui doesn't import
core. Field names are the setting keys (`ui.theme`), which is what core's `registry.coerce(key, raw)` takes back.

```jinja
{# settings.html #}
gth_setting_field(setting, value=None, errors=None, name=None, field_class="mb-3", segmented_max=4)
gth_settings_section(id, title, settings, values=None, errors=None, action=None, description=None,
                     error=None, submit_label="Save", form_attrs=None)
```

| `setting.type` | Widget |
|---|---|
| `bool` | `gth_switch`, submitting `"true"`, or `"false"` when unchecked (`off_value`) |
| `choice` with `segmented_max` (4) or fewer options | `gth_segmented` |
| `choice` with more | `gth_select` |
| `int` | `gth_form_field(type="number", step=1)` with `min`/`max` |
| `str` | `gth_form_field` |
| `str` with `secret` | `gth_form_field(type="password")`, always empty, `autocomplete="new-password"`; when a value is saved, "Saved. Leave blank to keep it." and a `<key>.__clear` checkbox |

- `value=None` falls back to `setting.default`. `type` may be a string or an enum (core's `SettingType` is a
  `StrEnum`; a plain `Enum`'s `SettingType.BOOL` also works).
- **Secret settings are write-only.** Pass core's `SECRET_SET` marker (what `Settings.effective()` gives for a
  stored secret) or `None` as the value, never the secret. The input is rendered empty whatever it's given, so even a
  plaintext passed by mistake isn't echoed. The server's save follows one contract (greentechhub-fastapi's
  `SettingsViews` does it for you):
  - a blank field keeps the stored value;
  - `<key>.__clear=true` resets it (`reset_user`/`reset_app`);
  - anything else is the new value (`set_user`/`set_app`, which encrypt it).
- `gth_settings_section` groups fields under an `h3` per `setting.group`, in first-seen order, with ungrouped
  settings first. `values` is key → value (core's `Settings.effective(identity)`) and `errors` is key → messages.
  `error` is a banner.
- With `action`, the fields sit in a `<form method="post">` with a submit button. `form_attrs` adds `hx-*`. Without
  it, the caller brings the form. The section's id is `gth-settings-<id>`, the natural `hx-target` for swapping it
  back with a 422.

**Ready-made page (v0.12).** Two templates render a whole settings page from data, so a service writes no settings
markup (greentechhub-fastapi's `SettingsViews` renders them by default):

| Template | Context |
|---|---|
| `settings_page.html` | extends `page.html` (`page_title`, `page_subtitle`); `settings_sections`: a list of sections; optional `settings_intro` text |
| `settings_section.html` | `section`: one section — the fragment a save response returns (200 + toast, or 422 + errors) |

A section is a mapping (or object) shaped like `gth_settings_section`'s parameters: `id`, `title`, `settings`, and
optionally `values`, `errors`, `error`, `action`, `description`, `submit_label`, `form_attrs`. With an `action` and no
`form_attrs`, the form posts over htmx and swaps the section in place (`hx-post` = action, `hx-target` =
`#gth-settings-<id>`, `hx-swap="outerHTML"`). Sections are stacked rather than tabbed, so a
`/settings#gth-settings-<id>` link lands on its section and a 422 is never hidden in a closed tab.

```python
templates.TemplateResponse(request, "settings_page.html", {
    "page_title": "Settings",
    "settings_sections": [{"id": "preferences", "title": "Preferences", "settings": preference_settings,
                           "values": effective, "action": "/settings/preferences"}],
})
```

The server side of that form, with core (render `settings_section.html` with the section, plus `errors`):

```python
form = await request.form()
errors = {}
for setting in preference_settings:
    try:
        await settings.set_user(identity, setting.key, registry.coerce(setting.key, form.get(setting.key, "")))
    except ValueError as exc:
        errors[setting.key] = [str(exc)]
# 422 + the section re-rendered with errors, or 200 + the section + HX-Trigger toast
```

The playground's `/settings` page runs this flow through the two templates, with dicts standing in for core's
definitions. Its "API token" preference is a secret: it keeps only "saved", never the text.

### Permission-filtered nav and the user menu

`nav_items` is built once, at startup, so permissions are checked per request: `app.html` filters the list through
the `nav_visible` global before the navbar, sidebar and command palette see it.

```python
# navigation.py
NavItem.required_permission  # optional permission string, e.g. "settings.manage"; required_scope still works
greentechhub_ui.navigation.filter_by_scope(nav_items, current_user, granted=None) -> list[NavItem]
```

An item with `required_permission` (or the older `required_scope`) is:

- hidden from anonymous viewers (`current_user` is None);
- shown to any signed-in viewer when `granted` is None, which is the old behaviour for services that haven't opted in;
- otherwise shown only when `granted` holds the permission. `granted` is the viewer's permission strings, e.g.
  greentechhub-core's `RoleResolver.granted()`.

A group left with no children (and no url of its own) is dropped. Breadcrumbs aren't filtered.

```jinja
{# navbar.html #}
gth_navbar(..., user_menu_items=None, logout_url=None, granted=None)
```

With `current_user` set, the navbar ends with a user menu, in both layouts: the user's `username` (or `email`), then
`user_menu_items` (NavItems, permission-filtered the same way), then a divider and **Log out**, a button in a
`<form method="post" action="{logout_url}">`, matching greentechhub-fastapi's `LoginViews` `POST /logout`. Without
items or `logout_url` it shows just the name. `app.html` passes these from the context keys of the same names (see
[docs/contract.md](contract.md)). The menu is in the navbar rather than the sidebar footer, so it's in the same place
in both layouts and the icon rail can't hide it; `{% block sidebar_extra %}` stays free for the service.

The playground has no real sign-in: impersonate a persona (anonymous, viewer or admin) on `/personas` to see both.
A permission-gated page sends you there with `?next=`, and the user menu's "Switch persona" leads back.

### Role assignments

Two templates render a role-assignment admin page from data, over greentechhub-core's `GrantStore` (in-app role
grants per user). greentechhub-fastapi's `RoleAdminViews` renders them by default:

| Template | Renders |
|---|---|
| `roles_page.html` | extends `page.html` (`page_title`, `page_subtitle`) and includes the section |
| `roles_section.html` | `<section id="gth-roles">`: an Assign form, then a table with one row per user — their roles as chips with Save, and Remove through `gth_confirm_delete`. Every save or remove returns this section |

| Context | |
|---|---|
| `roles_url` | base url: `POST` it to assign; `POST` / `DELETE` `<roles_url>/<subject>` (urlencoded, `/` too) to set or remove a user's roles |
| `roles_assignments` | `[{"subject", "roles": [role names]}]` |
| `roles_options` | `[{"value", "label"}]` — the service's roles |
| `roles_error` | optional banner |
| `roles_form` | optional `{"subject", "roles", "errors": {"subject"/"roles": [messages]}}`, echoing the Assign form on a 422 |
| `roles_title` | optional heading (default "Role assignments") |

- `hx-target="#gth-roles"` and `hx-swap="outerHTML"` sit on the section, so the forms and the confirm modal's
  `hx-delete` all swap it whole.
- Save sets a user's roles to exactly the checked chips. Each row's chips get their own id prefix (`gth_chips(id=)`).
- Roles from directory groups or `ROLE_BOOTSTRAP` aren't grants, so they aren't listed; the section says so.

The playground's `/roles` page (impersonate the admin on `/personas`; going there signed out takes you to pick one)
runs this flow over an in-memory stand-in for a
`GrantStore`.
