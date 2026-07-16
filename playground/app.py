"""Minimal demo app exercising every shipped gth-* component with fixture
data — no real database. See docs/testing.md. Run directly:

    python playground/app.py
    # or: uv run playground/app.py
"""

from pathlib import Path
from urllib.parse import quote, urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

import greentechhub_ui

_here = Path(__file__).parent

# ── Fixture data (generic — this demos the kit, not any one consumer) ──────

TASKS = [
    {"id": 1, "title": "Design onboarding flow", "status": "done", "priority": 40},
    {"id": 2, "title": "Fix flaky CI job", "status": "pending", "priority": 85},
    {"id": 3, "title": "Write release notes", "status": "pending", "priority": 30},
    {"id": 4, "title": "Migrate auth to OAuth2", "status": "blocked", "priority": 90},
    {"id": 5, "title": "Update dependency pins", "status": "done", "priority": 20},
    {"id": 6, "title": "Add rate limiting", "status": "pending", "priority": 60},
    {"id": 7, "title": "Improve error messages", "status": "pending", "priority": 45},
    {"id": 8, "title": "Set up staging environment", "status": "blocked", "priority": 75},
]

WIDGETS = [f"Widget #{i}" for i in range(1, 17)]
PAGINATION_PAGE_SIZE = 5

FLASHES_DEMO = [
    {"message": "This is a success flash message.", "kind": "success"},
    {"message": "This is a warning flash message.", "kind": "warning"},
]

# extra_css/extra_js/extra_head demo — data: URIs so this needs no external
# network resource and no extra static file, just to prove the data-driven
# slots (docs/contract.md) actually render and execute in a real browser.
EXTRA_CSS_DATA_URL = "data:text/css," + quote(".gth-extra-css-demo { color: hotpink; }")
EXTRA_JS_DATA_URL = "data:text/javascript," + quote(
    "document.getElementById('gth-extra-js-demo').textContent = 'extra_js worked!';"
)
EXTRA_HEAD_DEMO = '<meta name="gth-extra-head-demo" content="works">'

# ── Jinja/FastAPI wiring — mirrors BottleBot's real templating.py/app.py ───

templates = Jinja2Templates(directory=_here / "templates")
templates.env.loader = ChoiceLoader(
    [
        templates.env.loader,
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]
)
templates.env.globals["brand"] = greentechhub_ui.theme.brand_context(service_name="Playground")
templates.env.globals["nav_items"] = greentechhub_ui.navigation.build_nav_items(
    custom_items=[
        {"label": "Playground", "url": "/", "icon": "grid"},
    ],
    # Demonstrates the built-in + consumer-registered merge docs/components.md
    # promises (see docs/components.md#shipped-signatures-v04). DEFAULT_NAV_ITEMS
    # is empty in the real package today (no built-in exists yet) — this
    # override proves built_in_items render first, ahead of custom_items.
    built_in_items=[
        {"label": "Home", "url": "/", "icon": "house"},
    ],
)
templates.env.globals["theme_css_url"] = "/gth-static/theme.css"
templates.env.globals["icons_css_url"] = "/gth-assets/icons/bootstrap-icons.min.css"
templates.env.globals["toast_js_url"] = "/gth-assets/js/toast.js"
templates.env.globals["theme_toggle_js_url"] = "/gth-assets/js/theme-toggle.js"
templates.env.globals["show_theme_toggle"] = True

app = FastAPI(title="greentechhub-ui playground", docs_url=None, redoc_url=None)
app.mount("/gth-static", StaticFiles(directory=greentechhub_ui.theme_path), name="gth-static")
app.mount("/gth-assets", StaticFiles(directory=greentechhub_ui.static_path), name="gth-assets")


def _validate_budget(value: float) -> list[str] | None:
    errors = []
    if value < 0:
        errors.append("Must be greater than or equal to 0")
    if value > 1000:
        errors.append("Must be less than or equal to 1000")
    return errors or None


def _paginate_widgets(offset: int) -> dict:
    page = WIDGETS[offset: offset + PAGINATION_PAGE_SIZE]
    next_offset = offset + PAGINATION_PAGE_SIZE
    next_url = None
    if next_offset < len(WIDGETS):
        next_url = "/pagination-demo/list?" + urlencode({"offset": next_offset})
    return {"items": page, "next_url": next_url}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "tasks": TASKS,
        "field_errors": {},
        "budget_value": 250,
        "flashes_demo": FLASHES_DEMO,
        "extra_css": [EXTRA_CSS_DATA_URL],
        "extra_js": [EXTRA_JS_DATA_URL],
        "extra_head": [EXTRA_HEAD_DEMO],
        **_paginate_widgets(0),
    })


@app.get("/table-demo/filter", response_class=HTMLResponse)
async def table_filter(request: Request, q: str = ""):
    tasks = TASKS
    if q.strip():
        q_lower = q.strip().lower()
        tasks = [t for t in TASKS if q_lower in t["title"].lower()]
    return templates.TemplateResponse(request, "_tasks_tbody.html", {"tasks": tasks})


@app.get("/pagination-demo/list", response_class=HTMLResponse)
async def pagination_list(request: Request, offset: int = 0):
    return templates.TemplateResponse(request, "_pagination_list.html", _paginate_widgets(offset))


@app.post("/form-demo", response_class=HTMLResponse)
async def form_demo(request: Request, budget: float = Form(...)):
    errors = _validate_budget(budget)
    if errors:
        resp = templates.TemplateResponse(request, "_form_demo.html", {
            "field_errors": {"budget": errors},
            "budget_value": budget,
        }, status_code=422)
        return resp
    resp = templates.TemplateResponse(request, "_form_demo.html", {
        "field_errors": {},
        "budget_value": budget,
    })
    resp.headers["HX-Trigger"] = greentechhub_ui.toast(f"Saved budget: ${budget:.2f}")
    return resp


@app.post("/toast-demo")
async def toast_demo():
    resp = HTMLResponse("", status_code=204)
    resp.headers["HX-Trigger"] = greentechhub_ui.toast("Demo toast triggered!", "success")
    return resp


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8500)))
