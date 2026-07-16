[← Back to README](../README.md)

# 🏗️ Architecture

## Public API vs. implementation details

Bootstrap 5, HTMX, and Alpine.js are **implementation details, not public API**. A consuming service imports `greentechhub_ui` and uses `gth-*` macros — it never writes `<link href=".../bootstrap.min.css">` or `<script src=".../htmx.min.js">` itself. The base `app.html` shell owns those includes internally.

This matters because it means the underlying libraries can change without breaking consumers, as long as two things hold:

- **Macro signatures stay stable** (a `gth-table` macro's parameters don't change shape).
- **Rendered semantics stay stable** (a `gth-table` still produces a filterable/sortable table with the same HTML structure consumers can rely on, e.g. for JS that targets `.gth-table` class hooks).

Concretely: if Bootstrap 5 were ever replaced with Tailwind, or HTMX with a successor, that's an internal `greentechhub-ui` change — consuming services' templates (which only call `gth-*` macros) shouldn't need to change at all. This is the same discipline as `greentechhub-core`'s `AuthAdapter` interface — consumers depend on the contract, not the implementation. See [docs/contract.md](contract.md) for the template-side contract that makes this concrete.

## Package layout

Internally structured so `theme/` has **no dependency on `components/`** — this is deliberate groundwork for a possible future split into `greentechhub-theme` (branding/tokens only) and `greentechhub-ui` (full component library), per the open decisions in [TODO.md](../TODO.md). Not split today; kept as one repo until there's a real consumer that wants branding without components.

```
greentechhub-ui/
├── src/greentechhub_ui/
│   ├── theme/                  # self-contained — no imports from components/
│   │   ├── tokens.py           # brand colors, spacing, typography as CSS custom properties
│   │   └── theme.css
│   ├── templates/
│   │   ├── app.html            # owns Bootstrap/HTMX/Alpine <link>/<script> includes
│   │   ├── dashboard.html
│   │   └── auth/
│   │       └── login.html
│   ├── components/
│   │   ├── card.html
│   │   ├── table.html
│   │   ├── modal.html
│   │   ├── form.html
│   │   ├── pagination.html
│   │   ├── breadcrumbs.html
│   │   ├── stat_card.html
│   │   ├── empty_state.html
│   │   ├── confirm_delete.html
│   │   ├── page_header.html
│   │   ├── sidebar.html
│   │   └── navbar.html
│   ├── static/                 # vendored Bootstrap/HTMX/Alpine + icons/logo — internal, not linked to directly by consumers
│   │   ├── css/
│   │   ├── js/
│   │   ├── icons/
│   │   └── logo/
│   ├── navigation.py
│   └── extensions.py           # extension-point registration — see docs/extensibility.md
├── playground/                 # demo app exercising every component — see docs/testing.md
│   ├── app.py                  # minimal FastAPI app
│   └── templates/
├── tests/
│   ├── test_macros_snapshot.py
│   ├── test_html_validity.py
│   └── e2e/
│       └── test_playground.py  # Playwright smoke tests against playground/
├── pyproject.toml
└── README.md
```

## Integration pattern

**FastAPI:**

```python
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
import greentechhub_ui

templates = Jinja2Templates(directory="templates")  # service-local pages
templates.env.loader = ChoiceLoader([
    templates.env.loader,
    FileSystemLoader(greentechhub_ui.templates_path),  # shared base/components
])
templates.env.globals["brand"] = greentechhub_ui.theme.brand_context()
```

**Django (GreenTechHub):**

```python
# settings.py
TEMPLATES = [{
    "BACKEND": "django.template.backends.jinja2.Jinja2",
    "DIRS": [greentechhub_ui.templates_path, greentechhub_ui.components_path],
    "OPTIONS": {"environment": "greentechhub.jinja_env.environment"},
}]
```

```python
# greentechhub/jinja_env.py — supplies the same context contract Django-side
def environment(**options):
    env = Environment(**options)
    env.globals.update(url_for=django_url_for_shim, brand=greentechhub_ui.theme.brand_context())
    return env
```

Note what's absent from both samples: no reference to Bootstrap, HTMX, or Alpine by name. That's intentional — see the public API section above.

## Internal interaction conventions

*(Implementation detail, documented for contributors to `greentechhub-ui` itself — not something a consumer calling `gth-modal` needs to know.)*

- **HTMX owns server round-trips**: table filter/sort/pagination, form submits, toast-triggering via an `HX-Trigger` response header wired to `greentechhub-core`'s flash module.
- **Alpine.js owns pure client state**: dropdown/tab/accordion open state, dark-mode toggle, modal open/close where no server data is needed.
- These conventions live inside the package's components — a contributor extending `greentechhub-ui` needs to know them; a consumer calling `gth-modal` does not.
