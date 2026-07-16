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

`gth-modal`/`gth-confirm-delete` are deferred (see [TODO.md](../TODO.md)) — not shipped yet.

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
   messages adapter, etc.) is still an open dependency on greentechhub-core. #}
gth_toast_flashes(flashes)
{# flashes: list of {message, kind} dicts — the same shape toast() produces #}
```
