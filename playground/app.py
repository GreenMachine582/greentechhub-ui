"""Minimal demo app exercising every shipped gth-* component with fixture
data — no real database. See docs/testing.md. Run directly:

    python playground/app.py
    # or: uv run playground/app.py
"""

import asyncio
from functools import partial
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

# gth_data_table / TableState demo — enough rows for a multi-page pager with
# ellipses, deterministic so tests can assert on them.
RECORD_CATEGORIES = ("Sensor", "Motor", "Cable", "Board")
RECORDS = [
    {
        "id": i,
        "name": f"{('Alpha', 'Bravo', 'Delta', 'Echo', 'Kilo', 'Nova')[i % 6]} part {i:03d}",
        "category": RECORD_CATEGORIES[i % 4],
        "stock": (i * 37) % 250,
        "price": round(((i * 53) % 900) / 10 + 4.99, 2),
    }
    for i in range(1, 121)
]
CATEGORY_OPTIONS = [{"value": "", "label": "All", "style": "btn-outline-secondary"}] + [
    {"value": c, "label": c, "style": "btn-outline-secondary"} for c in RECORD_CATEGORIES
]
PAGINATION_PAGE_SIZE = 5

FLASHES_DEMO = [
    {"message": "This is a success flash message.", "kind": "success"},
    {"message": "This is a warning flash message.", "kind": "warning"},
]

WATCHLIST_DEMO = [
    {"id": 1, "name": "Widget A"},
    {"id": 2, "name": "Widget B"},
    {"id": 3, "name": "Widget C"},
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
templates.env.globals.update(greentechhub_ui.shell_globals(
    service_name="Playground",
    show_logo=True,
    nav_items=greentechhub_ui.navigation.build_nav_items(
        custom_items=[
            {"label": "Playground", "url": "/", "icon": "grid"},
            {"label": "Tables", "url": "/tables", "icon": "table"},
        ],
        # Demonstrates the built-in + consumer-registered merge docs/components.md
        # promises (see docs/components.md#shipped-signatures-v04). DEFAULT_NAV_ITEMS
        # is empty in the real package today (no built-in exists yet) — this
        # override proves built_in_items render first, ahead of custom_items.
        built_in_items=[
            {"label": "Home", "url": "/", "icon": "house"},
        ],
    ),
))

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


WIDGET_ROWS_PAGE_SIZE = 5


def _widget_rows(page: int) -> dict:
    """gth_table_load_more demo — same WIDGETS fixture, page/size style."""
    start = (page - 1) * WIDGET_ROWS_PAGE_SIZE
    rows = WIDGETS[start: start + WIDGET_ROWS_PAGE_SIZE]
    next_url = None
    if start + WIDGET_ROWS_PAGE_SIZE < len(WIDGETS):
        next_url = "/v07-demo/widget-rows?" + urlencode({"page": page + 1})
    return {"widget_rows": rows, "widget_total": len(WIDGETS), "widget_next_url": next_url}


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
        "watchlist": WATCHLIST_DEMO,
        **_paginate_widgets(0),
        **_widget_rows(1),
        **_multi_context(tags=["urgent"]),
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


@app.get("/modal-demo/content", response_class=HTMLResponse)
async def modal_demo_content():
    return HTMLResponse("<p>Loaded via HTMX, right as the modal opened.</p>")


@app.delete("/watchlist-demo/{item_id}", response_class=HTMLResponse)
async def watchlist_demo_delete(request: Request, item_id: int):
    WATCHLIST_DEMO[:] = [item for item in WATCHLIST_DEMO if item["id"] != item_id]
    return templates.TemplateResponse(
        request, "_watchlist_list.html", {"watchlist": WATCHLIST_DEMO}
    )


def _is_htmx_fragment(request: Request) -> bool:
    """htmx swap requests get just the table; plain navigation (and htmx's
    history-restore request, which needs a whole page) get the page."""
    return (request.headers.get("HX-Request") == "true"
            and request.headers.get("HX-History-Restore-Request") != "true")


def _records_state(query, *, mode: str, scroll: bool, base_url: str,
                   table_id: str = "records") -> greentechhub_ui.TableState:
    return greentechhub_ui.TableState.from_query(
        query,
        id=table_id,
        base_url=base_url,
        mode=mode,
        page_size=10,
        page_sizes=(10, 25, 50),
        sortable=("name", "category", "stock", "price"),
        default_sort="name",
        filter_params=("q", "category"),
        push_url=mode == "pages" and table_id == "records",
        max_height="22rem" if scroll else None,
    )


def _query_records(state: greentechhub_ui.TableState):
    """What a consumer's repository does with a TableState: filter, sort,
    then slice (or not, for mode="none")."""
    rows = RECORDS
    if q := state.filters.get("q", "").lower():
        rows = [r for r in rows if q in r["name"].lower()]
    if category := state.filters.get("category"):
        rows = [r for r in rows if r["category"] == category]
    if state.sort:
        rows = sorted(rows, key=lambda r: (r[state.sort], r["id"]),
                      reverse=state.direction == "desc")
    total = len(rows)
    if state.mode != "none":
        rows = rows[state.offset: state.offset + state.limit]
    return rows, state.with_result(total=total)


@app.get("/tables", response_class=HTMLResponse)
async def tables(request: Request, mode: str = "pages", scroll: int = 0):
    if mode not in greentechhub_ui.table.MODES:
        mode = "pages"
    fixed = {"mode": mode, **({"scroll": 1} if scroll else {})}
    state = _records_state(request.query_params, mode=mode, scroll=bool(scroll),
                           base_url="/tables?" + urlencode(fixed))
    rows, state = _query_records(state)
    context = {"table": state, "records": rows, "scroll": bool(scroll),
               "category_options": CATEGORY_OPTIONS}
    if _is_htmx_fragment(request):
        return templates.TemplateResponse(request, "_records_table.html", context)
    return templates.TemplateResponse(request, "tables.html", context)


# gth_sidebar demo — a page rendered in layout="sidebar" with its own nested
# nav, overriding the navbar-layout globals just for this request.
SIDEBAR_DEMO_NAV = [
    {"label": "Dashboard", "url": "/layouts/sidebar", "icon": "speedometer2", "match": "exact"},
    {"label": "Inventory", "icon": "box-seam", "children": [
        {"label": "Parts", "url": "/layouts/sidebar/parts", "icon": "cpu",
         "badge": {"label": "120", "tone": "neutral"}},
        {"label": "Suppliers", "url": "/layouts/sidebar/suppliers", "icon": "truck"},
        {"label": "Archive", "icon": "archive", "children": [
            {"label": "2025", "url": "/layouts/sidebar/archive/2025"},
            {"label": "2024", "url": "/layouts/sidebar/archive/2024"},
        ]},
    ]},
    {"label": "Reports", "url": "/layouts/sidebar/reports", "icon": "bar-chart", "children": [
        {"label": "Monthly", "url": "/layouts/sidebar/reports/monthly"},
        {"label": "Health", "url": "/layouts/sidebar/reports/health",
         "badge": {"label": "3", "tone": "warn"}},
    ]},
    {"label": "Settings", "url": "/layouts/sidebar/settings", "icon": "gear"},
]


@app.get("/layouts/sidebar", response_class=HTMLResponse)
@app.get("/layouts/sidebar/{rest:path}", response_class=HTMLResponse)
async def sidebar_demo(request: Request, rest: str = ""):
    return templates.TemplateResponse(request, "sidebar_demo.html", {
        "layout": "sidebar",
        "nav_items": SIDEBAR_DEMO_NAV,
        "current_path": request.url.path,
        "nav_breadcrumbs": partial(greentechhub_ui.navigation.breadcrumbs_for, SIDEBAR_DEMO_NAV),
    })


@app.get("/v07-demo/widget-rows", response_class=HTMLResponse)
async def v07_widget_rows(request: Request, page: int = 1):
    return templates.TemplateResponse(request, "_widget_rows.html", _widget_rows(page))


@app.get("/v07-demo/widgets", response_class=HTMLResponse)
async def v07_widget_options(request: Request, q: str = ""):
    widgets = [(i, w) for i, w in enumerate(WIDGETS, start=1) if q.strip().lower() in w.lower()]
    return templates.TemplateResponse(request, "_widget_options.html", {"widgets": widgets[:10]})


def _v07_modal_context(widget: str = "", size: str = "S", errors: dict | None = None,
                       search: str = "", record: str = "", record_label: str = "") -> dict:
    picked = widget.isdigit() and 0 < int(widget) <= len(WIDGETS)
    return {
        "widget_value": widget,
        "widget_label": WIDGETS[int(widget) - 1] if picked else search,
        "size": size,
        "record_value": record,
        "record_label": record_label,
        "errors": errors or {},
    }


def _record(record_id: str) -> dict | None:
    if record_id.isdigit() and 0 < int(record_id) <= len(RECORDS):
        return RECORDS[int(record_id) - 1]
    return None


@app.get("/v07-demo/modal", response_class=HTMLResponse)
async def v07_modal(request: Request):
    return templates.TemplateResponse(request, "_v07_modal.html", _v07_modal_context())


@app.post("/v07-demo/modal", response_class=HTMLResponse)
async def v07_modal_submit(request: Request, widget: str = Form(""), size: str = Form("S"),
                           widget_search: str = Form(""), record: str = Form(""),
                           record_label: str = Form("")):
    if not widget.isdigit():
        context = _v07_modal_context(widget, size, {"widget": ["Pick a widget from the list."]},
                                     widget_search, record, record_label)
        # Re-render just the form (hx-target="this"); the modal stays open.
        return templates.TemplateResponse(request, "_v07_form.html", context, status_code=422)
    resp = HTMLResponse("", status_code=204)
    part = _record(record)
    resp.headers["HX-Trigger"] = greentechhub_ui.toast(
        f"Saved {WIDGETS[int(widget) - 1]} ({size})" + (f" for {part['name']}" if part else ""),
        events=["closeModal"],
    )
    return resp


@app.get("/v07-demo/record-picker", response_class=HTMLResponse)
async def v07_record_picker(request: Request):
    """A gth_record_picker panel body: filter + data table of RECORDS. One
    endpoint serves two pickers, so ?for= keeps their table ids apart."""
    picker = request.query_params.get("for")
    picker = picker if picker in ("modal", "page") else "page"
    state = _records_state(request.query_params, mode="pages", scroll=False,
                           base_url="/v07-demo/record-picker?" + urlencode({"for": picker}),
                           table_id=f"picker-{picker}")
    rows, state = _query_records(state)
    # The first load fills the panel (filter + table); the table's own
    # sort/filter/pager swaps target the table (HX-Target: its id) and must
    # get just the table back.
    with_filter = request.headers.get("HX-Target") != state.id
    return templates.TemplateResponse(request, "_record_picker_panel.html",
                                      {"table": state, "records": rows, "with_filter": with_filter})


@app.post("/v07-demo/record-pick", response_class=HTMLResponse)
async def v07_record_pick(part: str = Form(""), part_label: str = Form("")):
    record = _record(part)
    if record is None:
        return HTMLResponse("Nothing picked.")
    return HTMLResponse(f"part={record['id']} ({record['name']})")


@app.get("/v07-demo/tab/{key}", response_class=HTMLResponse)
async def v07_tab(key: str):
    if key not in ("activity", "settings"):
        return HTMLResponse("Unknown tab", status_code=404)
    await asyncio.sleep(0.3)  # long enough to see the skeleton
    return HTMLResponse(f'<p class="mb-0" data-tab-loaded="{key}">Loaded the '
                        f"<strong>{key}</strong> pane from the server.</p>")


@app.post("/v07-demo/chips", response_class=HTMLResponse)
async def v07_chips(request: Request):
    form = await request.form()
    parts = [f"tags={t}" for t in form.getlist("tags")]
    if form.get("alerts"):
        parts.append(f"alerts={form.get('alerts')}")
    return HTMLResponse(", ".join(parts) or "(nothing)")


def _multi_context(widgets=(), tags=(), errors=None) -> dict:
    widget_values = [{"value": w, "label": WIDGETS[int(w) - 1]}
                     for w in widgets if w.isdigit() and 0 < int(w) <= len(WIDGETS)]
    return {"widget_values": widget_values, "tag_values": [{"value": t, "label": t} for t in tags],
            "errors": errors or {}, "saved": None}


@app.post("/v07-demo/multi", response_class=HTMLResponse)
async def v07_multi(request: Request):
    form = await request.form()
    widgets, tags = form.getlist("widgets"), form.getlist("tags")
    if not widgets:
        context = _multi_context(widgets, tags, {"widgets": ["Pick at least one widget."]})
        return templates.TemplateResponse(request, "_multi_form.html", context, status_code=422)
    context = _multi_context(widgets, tags)
    context["saved"] = f"widgets={','.join(widgets)} tags={','.join(tags) or '-'}"
    return templates.TemplateResponse(request, "_multi_form.html", context)


@app.post("/v07-demo/slow-job")
async def v07_slow_job():
    await asyncio.sleep(2)
    resp = HTMLResponse("", status_code=204)
    resp.headers["HX-Trigger"] = greentechhub_ui.toast("Slow job finished")
    return resp


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8500)))
