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
| `gth-toast` | Renders `flashes` from the [template context contract](contract.md) as accessible toast notifications |
| `gth-pagination` | Renders page controls from `greentechhub-core`'s pagination envelope |
| `gth-table-load-more` | Trailing "load more" row for tables — `gth-pagination`'s `<tr>` sibling (v0.7) |
| `gth-busy-button` | Button for long-running requests: disabled + spinner while in flight, optional "started" toast (v0.7) |
| `gth-combobox` | Server-backed searchable single-select ("autocomplete") (v0.7) |
| `gth-segmented` | Joined radio-button group for 2–4 mutually exclusive choices (v0.7) |
| `gth-data-table` | Table whose navigation is config: `TableState(mode="pages"\|"load_more"\|"infinite"\|"none")`, plus sortable headers — one template for the page and every partial (v0.7) |
| `gth-table-filter` | Debounced search box + filter-control slot that re-requests a `gth-data-table` from page 1 (v0.7) |
| `gth-skeleton` | Loading placeholders — lines, or table rows (v0.7) |
| `gth-empty-state` | "Nothing here yet" placeholder for empty tables/lists |
| `gth-sidebar` / `gth-navbar` | Renders `nav_items` (built-in + consumer-registered, see [docs/extensibility.md](extensibility.md)), scope-filtered against `current_user` |

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
