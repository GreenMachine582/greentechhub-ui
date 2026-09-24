[← Back to README](../README.md)

# 🧱 Component Catalogue

All macros are prefixed `gth-` and are the only public surface consumers should touch — see [docs/architecture.md](architecture.md#public-api-vs-implementation-details) for why.

| Macro | Purpose |
|---|---|
| `gth-page-header` | Title + breadcrumb + action-button slot, top of every page |
| `gth-card` | Standard bordered content container |
| `gth-stat-card` | Dashboard KPI tile (label, value, delta, icon) |
| `gth-table` | Table shell + body with a built-in empty state; the `<tbody>` can be swapped by an HTMX partial (filter/sort controls are the consumer's own — headers render as plain text) |
| `gth-form` | Form wrapper with consistent label/validation-error layout |
| `gth-modal` | Generic modal, focus-trapped (see [docs/accessibility.md](accessibility.md)); server-rendered whole into `#gth-modal-host` for HTMX flows (v0.7) |
| `gth-confirm-delete` / `gth-danger-modal` | Pre-built destructive-action confirmation modal |
| `gth-toast` | Toasts over `HX-Trigger` (`greentechhub_ui.toast()`) and server-side `flashes` in one markup: kinds, title, icon, action link, duration/sticky, surface or solid (v0.8 look) |
| `gth-back-to-top` | Floating "back to top" button past a scroll threshold (v0.8) |
| `gth-pagination` | Renders page controls from `greentechhub-core`'s pagination envelope |
| `gth-table-load-more` | Trailing "load more" row for tables — `gth-pagination`'s `<tr>` sibling (v0.7) |
| `gth-busy-button` | Button for long-running requests: disabled + spinner while in flight, optional "started" toast (v0.7) |
| `gth-combobox` | Server-backed searchable single-select ("autocomplete") (v0.7) |
| `gth-segmented` | Joined radio-button group for 2–4 mutually exclusive choices (v0.7) |
| `gth-data-table` | Table whose navigation is config: `TableState(mode="pages"\|"load_more"\|"infinite"\|"none")`, plus sortable headers — one template for the page and every partial (v0.7) |
| `gth-table-filter` | Debounced search box + filter-control slot that re-requests a `gth-data-table` from page 1 (v0.7) |
| `gth-skeleton` | Loading placeholders — lines, or table rows (v0.7) |
| `gth-badge` | Status pill with good/bad/warn/info/neutral/brand tones, contrast-safe in both modes (v0.7) |
| `gth-tabs` | Bootstrap tabs; panes static (`{% call(key) %}`) or htmx-loaded once on first show (v0.7) |
| `gth-multiselect` | Searchable multi-select with removable chips; tags mode for free text (v0.7) |
| `gth-record-picker` | Field that opens a floating, searchable, sortable, paged table to pick one record (v0.7) |
| `gth-chips` / `gth-switch` | Multi-select filter pills; brand-colored on/off switch (v0.7) |
| `gth-empty-state` | "Nothing here yet" placeholder for empty tables/lists |
| `gth-sidebar` / `gth-navbar` | Renders `nav_items` (built-in + consumer-registered, see [docs/extensibility.md](extensibility.md)), scope-filtered against `current_user`. `gth-sidebar` (v0.8): nested groups along the active trail, filter, icon rail, drawer on phones — `app.html`'s `layout="sidebar"` |
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
greentechhub_ui.navigation.build_nav_items(custom_items, current_user=None, built_in_items=None) -> list[NavItem]
{# The "built-in + consumer-registered, scope-filtered" merge the gth-sidebar/
   gth-navbar row above promises. built_in_items defaults to DEFAULT_NAV_ITEMS
   (empty today — no cross-service nav concept exists yet, e.g. no
   greentechhub-core auth for an "Account" link). Built-ins are placed before
   custom_items, then the combined list is scope-filtered via filter_by_scope
   against current_user. A future addition to DEFAULT_NAV_ITEMS becomes
   visible to every consumer through this helper without any of them changing
   their own code. See docs/extensibility.md for the current_user scoping
   contract. #}
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
gth_segmented(name, options, value=None, label=None, field_class="mb-3")
{# options: [{"value", "label", "style"?, "icon"?}] — style is a
   btn-outline-* class (default btn-outline-primary). Checked = value, or the
   first option. Submits name=<value> like any radio group. #}
```

```python
# toast.py
greentechhub_ui.toast(message, kind="success", *, events=())
# events: extra HX-Trigger events merged into the same header, e.g.
# ["closeModal", "stocksChanged"] — a response can only carry one HX-Trigger.

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
)                                    #   infinite mode then observes that box
rows, total = repo.list(offset=state.offset, limit=state.limit, sort=state.sort,
                        direction=state.direction, **state.filters)
state = state.with_result(total=total)   # or has_next=... when the count is unknown
template = "_stocks_table.html" if is_htmx_swap(request) else "stocks.html"
```

Query parameters are fixed: `page`, `size`, `sort`, `dir`, `partial=rows`, plus each `filter_params` name. Anything not allow-listed (an unsortable column, an off-list size, a negative page) is ignored, not trusted. Return the table fragment for htmx swaps — `HX-Request: true` *without* `HX-History-Restore-Request: true` (a history restore needs the whole page) — and the full page otherwise.

```jinja
{# table.html #}
gth_data_table(state, headers, rows, empty_message="Nothing here yet.", table_class="",
               load_more_label="Load more")      {# rows via {% call(row) %} #}
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
     none      — nothing; pass every row #}

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
gth_chips(name, options, values=(), label=None, field_class="mb-3")
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
                  panel_width="40rem", clearable=True, size="panel", expandable=True)
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
   applied before first paint. Below 992px it's Bootstrap's offcanvas-lg drawer
   (a link click closes it). sidebar.js also remembers which groups were
   opened by hand. {% block sidebar_extra %} fills the footer. #}

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
