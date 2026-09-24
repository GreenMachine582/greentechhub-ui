[← Back to README](../README.md)

# 🔌 The Framework-Agnostic Template Contract

This is the standout design decision of `greentechhub-ui` — the piece that makes the rest of the package possible.

FastAPI's `Jinja2Templates` and Django's `Jinja2` template backend (`django.template.backends.jinja2.Jinja2`) are **both just Jinja2 underneath**. That means the same `.html` macro files can render correctly from a FastAPI service *and* from GreenTechHub's Django app — without a rewrite — as long as the macros don't reach for framework-specific globals (FastAPI's `request`, Django's `request.user`, differing `url_for` signatures).

So `greentechhub-ui` macros are written against a **plain context contract** instead of a framework object:

```python
# what every macro expects in its Jinja2 context — nothing framework-specific
{
  "nav_items": [...],        # from navigation.py
  "current_user": {...} | None,
  "flashes": [...],          # shape is greentechhub_core.types.FlashMessage; production/storage (session
                              # wiring, a Django messages adapter, etc.) is owned by the framework adapter
                              # (greentechhub_fastapi.flash / a Django messages bridge), not greentechhub-core
  "url_for": callable,       # injected per-framework: FastAPI's request.url_for, or a thin Django shim
  "brand": {"name": "GreenTechHub", "logo_url": "...", "logo_light_url": "...", "favicon_url": "...",
            "service_name": "PyFinBot"},   # logo_light_url optional: the navbar's light-mode logo
  "extra_head": [...],       # optional per-page <head> additions (trusted HTML strings) — see docs/extensibility.md
  "extra_css": [...],        # optional stylesheet URLs, e.g. a page needing a charting library
  "extra_js": [...],         # optional script URLs, same idea as extra_css
}
```

`brand.logo_url`/`brand.favicon_url` are populated by `theme.brand_context(show_logo=True, static_url_prefix=...)`
— a Python-side opt-in (both `None` by default), distinct from the `*_url` Jinja globals below, which a consumer
sets directly as template defaults rather than through a Python function argument.

**Practical effect**: GreenTechHub doesn't have to migrate off Django to get the same navbar, cards, and modals as the FastAPI services — it wires Django's Jinja2 backend to the same template/macro directories and supplies the same context shape.

Worth calling out explicitly because it's not obvious from "just use Jinja2 macros" — the contract discipline is what actually makes it portable. Concrete wiring for both frameworks is in [docs/architecture.md](architecture.md#integration-pattern).

## Setup (FastAPI and Django)

`greentechhub-ui` depends on `jinja2` alone — never on a web framework — so the wiring is split: gth-ui provides
framework-neutral helpers, each framework adapter the small framework-specific half.

| Need | gth-ui (any framework) | FastAPI (`greentechhub-fastapi`) | Django |
|---|---|---|---|
| Templates loadable | `greentechhub_ui.install(env, **shell_globals kwargs)` — adds gth-ui's loaders *after* the app's own and installs `shell_globals()` | `install(templates.env, service_name=…, nav_items=…)` on `Jinja2Templates` | `install()` inside the Jinja2 backend's `environment` callable; or `template_dirs()` in `TEMPLATES[...]["DIRS"]` |
| Static files served | `static_dirs()` — `{"/gth-assets": static_path, "/gth-static": theme_path}`, the same prefixes `shell_globals()` renders URLs for | `mount_static_dirs(app, greentechhub_ui.static_dirs())` | `STATICFILES_DIRS = [(p.strip("/"), d) for p, d in static_dirs().items()]` |
| `current_path` per request | — | `Jinja2Templates(..., context_processors=[ui_context])` | gth-django's context processor (see its `docs/context.md`) |
| htmx: fragment or page? | `greentechhub_ui.htmx.wants_fragment(request.headers)`, `hx_target(...)`, `TableState.is_own_swap(...)` | same (Starlette headers are a Mapping) | same (`request.headers`) |
| htmx: 204 with `HX-Trigger` | `toast(...)` / `htmx.trigger(...)` build the header value | `hx_response(greentechhub_ui.toast("Saved"))` | `HttpResponse(status=204, headers={"HX-Trigger": toast(...)})` |
| One macro for an endpoint | `render_macro(env, "badge.html", "gth_badge", "3", "warn")` | same | same (the backend's `env`) |

```python
# FastAPI
templates = Jinja2Templates(directory="templates", context_processors=[ui_context])
greentechhub_ui.install(templates.env, service_name="PyFinBot", nav_items=build_nav_items([...]))
mount_static_dirs(app, greentechhub_ui.static_dirs())

# Django — settings.TEMPLATES[...]["OPTIONS"]["environment"] = "myproject.jinja2.environment"
def environment(**options):
    return greentechhub_ui.install(Environment(**options), service_name="GreenTechHub", nav_items=[...])
```

`templates/page.html` is an optional base for ordinary pages: `app.html` plus a `gth_page_header` from
`page_title` / `page_subtitle`, breadcrumbs derived from the nav, `{% block page %}` for the body and
`{% block header_actions %}` for the header's action slot.

## Static asset globals

`app.html` never hardcodes an asset path — it resolves each one through a Jinja global, falling back to a
default when a consumer doesn't set one. This is what makes swapping hosting (bundled-per-service vs. a shared
static host, see [docs/theming.md](theming.md)) a globals change, not a template change:

| Global | Default when unset |
|---|---|
| `theme_css_url` | none (no stylesheet rendered) |
| `icons_css_url` | none (no stylesheet rendered) |
| `toast_js_url` | none (no script rendered) |
| `theme_toggle_js_url` | none (no script rendered) |
| `bootstrap_css_url` | the upstream Bootstrap 5.3.3 CDN URL |
| `bootstrap_js_url` | the upstream Bootstrap 5.3.3 CDN URL |
| `htmx_js_url` | the upstream HTMX 1.9.10 CDN URL |
| `modal_host_js_url` | none (no script rendered) — needed for the `#gth-modal-host` flow (v0.7) |
| `combobox_js_url` | none (no script rendered) — needed by `gth-combobox` and `gth-multiselect` (v0.7) |
| `record_picker_js_url` | none (no script rendered) — needed by `gth-record-picker` (v0.7) |
| `tree_js_url` | none (no script rendered) — needed by `gth-tree` (v0.8) |
| `back_to_top_js_url` | none — with it set, `app.html` renders `gth-back-to-top` and its script (v0.8) |
| `sidebar_js_url` | none — rendered only in `layout="sidebar"`, needed by `gth-sidebar` (v0.8) |
| `command_palette_js_url` | none — with it set, `gth-command-palette` is included in `layout="sidebar"`, or in the default layout when `show_command_palette` is true (v0.8) |

The last three default to a public CDN today (so no existing consumer's rendered output changes) rather than a
vendored path — see [static/VENDORED.md](../src/greentechhub_ui/static/VENDORED.md) and [TODO.md](../TODO.md)'s
v0.5/v0.6 entries for why, and when those defaults go away.

`navbar_theme` (optional, default none) is passed straight to `gth_navbar`: unset, the navbar follows the color
mode; `"dark"` pins it dark.

**Layout and navigation globals (v0.8)** — all optional:

| Global | Meaning |
|---|---|
| `layout` | `"navbar"` (default: exactly the v0.7 shell) or `"sidebar"` (nav_items move into `gth_sidebar`; a drawer below 992px) |
| `current_path` | per-request: the path `gth_sidebar` marks active and `nav_breadcrumbs` resolves |
| `nav_breadcrumbs(path)` | breadcrumbs for `gth_page_header`, derived from `nav_items` (installed by `shell_globals`) |
| `nav_mark_active`, `nav_flatten` | helpers `gth_sidebar` / `gth-command-palette` call (installed by `shell_globals`) |
| `show_command_palette` | include the palette (and a navbar search button) in the default layout |
| `command_search_url` | the palette's server search endpoint (`gth_command_item` rows) |

A per-request context value overrides a global of the same name — e.g. one page can render `layout="sidebar"`
with its own `nav_items` (the playground's `/layouts/sidebar`).

`greentechhub_ui.shell_globals(service_name=..., nav_items=...)` returns every global above (plus `brand`/`nav_items`) pointing at the vendored copies under the `/gth-assets` / `/gth-static` mount prefixes — prefer it over setting them one by one.
