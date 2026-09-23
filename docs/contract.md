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

The last three default to a public CDN today (so no existing consumer's rendered output changes) rather than a
vendored path — see [static/VENDORED.md](../src/greentechhub_ui/static/VENDORED.md) and [TODO.md](../TODO.md)'s
v0.5/v0.6 entries for why, and when those defaults go away.

`navbar_theme` (optional, default none) is passed straight to `gth_navbar`: unset, the navbar follows the color
mode; `"dark"` pins it dark.

`greentechhub_ui.shell_globals(service_name=..., nav_items=...)` returns every global above (plus `brand`/`nav_items`) pointing at the vendored copies under the `/gth-assets` / `/gth-static` mount prefixes — prefer it over setting them one by one.
