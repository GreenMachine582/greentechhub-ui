[← Back to README](../README.md)

# 🧱 Component Catalogue

All macros are prefixed `gth-` and are the only public surface consumers should touch — see [docs/architecture.md](architecture.md#public-api-vs-implementation-details) for why.

| Macro | Purpose |
|---|---|
| `gth-page-header` | Title + breadcrumb + action-button slot, top of every page |
| `gth-card` | Standard bordered content container |
| `gth-stat-card` | Dashboard KPI tile (label, value, delta, icon) |
| `gth-table` | Sortable/filterable table shell — headers wired for HTMX-driven sort/filter requests, empty-state fallback built in |
| `gth-form` | Form wrapper with consistent label/validation-error layout |
| `gth-modal` | Generic modal, HTMX-loadable content slot, focus-trapped (see [docs/accessibility.md](accessibility.md)) |
| `gth-confirm-delete` / `gth-danger-modal` | Pre-built destructive-action confirmation modal |
| `gth-toast` | Renders `flashes` from the [template context contract](contract.md) as accessible toast notifications |
| `gth-pagination` | Renders page controls from `greentechhub-core`'s pagination envelope |
| `gth-breadcrumbs` | From `nav_items` + current route |
| `gth-empty-state` | "Nothing here yet" placeholder for empty tables/lists |
| `gth-sidebar` / `gth-navbar` | Renders `nav_items` (built-in + consumer-registered, see [docs/extensibility.md](extensibility.md)), scope-filtered against `current_user` |

## Shipped signatures (v0.2)

The table above describes intent; these are the actual macro signatures as implemented, each in its own file under `components/`:

```jinja
{# card.html — body via {% call %} #}
gth_card(title=None, footer=None, card_class="", body_class="")

{# stat_card.html #}
gth_stat_card(label, value, delta=None, delta_tone="neutral", icon=None, card_class="")
{# delta is a pre-formatted string (caller formats it, e.g. "%+.2f"|format(x));
   delta_tone is "good"|"bad"|"neutral" — deliberately not sign-inferred, since
   "lower is better" is a per-consumer judgment call, not a universal one. #}

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
