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
    {"message": "Your export is ready.", "kind": "info", "title": "Export finished",
     "action": {"label": "Download CSV", "url": "/feedback#flashes"}},
    {"message": "The sync failed: the supplier API timed out.", "kind": "danger",
     "variant": "solid"},
    {"message": "A flash rendered from a FlashMessage-shaped dict, neutral kind.",
     "kind": "neutral"},
]

# gth-toast demo presets: every option toast() offers. Keyed by an
# allow-listed name so the endpoint never echoes request input into a toast.
TOAST_PRESETS = {
    "success": dict(message="Saved successfully.", kind="success"),
    "info": dict(message="Sync scheduled for 02:00.", kind="info"),
    "warning": dict(message="Stock is running low on 3 parts.", kind="warning"),
    "danger": dict(message="Payment failed — the card was declined.", kind="danger"),
    "neutral": dict(message="3 new comments on your draft.", kind="neutral"),
    "title": dict(message="v0.8.0 is live on staging.", kind="success", title="Deploy finished"),
    "action": dict(message="A newer draft of this page exists.", kind="info", title="New version",
                   action={"label": "Review changes", "url": "/feedback#toast"}),
    "sticky": dict(message="This one stays until you close it.", kind="warning",
                   title="Needs attention", duration=0),
    "quick": dict(message="Gone in 1.5 seconds.", kind="neutral", duration=1500),
    "icon": dict(message="Custom icon via icon=\"rocket-takeoff\".", kind="info",
                 icon="rocket-takeoff"),
    "long": dict(message=("A long message wraps inside the toast instead of stretching it: "
                          "supplier ACME-4471 returned 12 partial shipments across three "
                          "warehouses, two of which still need a signed delivery note."),
                 kind="info", title="Partial shipment"),
    "html": dict(message=('<strong>Trusted markup</strong> produced by the server, with a '
                          '<a href="/forms">link</a> — html=True, never for user input.'),
                 kind="success", html=True),
    "solid-success": dict(message="Solid success.", kind="success", variant="solid"),
    "solid-info": dict(message="Solid info.", kind="info", variant="solid"),
    "solid-warning": dict(message="Solid warning — the close button stays dark.", kind="warning",
                          variant="solid"),
    "solid-danger": dict(message="Solid danger.", kind="danger", variant="solid"),
    "solid-neutral": dict(message="Solid neutral.", kind="neutral", variant="solid"),
    "events": dict(message="Also fired watchlistChanged: the sidebar's Confirm delete badge "
                           "re-fetched.", kind="info", events=["watchlistChanged"]),
}

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
# The playground dogfoods layout="sidebar": one page per category, each
# demo section an anchor the sidebar (and the command palette) links to.
PLAYGROUND_NAV = [
    {"label": "Layout", "url": "/layout", "icon": "layout-text-window", "children": [
        {"label": "Page header", "url": "/layout#page-header"},
        {"label": "Card", "url": "/layout#card"},
        {"label": "Stat card", "url": "/layout#stat-card"},
        {"label": "Empty state", "url": "/layout#empty-state"},
        {"label": "Skeleton", "url": "/layout#skeleton"},
        {"label": "Badge", "url": "/layout#badge"},
        {"label": "Tabs", "url": "/layout#tabs"},
    ]},
    {"label": "Data", "url": "/data", "icon": "table", "children": [
        {"label": "Table", "url": "/data#table"},
        {"label": "Pagination", "url": "/data#pagination"},
        {"label": "Load more", "url": "/data#load-more"},
        {"label": "Data tables", "url": "/tables", "icon": "grid-3x3"},
        {"label": "Tree", "url": "/tree", "icon": "diagram-3"},
    ]},
    {"label": "Forms", "url": "/forms", "icon": "input-cursor-text", "children": [
        {"label": "Form + validation", "url": "/forms#form"},
        {"label": "Chips + switch", "url": "/forms#chips"},
        {"label": "Multiselect + tags", "url": "/forms#multiselect"},
        {"label": "Record picker", "url": "/forms#record-picker"},
        {"label": "Busy button", "url": "/forms#busy-button"},
    ]},
    {"label": "Feedback", "url": "/feedback", "icon": "bell", "children": [
        {"label": "Toast", "url": "/feedback#toast"},
        {"label": "Flashes", "url": "/feedback#flashes"},
    ]},
    {"label": "Overlays", "url": "/overlays", "icon": "window-stack", "children": [
        {"label": "Modal", "url": "/overlays#modal"},
        {"label": "Confirm delete", "url": "/overlays#confirm-delete",
         "badge_url": "/nav-badges/watchlist", "badge_event": "watchlistChanged"},
        {"label": "Modal host", "url": "/overlays#modal-host"},
    ]},
    {"label": "Navigation", "url": "/navigation", "icon": "signpost-split", "children": [
        {"label": "Sidebar", "url": "/navigation#sidebar"},
        {"label": "Breadcrumbs", "url": "/navigation#breadcrumbs"},
        {"label": "Command palette", "url": "/navigation#command-palette"},
    ]},
    {"label": "Extensibility", "url": "/extensibility", "icon": "plug"},
]

# Title and subtitle per category page.
PAGES = {
    "layout": ("Layout", "Page structure: headers, cards, stat tiles, empty and loading states, "
               "badges, tabs."),
    "data": ("Data", "Tables and lists, plus the config-driven data tables and the tree on their "
             "own pages."),
    "forms": ("Forms", "Fields, validation, pickers and long-running actions."),
    "feedback": ("Feedback", "Toasts over HX-Trigger, and server-side flashes."),
    "overlays": ("Overlays", "Modals: static, htmx-loaded, confirm-delete, and server-rendered via "
                 "the modal host."),
    "navigation": ("Navigation", "The sidebar this page uses, breadcrumbs derived from it, and the "
                   "command palette."),
    "extensibility": ("Extensibility", "Data-driven extra_head / extra_css / extra_js slots."),
}

templates.env.globals.update(greentechhub_ui.shell_globals(
    service_name="Playground",
    show_logo=True,
    layout="sidebar",
    nav_items=greentechhub_ui.navigation.build_nav_items(
        custom_items=PLAYGROUND_NAV,
        # Demonstrates the built-in + consumer-registered merge docs/components.md
        # promises (see docs/components.md#shipped-signatures-v04). DEFAULT_NAV_ITEMS
        # is empty in the real package today (no built-in exists yet) — this
        # override proves built_in_items render first, ahead of custom_items.
        built_in_items=[
            {"label": "Overview", "url": "/", "icon": "grid", "match": "exact"},
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


def _page(request: Request, name: str, **context):
    """A category page: pages/<name>.html with its title and current_path
    (for the sidebar's active trail and nav_breadcrumbs)."""
    title, subtitle = PAGES.get(name, ("greentechhub-ui playground", ""))
    return templates.TemplateResponse(request, f"pages/{name}.html", {
        "current_path": request.url.path, "page_title": title, "page_subtitle": subtitle,
        **context,
    })


@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    return _page(request, "overview", categories=PLAYGROUND_NAV)


@app.get("/layout", response_class=HTMLResponse)
async def layout_page(request: Request):
    return _page(request, "layout")


@app.get("/data", response_class=HTMLResponse)
async def data_page(request: Request):
    return _page(request, "data", tasks=TASKS, **_paginate_widgets(0), **_widget_rows(1))


@app.get("/forms", response_class=HTMLResponse)
async def forms_page(request: Request):
    return _page(request, "forms", field_errors={}, budget_value=250,
                 **_multi_context(tags=["urgent"]))


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    return _page(request, "feedback", flashes_demo=FLASHES_DEMO)


@app.get("/overlays", response_class=HTMLResponse)
async def overlays_page(request: Request):
    return _page(request, "overlays", watchlist=WATCHLIST_DEMO)


@app.get("/navigation", response_class=HTMLResponse)
async def navigation_page(request: Request):
    return _page(request, "navigation")


@app.get("/extensibility", response_class=HTMLResponse)
async def extensibility_page(request: Request):
    return _page(request, "extensibility", extra_css=[EXTRA_CSS_DATA_URL],
                 extra_js=[EXTRA_JS_DATA_URL], extra_head=[EXTRA_HEAD_DEMO])


_WATCHLIST_BADGE = templates.env.from_string(
    '{% from "badge.html" import gth_badge %}{% if n %}{{ gth_badge(n, "neutral") }}{% endif %}'
)


@app.get("/nav-badges/watchlist", response_class=HTMLResponse)
async def watchlist_badge():
    """Live nav badge: the watchlist size, re-fetched on watchlistChanged."""
    return HTMLResponse(_WATCHLIST_BADGE.render(n=len(WATCHLIST_DEMO)))


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
async def toast_demo(preset: str | None = None):
    if preset is None:
        options = dict(message="Demo toast triggered!", kind="success")
    elif preset in TOAST_PRESETS:
        options = TOAST_PRESETS[preset]
    else:
        return HTMLResponse("Unknown preset", status_code=404)
    resp = HTMLResponse("", status_code=204)
    resp.headers["HX-Trigger"] = greentechhub_ui.toast(**options)
    return resp


@app.get("/modal-demo/content", response_class=HTMLResponse)
async def modal_demo_content():
    return HTMLResponse("<p>Loaded via HTMX, right as the modal opened.</p>")


@app.delete("/watchlist-demo/{item_id}", response_class=HTMLResponse)
async def watchlist_demo_delete(request: Request, item_id: int):
    WATCHLIST_DEMO[:] = [item for item in WATCHLIST_DEMO if item["id"] != item_id]
    resp = templates.TemplateResponse(
        request, "_watchlist_list.html", {"watchlist": WATCHLIST_DEMO}
    )
    resp.headers["HX-Trigger"] = "watchlistChanged"  # refreshes the sidebar badge
    return resp


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
               "category_options": CATEGORY_OPTIONS, "current_path": request.url.path}
    if _is_htmx_fragment(request):
        return templates.TemplateResponse(request, "_records_table.html", context)
    return templates.TemplateResponse(request, "tables.html", context)


# gth_sidebar demo — a page rendered in layout="sidebar" with its own nested
# nav, overriding the navbar-layout globals just for this request.
SIDEBAR_DEMO_NAV = [
    {"label": "Back to playground", "url": "/", "icon": "arrow-left", "match": "exact"},
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
         "badge_url": "/layouts/sidebar-badges/health", "badge_event": "healthChanged"},
    ]},
    {"label": "Settings", "url": "/layouts/sidebar/settings", "icon": "gear"},
]


# Live nav badge demo: an open-issues count the Health item re-fetches
# whenever a response fires healthChanged.
HEALTH_ISSUES = {"open": 3}
_BADGE = templates.env.from_string(
    '{% from "badge.html" import gth_badge %}'
    '{% if n %}{{ gth_badge(n, "warn") }}{% endif %}'
)


@app.get("/layouts/sidebar-badges/health", response_class=HTMLResponse)
async def health_badge():
    return HTMLResponse(_BADGE.render(n=HEALTH_ISSUES["open"]))


@app.post("/layouts/sidebar-badges/health/{action}")
async def health_badge_action(action: str):
    if action == "resolve":
        HEALTH_ISSUES["open"] = max(0, HEALTH_ISSUES["open"] - 1)
    elif action == "reset":
        HEALTH_ISSUES["open"] = 3
    else:
        return HTMLResponse("Unknown action", status_code=404)
    resp = HTMLResponse("", status_code=204)
    resp.headers["HX-Trigger"] = greentechhub_ui.toast(
        f"{HEALTH_ISSUES['open']} open issue(s)", kind="info", events=["healthChanged"]
    )
    return resp


@app.get("/layouts/sidebar", response_class=HTMLResponse)
@app.get("/layouts/sidebar/{rest:path}", response_class=HTMLResponse)
async def sidebar_demo(request: Request, rest: str = ""):
    return templates.TemplateResponse(request, "sidebar_demo.html", {
        "layout": "sidebar",
        "nav_items": SIDEBAR_DEMO_NAV,
        "current_path": request.url.path,
        "nav_breadcrumbs": partial(greentechhub_ui.navigation.breadcrumbs_for, SIDEBAR_DEMO_NAV),
        "command_search_url": "/layouts/sidebar-search",
    })


_COMMAND_ITEMS = templates.env.from_string(
    '{% from "command_palette.html" import gth_command_item %}'
    '{% for r in rows %}{{ gth_command_item(r.name, "/layouts/sidebar/parts?id=" ~ r.id, "cpu",'
    ' r.category ~ " · $" ~ "%.2f"|format(r.price)) }}{% endfor %}'
)


@app.get("/layouts/sidebar-search", response_class=HTMLResponse)
async def sidebar_search(q: str = ""):
    """gth_command_palette search_url demo: parts matching q."""
    q = q.strip().lower()
    rows = [r for r in RECORDS if q and q in r["name"].lower()][:8]
    return HTMLResponse(_COMMAND_ITEMS.render(rows=rows))


# ── gth_tree demo: category › assembly › part, from RECORDS ───────────────

ASSEMBLIES = ("Alpha", "Bravo", "Delta", "Echo", "Kilo", "Nova")
TREE_CONFIG = {  # tree id → select mode (the lazy endpoint renders with it)
    "explorer": "single",
    "reorder": "multi",
}


def _assembly(record: dict) -> str:
    return record["name"].split()[0]


def _parts_of(category: str, assembly: str) -> list[dict]:
    return [r for r in RECORDS if r["category"] == category and _assembly(r) == assembly]


def _part_node(record: dict, *, checked: bool = False, selected: bool = False) -> dict:
    return {"id": f"p:{record['id']}", "label": record["name"], "icon": "cpu",
            "url": f"/tree/detail?id=p:{record['id']}", "checked": checked, "selected": selected}


def _tree_nodes(checked: set[str] = frozenset()) -> list[dict]:
    """Categories and their assemblies; an assembly's parts are lazy unless
    one of them is checked (a re-rendered form), which needs them in place."""
    nodes = []
    for category in RECORD_CATEGORIES:
        cat_id = f"c:{category}"
        cat_checked = cat_id in checked
        count = sum(r["category"] == category for r in RECORDS)
        cat_node = {"id": cat_id, "label": category, "icon": "collection",
                    "url": f"/tree/detail?id={cat_id}", "badge": {"label": str(count)},
                    "checked": cat_checked, "children": []}
        for assembly in ASSEMBLIES:
            parts = _parts_of(category, assembly)
            if not parts:
                continue
            asm_id = f"a:{category}:{assembly}"
            asm_checked = cat_checked or asm_id in checked
            node = {"id": asm_id, "label": f"{assembly} assembly", "icon": "boxes",
                    "url": f"/tree/detail?id={asm_id}", "checked": asm_checked}
            if any(f"p:{p['id']}" in checked for p in parts):
                node["children"] = [_part_node(p, checked=asm_checked or f"p:{p['id']}" in checked)
                                    for p in parts]
                node["expanded"] = True
                cat_node["expanded"] = True
            else:
                node["has_children"] = True
            cat_node["children"].append(node)
        nodes.append(cat_node)
    return nodes


def _resolve_parts(ids: list[str]) -> list[dict]:
    """Top-most checked ids → the parts they stand for."""
    picked = {}
    for node_id in ids:
        kind, _, key = node_id.partition(":")
        if kind == "c":
            rows = [r for r in RECORDS if r["category"] == key]
        elif kind == "a":
            category, _, assembly = key.partition(":")
            rows = _parts_of(category, assembly)
        elif kind == "p" and key.isdigit() and 0 < int(key) <= len(RECORDS):
            rows = [RECORDS[int(key) - 1]]
        else:
            rows = []
        picked.update({r["id"]: r for r in rows})
    return sorted(picked.values(), key=lambda r: r["id"])


@app.get("/tree", response_class=HTMLResponse)
async def tree_page(request: Request):
    # (Not "tree.html": that name is gth_tree's own component file.)
    return templates.TemplateResponse(request, "tree_page.html", {
        "current_path": request.url.path,
        "tree_nodes": _tree_nodes(), "reorder_nodes": _tree_nodes(), "errors": {}, "resolved": None,
    })


@app.get("/tree/nodes", response_class=HTMLResponse)
async def tree_nodes(request: Request, tree: str, parent: str, level: int = 3):
    """gth_tree lazy_url endpoint: one assembly's parts."""
    select = TREE_CONFIG.get(tree)
    kind, _, key = parent.partition(":")
    category, _, assembly = key.partition(":")
    if select is None or kind != "a":
        return HTMLResponse("", status_code=404)
    nodes = [_part_node(p) for p in _parts_of(category, assembly)]
    return templates.TemplateResponse(request, "_tree_nodes.html", {
        "nodes": nodes, "level": level, "tree_id": tree, "select": select,
        "lazy_url": f"/tree/nodes?tree={tree}",
    })


@app.get("/tree/detail", response_class=HTMLResponse)
async def tree_detail(request: Request, id: str):
    kind, _, key = id.partition(":")
    rows = _resolve_parts([id])
    if not rows:
        return HTMLResponse("", status_code=404)
    context = {"kind": kind, "rows": rows, "title": {
        "c": key, "a": key.replace(":", " › ") + " assembly", "p": rows[0]["name"],
    }.get(kind, key)}
    return templates.TemplateResponse(request, "_tree_detail.html", context)


@app.post("/tree/reorder", response_class=HTMLResponse)
async def tree_reorder(request: Request):
    form = await request.form()
    ids = form.getlist("nodes")
    parts = _resolve_parts(ids)
    context = {"reorder_nodes": _tree_nodes(set(ids)), "errors": {}, "resolved": None}
    if not parts:
        context["errors"] = {"nodes": ["Tick at least one category, assembly or part."]}
        return templates.TemplateResponse(request, "_tree_reorder_form.html", context,
                                          status_code=422)
    context["resolved"] = {"ids": ids, "count": len(parts)}
    return templates.TemplateResponse(request, "_tree_reorder_form.html", context)


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
