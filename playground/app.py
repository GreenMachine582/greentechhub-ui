"""Minimal demo app exercising every shipped gth-* component with fixture
data — no real database. See docs/testing.md. Its wiring is exactly what a
FastAPI consumer writes (greentechhub_ui.install / static_dirs plus
greentechhub_fastapi's ui_context / mount_static_dirs / hx_response — see
docs/contract.md "Setup"); everything else here is demo fixtures. Run
directly:

    python playground/app.py
    # or: uv run playground/app.py
"""

import asyncio
import csv
import io
import json
import re
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from urllib.parse import quote, unquote, urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from greentechhub_core.email import InMemoryEmailSender
from greentechhub_core.notifications import InMemoryNotificationStore, new_notification
from greentechhub_core.security import InMemoryTokenStore, OneTimeTokens
from greentechhub_core.settings.builtins import (
    SITE_BANNER_KEY,
    SITE_BANNER_TONE_KEY,
    site_banner_settings,
)
from greentechhub_fastapi import register_email
from greentechhub_fastapi.auth import EmailVerificationViews, PasswordResetViews
from greentechhub_fastapi.htmx import hx_response
from greentechhub_fastapi.templating import mount_static_dirs, ui_context
from markupsafe import Markup
from starlette.datastructures import UploadFile

import greentechhub_ui
from greentechhub_ui.htmx import trigger, wants_fragment

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
        # Every 5 days from Jan 2025 to Aug 2026 — spans two AU financial years.
        "added": date(2025, 1, 1) + timedelta(days=i * 5),
    }
    for i in range(1, 121)
]
# The table refresh demo appends to RECORDS and the bulk actions change stock;
# POST /demo/reset trims it back and restores the stock.
_RECORDS_INITIAL = len(RECORDS)
_RECORDS_STOCK = [r["stock"] for r in RECORDS]
# No per-option "style", so gth_segmented draws its brand track (v0.12).
CATEGORY_OPTIONS = [{"value": "", "label": "All"}] + [
    {"value": c, "label": c} for c in RECORD_CATEGORIES
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

_WATCHLIST_INITIAL = (
    {"id": 1, "name": "Widget A"},
    {"id": 2, "name": "Widget B"},
    {"id": 3, "name": "Widget C"},
)
# Module state the confirm-delete demo mutates; POST /demo/reset restores it.
WATCHLIST_DEMO = [dict(item) for item in _WATCHLIST_INITIAL]

# extra_css/extra_js/extra_head demo — data: URIs so this needs no external
# network resource and no extra static file, just to prove the data-driven
# slots (docs/contract.md) actually render and execute in a real browser.
EXTRA_CSS_DATA_URL = "data:text/css," + quote(".gth-extra-css-demo { color: hotpink; }")
EXTRA_JS_DATA_URL = "data:text/javascript," + quote(
    "document.getElementById('gth-extra-js-demo').textContent = 'extra_js worked!';"
)
EXTRA_HEAD_DEMO = '<meta name="gth-extra-head-demo" content="works">'

# ── Jinja/FastAPI wiring — the setup any consumer uses (docs/contract.md,
#    "Setup"): gth-ui's framework-neutral install()/static_dirs() plus
#    greentechhub-fastapi's ui_context/mount_static_dirs ─────────────────────

# ui_context supplies current_path to every page: the sidebar's active trail
# and nav_breadcrumbs need it.
THEME_COOKIE = "playground-theme"
THEME_MODES = ("light", "dark", "system")


def theme_context(request: Request) -> dict:
    """What a service's settings wiring supplies (greentechhub-fastapi's
    register_settings, later): the signed-in user's saved ui.theme as theme_mode,
    and where the toggle saves. The playground has no users, so a cookie stands in
    for the store — per browser, so e2e tests don't share a theme."""
    mode = request.cookies.get(THEME_COOKIE)
    return {"theme_save_url": "/demo/theme", "theme_mode": mode if mode in THEME_MODES else None}


# Personas: the playground has no auth, so you impersonate one (ServiceNow
# style) on /personas, and a cookie stands in for the session. A service's
# settings wiring (greentechhub-fastapi's register_settings) supplies the same
# keys: current_user (core's Identity), granted (RoleResolver), user_menu_items
# and logout_url.
USER_COOKIE = "playground-user"
PERSONAS = {
    "anonymous": {"user": None, "granted": frozenset(), "icon": "incognito",
                  "description": "Signed out. No user menu; permission-gated pages send you here."},
    "viewer": {"user": {"username": "viewer", "email": "viewer@example.com"},
               "granted": frozenset(), "icon": "person",
               "description": "Signed in with no permissions: the user menu and Preferences, "
                              "but not Settings \u203a App or Roles."},
    "admin": {"user": {"username": "admin", "email": "admin@example.com"},
              "granted": frozenset({"settings.manage"}), "icon": "person-gear",
              "description": "Holds settings.manage: Settings \u203a App and the Roles page "
                             "appear in the sidebar."},
}


def _persona(request: Request) -> str:
    key = request.cookies.get(USER_COOKIE, "")
    return key if key in PERSONAS and PERSONAS[key]["user"] else "anonymous"


def user_context(request: Request) -> dict:
    persona = PERSONAS[_persona(request)]
    if persona["user"] is None:
        return {"current_user": None}
    return {
        "current_user": persona["user"],
        "granted": persona["granted"],
        "user_menu_items": [{"label": "Settings", "url": "/settings", "icon": "sliders"},
                            {"label": "Switch persona", "url": "/personas",
                             "icon": "person-badge"}],
        "logout_url": "/demo/logout",
        "notifications_url": NOTIFICATIONS_URL,
    }


# What the admin persona holds: Settings › App and the Roles page need it.
MANAGE_PERMISSION = "settings.manage"


def _has(request: Request, permission: str) -> bool:
    return permission in user_context(request).get("granted", ())


def _local_path(url: str | None) -> str | None:
    """`url` if it's a path on this site, else None — so ?next= can't send
    anyone off-site (no //host, no scheme, no backslash tricks)."""
    if not url or not url.startswith("/") or url.startswith("//") or "\\" in url:
        return None
    return url


def _require_persona(request: Request, permission: str) -> Response | None:
    """None when the impersonated persona holds `permission`. Otherwise a page
    request is sent to /personas to pick one that does (like
    require_page_permission's login redirect), and htmx / non-GET calls get a
    plain 403 (like require_permission) — a fragment can't redirect sensibly."""
    if _has(request, permission):
        return None
    if request.method != "GET" or request.headers.get("HX-Request"):
        return Response(status_code=403)
    query = urlencode({"next": request.url.path, "need": permission})
    return Response(status_code=303, headers={"Location": f"/personas?{query}"})


PREFS_COOKIE = "playground-prefs"


def _preferences(request: Request) -> dict[str, object]:
    """This browser's saved Preferences (all but the theme, which has its own
    cookie): per browser like a service's per-user store, so one visitor's —
    or one e2e test's — choices never leak into another's pages."""
    try:
        values = json.loads(unquote(request.cookies.get(PREFS_COOKIE, "")) or "{}")
    except ValueError:
        return {}
    return values if isinstance(values, dict) else {}


def settings_values_context(request: Request) -> dict:
    """user_settings, as greentechhub-fastapi's settings_context supplies it:
    here only the Preferences this browser saved, so pages render the defaults
    until then. The |date / |datetime filters follow it."""
    prefs = _preferences(request)
    return {"user_settings": prefs} if prefs else {}


def site_banners_context(request: Request) -> dict:
    """site_banners for app.html's banner slot.

    - The admin-set site banner (Settings › App: site.banner + site.banner_tone)
      on every page while it's non-empty — what greentechhub-fastapi's opt-in
      site banner does with core's site_banner_settings(). Its id is fixed and
      a dismissal is remembered against the message, so editing the text
      brings it back.
    - A demo notice on /feedback only, so the other pages (and their layout
      tests) stay as they are. ?banner_v=2 edits its message, which brings a
      dismissed banner back.
    """
    banners = []
    if message := str(SETTINGS_VALUES.get(SITE_BANNER_KEY) or "").strip():
        tone = SETTINGS_VALUES.get(SITE_BANNER_TONE_KEY, "warn")
        banners.append({"message": message, "tone": tone, "id": "site"})
    if request.url.path == "/feedback":
        edited = request.query_params.get("banner_v") == "2"
        notice = ("Playground notice (edited): this banner's message changed, so it shows again."
                  if edited else
                  "Playground notice: dismiss this banner and reload — it stays hidden.")
        banners.append({"message": notice, "id": "playground-intro",
                        "action": {"label": "How it works", "url": "/feedback#alert-banner"}})
    return {"site_banners": banners} if banners else {}


templates = Jinja2Templates(directory=_here / "templates",
                            context_processors=[ui_context, theme_context, user_context,
                                                settings_values_context, site_banners_context])
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
        {"label": "Action menu", "url": "/data#action-menu"},
        {"label": "Description list", "url": "/data#description-list"},
        {"label": "Progress", "url": "/data#progress"},
        {"label": "Pagination", "url": "/data#pagination"},
        {"label": "Load more", "url": "/data#load-more"},
        {"label": "Formatting", "url": "/data#formatting"},
        {"label": "Data tables", "url": "/tables", "icon": "grid-3x3"},
        {"label": "Tree", "url": "/tree", "icon": "diagram-3"},
    ]},
    {"label": "Forms", "url": "/forms", "icon": "input-cursor-text", "children": [
        {"label": "Form + validation", "url": "/forms#form"},
        {"label": "Chips + switch", "url": "/forms#chips"},
        {"label": "Date range", "url": "/forms#date-range"},
        {"label": "File drop", "url": "/forms#file-drop"},
        {"label": "Multiselect + tags", "url": "/forms#multiselect"},
        {"label": "Record picker", "url": "/forms#record-picker"},
        {"label": "Busy button", "url": "/forms#busy-button"},
    ]},
    {"label": "Feedback", "url": "/feedback", "icon": "bell", "children": [
        {"label": "Toast", "url": "/feedback#toast"},
        {"label": "Error toasts", "url": "/feedback#error-toasts"},
        {"label": "Flashes", "url": "/feedback#flashes"},
        {"label": "Inline alert", "url": "/feedback#inline-alert"},
        {"label": "Alert banner", "url": "/feedback#alert-banner"},
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
    {"label": "Settings", "url": "/settings", "icon": "sliders", "children": [
        {"label": "Preferences", "url": "/settings#gth-settings-preferences"},
        # Only an admin sees this link (the demo sign-in on /extensibility).
        {"label": "App", "url": "/settings#gth-settings-app",
         "required_permission": "settings.manage"},
    ]},
    {"label": "Extensibility", "url": "/extensibility", "icon": "plug"},
    {"label": "Personas", "url": "/personas", "icon": "person-badge"},
    {"label": "Login page", "url": "/login-demo", "icon": "box-arrow-in-right"},
    # Only the demo admin (sign in on /extensibility) sees this.
    {"label": "Roles", "url": "/roles", "icon": "people",
     "required_permission": "settings.manage"},
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
    "personas": ("Personas", "Impersonate a persona to see the playground as they would: the user "
                             "menu, permission-filtered nav and gated pages."),
    "settings": ("Settings", "gth_settings_section over setting definitions: each type picks its "
                 "own widget."),
    "outbox": ("Outbox", "The emails the password reset and email verification demos sent."),
}

greentechhub_ui.install(
    templates.env,
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
)

app = FastAPI(title="greentechhub-ui playground", docs_url=None, redoc_url=None)
mount_static_dirs(app, greentechhub_ui.static_dirs())


def _macro(template: str, macro: str, *args, **kwargs) -> Markup:
    """One gth macro rendered for an htmx endpoint (live badges, palette rows,
    lazy tree nodes), with the env's globals in scope."""
    return greentechhub_ui.render_macro(templates.env, template, macro, *args, **kwargs)


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
        next_url = "/demo/widget-rows?" + urlencode({"page": page + 1})
    return {"widget_rows": rows, "widget_total": len(WIDGETS), "widget_next_url": next_url}


def _paginate_widgets(offset: int) -> dict:
    page = WIDGETS[offset: offset + PAGINATION_PAGE_SIZE]
    next_offset = offset + PAGINATION_PAGE_SIZE
    next_url = None
    if next_offset < len(WIDGETS):
        next_url = "/pagination-demo/list?" + urlencode({"offset": next_offset})
    return {"items": page, "next_url": next_url}


def _page(request: Request, name: str, **context):
    """A category page: pages/<name>.html (extends gth-ui's page.html) with its
    title; current_path comes from the ui_context processor."""
    title, subtitle = PAGES.get(name, ("greentechhub-ui playground", ""))
    return templates.TemplateResponse(request, f"pages/{name}.html", {
        "page_title": title, "page_subtitle": subtitle, **context,
    })


# ── Settings demo ─────────────────────────────────────────────────────────────
# Plain dicts shaped like greentechhub-core's Setting (key, type, label, default,
# help_text, choices, min, max, group): the macros duck-type, so a service passes
# core's Setting objects and Settings.effective() values the same way. The coercion
# below stands in for core's registry.coerce(key, raw).


def _setting_dict(setting) -> dict:
    """A greentechhub-core Setting in this demo's dict shape (the save handler
    reads setting["key"] etc.), so a section can list core's own definitions."""
    d = {"key": setting.key, "type": str(setting.type), "label": setting.label,
         "default": setting.default, "help_text": setting.help_text}
    if setting.choices:
        d["choices"] = list(setting.choices)
    if setting.min is not None or setting.max is not None:
        d["min"], d["max"] = setting.min, setting.max
    return d


SETTINGS_DEMO = {
    "preferences": ("Preferences", "Only you see these.", [
        {"key": "ui.theme", "type": "choice", "label": "Theme", "default": "system",
         "help_text": "Light, dark, or follow your device.", "group": "Appearance",
         "choices": [("light", "Light"), ("dark", "Dark"), ("system", "System")]},
        {"key": "locale.timezone", "type": "choice", "label": "Timezone", "default": "UTC",
         "help_text": "More than four choices, so a select.", "group": "Locale",
         "choices": [(z, z) for z in ("UTC", "Australia/Sydney", "Australia/Perth",
                                      "Europe/London", "America/New_York", "Asia/Tokyo")]},
        {"key": "locale.date_format", "type": "choice", "label": "Date format", "default": "iso",
         "group": "Locale", "choices": [("iso", "2026-01-31"), ("dmy", "31/01/2026"),
                                        ("mdy", "01/31/2026"), ("long", "31 Jan 2026")]},
        {"key": "ui.density", "type": "choice", "label": "Density", "default": "comfortable",
         "help_text": "Compact fits more rows and fields on screen.", "group": "Appearance",
         "choices": [("comfortable", "Comfortable"), ("compact", "Compact")]},
        {"key": "ui.motion", "type": "choice", "label": "Motion", "default": "system",
         "help_text": "Reduce turns off animations and transitions.", "group": "Appearance",
         "choices": [("system", "Follow device"), ("reduce", "Reduce"), ("full", "Full")]},
        {"key": "ui.sidebar_default", "type": "choice", "label": "Sidebar",
         "default": "expanded", "group": "Appearance",
         "help_text": "How the sidebar starts until you toggle it in this browser.",
         "choices": [("expanded", "Expanded"), ("rail", "Icons only")]},
        {"key": "locale.number_format", "type": "choice", "label": "Number format",
         "default": "comma_dot", "group": "Locale",
         "choices": [("comma_dot", "1,234.56"), ("dot_comma", "1.234,56"),
                     ("space_comma", "1 234,56")]},
        {"key": "ui.page_size", "type": "int", "label": "Rows per page", "default": 25,
         "min": 5, "max": 200, "help_text": "5 to 200.", "group": "Tables"},
        {"key": "demo.api_token", "type": "str", "secret": True, "label": "API token",
         "default": "", "group": "Integrations",
         "help_text": "A fake credential: write-only, like a service's secret setting."},
    ]),
    "app": ("App", "Everyone sees these. A service gates this section on a permission. Save a site "
                   "banner and it shows above every page.", [
        # greentechhub-core's own site banner settings: the message (empty for
        # none) and one of gth_alert_banner's tones.
        *map(_setting_dict, site_banner_settings(edit_permission=MANAGE_PERMISSION)),
        {"key": "site.maintenance", "type": "bool", "label": "Maintenance mode", "default": False,
         "help_text": "An unchecked switch still submits \"false\" (off_value)."},
    ]),
}
SETTINGS_VALUES: dict[str, object] = {}


def _coerce_setting(setting: dict, raw: str | None) -> object:
    if setting["type"] == "bool":
        if raw in ("true", "false"):
            return raw == "true"
        raise ValueError("Choose on or off.")
    if setting["type"] == "int":
        try:
            value = int((raw or "").strip())
        except ValueError:
            raise ValueError("Enter a whole number.") from None
        if not setting["min"] <= value <= setting["max"]:
            raise ValueError(f"Must be between {setting['min']} and {setting['max']}.")
        return value
    if setting["type"] == "choice" and raw not in [v for v, _ in setting["choices"]]:
        raise ValueError("Pick one of the options.")
    return raw or ""


def _saved_settings(request: Request) -> dict[str, object]:
    """SETTINGS_VALUES (the App section, shared), this browser's Preferences, and
    ui.theme from the theme cookie: the toggle and the Preferences form share
    one store, as a service's settings store would."""
    values = dict(SETTINGS_VALUES) | _preferences(request)
    if (mode := theme_context(request)["theme_mode"]) is not None:
        values["ui.theme"] = mode
    return values


def _settings_section(request: Request, section: str, *, errors=None, values=None) -> dict:
    """One section for gth-ui's settings_page.html / settings_section.html — the
    data a service (or greentechhub-fastapi's SettingsViews) passes. With an
    action and no form_attrs, the template wires the htmx post-and-swap itself."""
    title, description, settings = SETTINGS_DEMO[section]
    return {"id": section, "title": title, "description": description, "settings": settings,
            "values": values if values is not None else _saved_settings(request),
            "errors": errors, "action": f"/settings-demo/{section}"}


def _render_section(request: Request, section: dict, **kwargs) -> HTMLResponse:
    return templates.TemplateResponse(request, "settings_section.html", {"section": section},
                                      **kwargs)


def _visible_sections(request: Request) -> list[str]:
    """Preferences for everyone; App only with settings.manage — as
    greentechhub-fastapi's SettingsViews gates it on manage_permission."""
    return [s for s in SETTINGS_DEMO if s != "app" or _has(request, MANAGE_PERMISSION)]


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    title, subtitle = PAGES["settings"]
    return templates.TemplateResponse(request, "settings_page.html", {
        "page_title": title, "page_subtitle": subtitle,
        "settings_intro": (
            "gth_setting_field picks the widget from the setting's type: a switch for bool, "
            "segmented buttons for four or fewer choices, a select for more, number and text "
            "fields for int and str, and a write-only password field for a secret (the API "
            "token). Save a page size of 500 to see the 422 path."),
        "settings_sections": [_settings_section(request, s) for s in _visible_sections(request)],
    })


@app.post("/settings-demo/{section}", response_class=HTMLResponse)
async def settings_demo_save(request: Request, section: str):
    """The flow core's Settings facade expects: coerce every field, then 422 with
    the section re-rendered around its field errors, or save and toast."""
    if section not in SETTINGS_DEMO:
        return HTMLResponse("Unknown section", status_code=404)
    if section == "app" and (denied := _require_persona(request, MANAGE_PERMISSION)):
        return denied  # a POST, so a 403
    form = await request.form()
    _, _, settings = SETTINGS_DEMO[section]
    submitted, errors, cleared = {}, {}, []
    for setting in settings:
        raw = form.get(setting["key"])
        if setting.get("secret"):
            # Write-only, as greentechhub-fastapi's SettingsViews treats core's
            # secret settings: the Remove box clears it, a blank field keeps it,
            # and a new value is saved. The demo keeps only "set" (True), never
            # the text, so the field gets what core's SECRET_SET marker gives.
            if form.get(f"{setting['key']}.__clear") == "true":
                cleared.append(setting["key"])
            elif raw:
                submitted[setting["key"]] = True
            continue
        if raw is None:
            continue  # not on this form: keep the saved value (as SettingsViews does)
        try:
            submitted[setting["key"]] = _coerce_setting(setting, raw)
        except ValueError as exc:
            errors[setting["key"]] = [str(exc)]
            submitted[setting["key"]] = raw
    if errors:
        return _render_section(request, _settings_section(
            request, section, errors=errors, values=_saved_settings(request) | submitted),
            status_code=422)
    # ui.theme lives in the theme cookie (see _saved_settings); the gth:theme
    # event applies it without a reload, as a service's save response would.
    theme = submitted.pop("ui.theme", None)
    prefs = None
    if section == "preferences":
        prefs = {k: v for k, v in (_preferences(request) | submitted).items() if k not in cleared}
    else:
        SETTINGS_VALUES.update(submitted)
    events = {"gth:theme": theme} if theme else {}
    values = _saved_settings(request) | (prefs or {}) | ({"ui.theme": theme} if theme else {})
    for key in cleared:
        values.pop(key, None)
    response = _render_section(request, _settings_section(request, section, values=values),
                               headers={"HX-Trigger": greentechhub_ui.toast(
                                   f"{SETTINGS_DEMO[section][0]} saved", events=events)})
    if prefs is not None:
        response.set_cookie(PREFS_COOKIE, quote(json.dumps(prefs)), max_age=60 * 60 * 24 * 365,
                            samesite="lax")
    if theme:
        response.set_cookie(THEME_COOKIE, theme, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response


@app.post("/demo/theme")
async def demo_theme(theme: str = Form(...)):
    """theme-toggle.js POSTs theme=<light|dark> here (theme_save_url)."""
    if theme not in THEME_MODES:
        return Response(status_code=422)
    response = Response(status_code=204)
    response.set_cookie(THEME_COOKIE, theme, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response


@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    return _page(request, "overview", categories=PLAYGROUND_NAV)


@app.get("/layout", response_class=HTMLResponse)
async def layout_page(request: Request):
    return _page(request, "layout")


@app.get("/data", response_class=HTMLResponse)
async def data_page(request: Request):
    return _page(request, "data", tasks=TASKS, inline=0, **_paginate_widgets(0), **_widget_rows(1))


# gth_progress live demo: a fake sync that advances 25% per poll.
PROGRESS_DEMO = {"value": 0}


def _progress_live(request: Request, **kwargs) -> HTMLResponse:
    return templates.TemplateResponse(request, "_progress_live.html",
                                      {"sync_value": PROGRESS_DEMO["value"]}, **kwargs)


@app.post("/demo/progress/start", response_class=HTMLResponse)
async def progress_start(request: Request):
    """Restart the fake sync: the returned bar carries poll_url, so it polls."""
    PROGRESS_DEMO["value"] = 0
    return _progress_live(request)


@app.get("/demo/progress", response_class=HTMLResponse)
async def progress_poll(request: Request):
    """One poll: advance, and at 100% return the bar without poll_url (polling
    stops there) plus a toast."""
    PROGRESS_DEMO["value"] = min(PROGRESS_DEMO["value"] + 25, 100)
    if PROGRESS_DEMO["value"] < 100:
        return _progress_live(request)
    return _progress_live(request, headers={"HX-Trigger": greentechhub_ui.toast("Sync complete")})


@app.get("/demo/action-rows", response_class=HTMLResponse)
async def action_rows(request: Request, inline: str = "0"):
    """The gth_action_menu demo's rows at another `inline` (0, 2 or all)."""
    count = None if inline == "all" else (int(inline) if inline in ("0", "2") else 0)
    return templates.TemplateResponse(request, "_action_rows.html",
                                      {"tasks": TASKS, "inline": count})


def _task(task_id: int) -> dict | None:
    return next((t for t in TASKS if t["id"] == task_id), None)


@app.post("/demo/tasks/{task_id}/archive")
async def archive_task(task_id: int):
    """An action-menu item posting with hx-swap="none": the answer is a toast."""
    task = _task(task_id)
    if task is None:
        return Response(status_code=404)
    return hx_response(greentechhub_ui.toast(
        f"Archived \"{task['title']}\" (demo: nothing changed)."))


@app.delete("/demo/tasks/{task_id}")
async def delete_task(task_id: int):
    task = _task(task_id)
    if task is None:
        return Response(status_code=404)
    return hx_response(greentechhub_ui.toast(
        f"Deleted \"{task['title']}\" (demo: nothing changed).", "warning"))


@app.get("/forms", response_class=HTMLResponse)
async def forms_page(request: Request):
    return _page(request, "forms", field_errors={}, budget_value=250,
                 upload_accept=UPLOAD_ACCEPT, upload_max_size=UPLOAD_MAX_SIZE,
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


@app.get("/personas", response_class=HTMLResponse)
async def personas_page(request: Request, next: str | None = None, need: str | None = None):
    return _page(request, "personas", personas=PERSONAS, current=_persona(request),
                 next=_local_path(next), need=need)


@app.post("/demo/sign-in")
async def demo_sign_in(as_: str = Form(..., alias="as"), next: str | None = Form(None)):
    """Impersonate a persona (anonymous signs out), then go back to `next`."""
    if as_ not in PERSONAS:
        return Response(status_code=422)
    response = Response(status_code=303, headers={"Location": _local_path(next) or "/personas"})
    if PERSONAS[as_]["user"] is None:
        response.delete_cookie(USER_COOKIE)
    else:
        response.set_cookie(USER_COOKIE, as_, samesite="lax")
    return response


# ── Role assignments demo ─────────────────────────────────────────────────
# gth-ui's roles_page.html / roles_section.html over an in-memory dict standing
# in for greentechhub-core's GrantStore — the flow greentechhub-fastapi's
# RoleAdminViews runs. Admin only, like RoleAdminViews' permission gate.

ROLE_OPTIONS = [{"value": "viewer", "label": "Viewer"}, {"value": "editor", "label": "Editor"},
                {"value": "admin", "label": "Admin"}]
ROLE_GRANTS: dict[str, set[str]] = {}




def _roles_context(**extra) -> dict:
    return {"roles_url": "/roles", "roles_options": ROLE_OPTIONS,
            "roles_assignments": [{"subject": s, "roles": sorted(r)}
                                  for s, r in sorted(ROLE_GRANTS.items())], **extra}


def _roles_section(request: Request, message: str | None = None, **extra) -> HTMLResponse:
    headers = {"HX-Trigger": greentechhub_ui.toast(message)} if message else None
    status = 422 if "roles_form" in extra else 200
    return templates.TemplateResponse(request, "roles_section.html", _roles_context(**extra),
                                      status_code=status, headers=headers)


def _picked_roles(form) -> list[str]:
    known = {o["value"] for o in ROLE_OPTIONS}
    return [r for r in form.getlist("roles") if r in known]


# gth-ui's login_page.html with the context greentechhub-fastapi's LoginViews
# passes: nothing on GET, `error` (and a 401) after a failed sign-in.
LOGIN_DEMO = {
    "login_url": "/login-demo",
    "register_url": "/register-demo",
    "forgot_password_url": "/forgot-password-demo",
    "login_help": "Demo accounts: demo / demo, and newbie / newbie (email not confirmed yet).",
    "login_links": [{"label": "Playground", "url": "/"},
                    {"label": "Docs", "url": "https://github.com/GreenMachine582/greentechhub-ui"}],
}


@app.get("/login-demo", response_class=HTMLResponse)
async def login_demo(request: Request):
    return templates.TemplateResponse(request, "login_page.html", LOGIN_DEMO)


@app.post("/login-demo", response_class=HTMLResponse)
async def login_demo_submit(request: Request, user_id: str = Form(""), password: str = Form("")):
    if DEMO_PASSWORDS.get(user_id) == password:
        if user_id in DEMO_UNVERIFIED:
            # What LoginViews.refuse_sign_in does: a 403, no session, and the resend link.
            return templates.TemplateResponse(request, "login_page.html", {
                **LOGIN_DEMO, "user_id": user_id, "error": "Confirm your email address first.",
                "verify_resend_url": DEMO_VERIFICATION.resend_url,
            }, status_code=403)
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login_page.html", {
        **LOGIN_DEMO, "user_id": user_id, "error": "Incorrect user ID or password.",
    }, status_code=401)


# ── Password reset and email verification ────────────────────────────────────
# greentechhub-fastapi's real PasswordResetViews and EmailVerificationViews,
# rendering gth-ui's pages, over core's in-memory tokens. The emails land in
# core's InMemoryEmailSender, shown on /demo/outbox, so the links can be
# followed. No base_url: the links stay relative, which works on any port.
OUTBOX = InMemoryEmailSender()
register_email(app, None, sender=OUTBOX)
DEMO_EMAILS = {"demo": "demo@example.com", "newbie": "newbie@example.com"}
DEMO_PASSWORDS: dict[str, str] = {}
DEMO_UNVERIFIED: set[str] = set()


def _reset_accounts() -> None:
    DEMO_PASSWORDS.clear()
    DEMO_PASSWORDS.update({"demo": "demo", "newbie": "newbie"})
    DEMO_UNVERIFIED.clear()
    DEMO_UNVERIFIED.add("newbie")
    OUTBOX.clear()


_reset_accounts()


def _find(identifier: str, among) -> tuple[str, str] | None:
    for subject, address in DEMO_EMAILS.items():
        if identifier in (subject, address) and subject in among:
            return subject, address
    return None


OUTBOX_HELP = "Demo: the email lands in the outbox (/demo/outbox) instead of being sent."


class DemoPasswordReset(PasswordResetViews):
    forgot_url = "/forgot-password-demo"
    reset_url = "/reset-password-demo"
    login_url = "/login-demo"

    async def find_account(self, identifier: str) -> tuple[str, str] | None:
        return _find(identifier, DEMO_PASSWORDS)

    async def set_password(self, subject: str, password: str) -> None:
        DEMO_PASSWORDS[subject] = password


class DemoEmailVerification(EmailVerificationViews):
    verify_url = "/verify-email-demo"
    login_url = "/login-demo"

    async def mark_verified(self, subject: str) -> None:
        DEMO_UNVERIFIED.discard(subject)

    async def find_unverified(self, identifier: str) -> tuple[str, str] | None:
        return _find(identifier, DEMO_UNVERIFIED)


class _HelpTemplates:
    """Adds the outbox hint to the forgot and resend forms (an optional
    *_help key the pages take), around the playground's templates."""

    def __init__(self, inner: Jinja2Templates) -> None:
        self._inner = inner

    def TemplateResponse(self, request, name, context=None, **kwargs):  # noqa: N802
        extra = {"forgot_help": OUTBOX_HELP, "resend_help": OUTBOX_HELP}
        return self._inner.TemplateResponse(request, name, {**extra, **(context or {})}, **kwargs)


_tokens = OneTimeTokens(InMemoryTokenStore())
DEMO_RESET = DemoPasswordReset(templates=_HelpTemplates(templates), tokens=_tokens)
DEMO_VERIFICATION = DemoEmailVerification(templates=_HelpTemplates(templates), tokens=_tokens)
app.include_router(DEMO_RESET.router())
app.include_router(DEMO_VERIFICATION.router())


@app.get("/demo/outbox", response_class=HTMLResponse)
async def demo_outbox(request: Request):
    messages = [{"to": m.to, "subject": m.subject, "text": m.text,
                 "links": re.findall(r"(/(?:reset-password|verify-email)-demo/\S+)", m.text)}
                for m in reversed(OUTBOX.outbox)]
    return _page(request, "outbox", messages=messages)



# gth-ui's register_page.html with the context greentechhub-fastapi's
# RegisterViews passes: the same checks, 422 + errors on a refusal.
REGISTER_DEMO = {
    "register_url": "/register-demo",
    "login_url": "/login-demo",
    "min_password_length": 8,
    "register_help": "Nothing is stored: any new user ID signs straight in.",
    "register_links": [{"label": "Playground", "url": "/"}],
}


@app.get("/register-demo", response_class=HTMLResponse)
async def register_demo(request: Request):
    return templates.TemplateResponse(request, "register_page.html", REGISTER_DEMO)


@app.post("/register-demo", response_class=HTMLResponse)
async def register_demo_submit(request: Request, user_id: str = Form(""), password: str = Form(""),
                               password_confirm: str = Form("")):
    user_id = user_id.strip()
    errors: dict[str, list[str]] = {}
    if not user_id:
        errors["user_id"] = ["Choose a user ID."]
    elif user_id == "demo":
        errors["user_id"] = ["That user ID is taken."]
    if len(password) < REGISTER_DEMO["min_password_length"]:
        errors["password"] = [f"Use at least {REGISTER_DEMO['min_password_length']} characters."]
    elif password != password_confirm:
        errors["password_confirm"] = ["The passwords don't match."]
    if not errors:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "register_page.html", {
        **REGISTER_DEMO, "user_id": user_id, "errors": errors,
    }, status_code=422)


@app.get("/roles", response_class=HTMLResponse)
async def roles_page(request: Request):
    if denied := _require_persona(request, MANAGE_PERMISSION):
        return denied
    return templates.TemplateResponse(request, "roles_page.html", _roles_context(
        page_title="Roles", page_subtitle="gth-ui's roles_page.html over a stand-in GrantStore."))


@app.post("/roles", response_class=HTMLResponse)
async def roles_assign(request: Request):
    if denied := _require_persona(request, MANAGE_PERMISSION):
        return denied
    form = await request.form()
    subject, roles = (form.get("subject") or "").strip(), _picked_roles(form)
    errors = {}
    if not subject:
        errors["subject"] = ["Enter a user ID."]
    if not roles:
        errors["roles"] = ["Pick at least one role."]
    if errors:
        return _roles_section(request, roles_form={"subject": subject, "roles": roles,
                                                   "errors": errors})
    ROLE_GRANTS.setdefault(subject, set()).update(roles)
    return _roles_section(request, f"Roles assigned to {subject}")


@app.post("/roles/{subject}", response_class=HTMLResponse)
async def roles_set(request: Request, subject: str):
    if denied := _require_persona(request, MANAGE_PERMISSION):
        return denied
    roles = _picked_roles(await request.form())
    if roles:
        ROLE_GRANTS[subject] = set(roles)
    else:
        ROLE_GRANTS.pop(subject, None)
    return _roles_section(request, f"Roles saved for {subject}")


@app.delete("/roles/{subject}", response_class=HTMLResponse)
async def roles_remove(request: Request, subject: str):
    if denied := _require_persona(request, MANAGE_PERMISSION):
        return denied
    ROLE_GRANTS.pop(subject, None)
    return _roles_section(request, f"Removed {subject}'s roles")


@app.post("/demo/logout")
async def demo_logout():
    """The user menu's Log out (logout_url) — a POST, like greentechhub-fastapi's LoginViews."""
    response = Response(status_code=303, headers={"Location": "/personas"})
    response.delete_cookie(USER_COOKIE)
    return response


@app.get("/nav-badges/watchlist", response_class=HTMLResponse)
async def watchlist_badge():
    """Live nav badge: the watchlist size, re-fetched on watchlistChanged
    (nothing at zero hides it)."""
    count = len(WATCHLIST_DEMO)
    return HTMLResponse(_macro("badge.html", "gth_badge", count, "neutral") if count else "")


# ── Notification centre demo ──────────────────────────────────────────────────
# greentechhub-core's real InMemoryNotificationStore, with routes shaped like
# greentechhub-fastapi's NotificationViews (same templates, context and
# gth:notifications event), keyed by the impersonated persona.
NOTIFICATIONS = InMemoryNotificationStore()
NOTIFICATIONS_URL = "/notifications"


def _seed_notifications() -> None:
    global NOTIFICATIONS
    NOTIFICATIONS = InMemoryNotificationStore()  # a fresh store: the demo reset's job
    start = datetime.now(UTC) - timedelta(hours=6)
    for persona in ("viewer", "admin"):
        seeded = [
            new_notification(persona, "Your watchlist export is ready.", kind="success",
                             title="Export finished", action={"label": "Open", "url": "/data"},
                             now=start),
            new_notification(persona, "ASX sync couldn't reach the price feed; it retries hourly.",
                             kind="warning", title="Sync delayed", now=start + timedelta(hours=2)),
            new_notification(persona, "A new sign-in from Firefox on Windows.", kind="info",
                             now=start + timedelta(hours=5)),
        ]
        for n in seeded:
            NOTIFICATIONS.add_sync(n)
        NOTIFICATIONS.mark_read_sync(persona, [seeded[0].id], at=start + timedelta(hours=1))


_seed_notifications()


def _notification_dict(n) -> dict:
    return {"id": n.id, "message": n.message, "kind": n.kind, "title": n.title, "icon": n.icon,
            "action_label": n.action_label, "action_url": n.action_url, "category": n.category,
            "created_at": n.created_at, "read_at": n.read_at, "read": n.read,
            "read_url": f"{NOTIFICATIONS_URL}/{n.id}/read", "toast": n.to_toast()}


def _notifications_context(persona: str, limit: int, unread_only: bool = False) -> dict:
    items = NOTIFICATIONS.list_for_sync(persona, unread_only=unread_only, limit=limit)
    return {"page_title": "Notifications",
            "notifications": [_notification_dict(n) for n in items],
            "unread_count": NOTIFICATIONS.unread_count_sync(persona), "unread_only": unread_only,
            "page_url": NOTIFICATIONS_URL, "mark_all_url": f"{NOTIFICATIONS_URL}/read-all"}


@app.get(NOTIFICATIONS_URL, response_class=HTMLResponse)
async def notifications_page(request: Request, unread: str | None = None):
    persona = _persona(request)
    if PERSONAS[persona]["user"] is None:
        return Response(status_code=303, headers={"Location": "/personas?next=/notifications"})
    return templates.TemplateResponse(request, "notifications_page.html",
                                      _notifications_context(persona, 50, unread in ("1", "true")))


@app.get(f"{NOTIFICATIONS_URL}/panel", response_class=HTMLResponse)
async def notifications_panel(request: Request):
    return templates.TemplateResponse(request, "notifications_panel.html",
                                      _notifications_context(_persona(request), 10))


@app.get(f"{NOTIFICATIONS_URL}/badge", response_class=HTMLResponse)
async def notifications_badge(request: Request):
    persona = _persona(request)
    if PERSONAS[persona]["user"] is None:
        return Response(status_code=204)
    return templates.TemplateResponse(request, "notification_badge.html",
                                      {"count": NOTIFICATIONS.unread_count_sync(persona)})


async def _marked(request: Request) -> Response:
    form = await request.form()
    if next_url := _local_path(str(form.get("next") or "") or None):
        return Response(status_code=303, headers={"Location": next_url})
    unread = NOTIFICATIONS.unread_count_sync(_persona(request))
    return Response(status_code=204,
                    headers={"HX-Trigger": json.dumps({"gth:notifications": {"unread": unread}})})


@app.post(f"{NOTIFICATIONS_URL}/read-all")
async def notifications_read_all(request: Request):
    NOTIFICATIONS.mark_all_read_sync(_persona(request), at=datetime.now(UTC))
    return await _marked(request)


@app.post(NOTIFICATIONS_URL + "/{notification_id}/read")
async def notifications_read_one(request: Request, notification_id: str):
    NOTIFICATIONS.mark_read_sync(_persona(request), [notification_id], at=datetime.now(UTC))
    return await _marked(request)


@app.post("/demo/reset")
async def demo_reset():
    """Restore the demos that keep server-side state (the watchlist, the
    health count, the site banner, the notifications) and refresh everything
    showing them."""
    _seed_notifications()
    _reset_accounts()
    SETTINGS_VALUES.pop(SITE_BANNER_KEY, None)
    SETTINGS_VALUES.pop(SITE_BANNER_TONE_KEY, None)
    WATCHLIST_DEMO[:] = [dict(item) for item in _WATCHLIST_INITIAL]
    HEALTH_ISSUES["open"] = HEALTH_ISSUES_INITIAL
    PROGRESS_DEMO["value"] = 0
    del RECORDS[_RECORDS_INITIAL:]
    for r, stock in zip(RECORDS, _RECORDS_STOCK, strict=True):
        r["stock"] = stock
    return hx_response(greentechhub_ui.toast(
        "Demo data reset.", "info",
        events=["watchlistChanged", "healthChanged", "watchlistReset", "recordsChanged",
                "gth:notifications"]))


@app.post("/demo/records")
async def add_record():
    """A "save" elsewhere on the page: the records table re-queries itself
    (gth_data_table refresh_event="recordsChanged"), keeping its sort/filters."""
    n = len(RECORDS) - _RECORDS_INITIAL + 1
    RECORDS.append({"id": len(RECORDS) + 1, "name": f"Added sensor {n}", "category": "Sensor",
                    "stock": 1, "price": 9.99, "added": date.today()})
    return hx_response(greentechhub_ui.toast(f"Added sensor {n}", events=["recordsChanged"]))


async def _bulk_records(request: Request) -> list[dict]:
    """The records a gth_data_table bulk action posted (repeated `ids`)."""
    form = await request.form()
    ids = {int(i) for i in form.getlist("ids") if str(i).isdigit()}
    return [r for r in RECORDS if r["id"] in ids]


def _records_word(n: int) -> str:
    return f"{n} record" if n == 1 else f"{n} records"


@app.post("/demo/records/restock")
async def restock_records(request: Request):
    rows = await _bulk_records(request)
    for r in rows:
        r["stock"] += 50
    return hx_response(greentechhub_ui.toast(f"Restocked {_records_word(len(rows))}.",
                                             events=["recordsChanged"]))


@app.post("/demo/records/sold-out")
async def sold_out_records(request: Request):
    rows = await _bulk_records(request)
    for r in rows:
        r["stock"] = 0
    return hx_response(greentechhub_ui.toast(f"Marked {_records_word(len(rows))} sold out.",
                                             "warning", events=["recordsChanged"]))


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


NOTES_MAX = 140


@app.post("/form-demo", response_class=HTMLResponse)
async def form_demo(request: Request, budget: float = Form(...), notes: str = Form("")):
    field_errors = {}
    if errors := _validate_budget(budget):
        field_errors["budget"] = errors
    # maxlength stops the browser; the server still has to check.
    if len(notes) > NOTES_MAX:
        field_errors["notes"] = [f"Keep notes to {NOTES_MAX} characters."]
    context = {"field_errors": field_errors, "budget_value": budget, "notes_value": notes}
    if field_errors:
        return templates.TemplateResponse(request, "_form_demo.html", context, status_code=422)
    resp = templates.TemplateResponse(request, "_form_demo.html", context)
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
    return hx_response(greentechhub_ui.toast(**options))


@app.get("/demo/error/{status}")
async def error_demo(status: int, own_toast: bool = False):
    """Failed requests for toast.js's automatic error toasts: a 404 with a
    FastAPI-style JSON detail, any other status bare, or (own_toast) a 500
    that sends its own toast — which the generic one then stands down for."""
    if own_toast:
        own = greentechhub_ui.toast("The report service is down — try again in a minute.", "danger",
                                    title="Reports unavailable")
        return hx_response(own, status_code=500)
    if status == 404:
        return JSONResponse({"detail": "Widget #42 not found"}, status_code=404)
    return HTMLResponse(f"Error {status}", status_code=status if 400 <= status < 600 else 500)


@app.get("/modal-demo/content", response_class=HTMLResponse)
async def modal_demo_content():
    return HTMLResponse("<p>Loaded via HTMX, right as the modal opened.</p>")


@app.delete("/watchlist-demo/{item_id}", response_class=HTMLResponse)
async def watchlist_demo_delete(request: Request, item_id: int):
    WATCHLIST_DEMO[:] = [item for item in WATCHLIST_DEMO if item["id"] != item_id]
    resp = templates.TemplateResponse(
        request, "_watchlist_list.html", {"watchlist": WATCHLIST_DEMO}
    )
    resp.headers["HX-Trigger"] = trigger("watchlistChanged")  # refreshes the sidebar badge
    return resp


@app.get("/demo/watchlist", response_class=HTMLResponse)
async def watchlist_list(request: Request):
    """The watchlist fragment, re-fetched after a reset (watchlistReset)."""
    return templates.TemplateResponse(request, "_watchlist_list.html",
                                      {"watchlist": WATCHLIST_DEMO})


def _records_state(query, *, mode: str, scroll: bool, base_url: str,
                   table_id: str = "records", user_settings=None) -> greentechhub_ui.TableState:
    return greentechhub_ui.TableState.from_query(
        query,
        id=table_id,
        base_url=base_url,
        mode=mode,
        page_size=10,
        page_sizes=(10, 25, 50),
        sortable=("name", "category", "stock", "price", "added"),
        default_sort="name",
        filter_params=("q", "category", "stock", "date_from", "date_to"),
        push_url=mode == "pages" and table_id == "records",
        max_height="22rem" if scroll else None,
        export_base_url="/tables/export.csv" if table_id == "records" else None,
        user_settings=user_settings,  # Preferences' "Rows per page", once saved
    )


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _query_records(state: greentechhub_ui.TableState):
    """What a consumer's repository does with a TableState: filter, sort,
    then slice (or not, for mode="none")."""
    rows = RECORDS
    if q := state.filters.get("q", "").lower():
        rows = [r for r in rows if q in r["name"].lower()]
    if category := state.filters.get("category"):
        rows = [r for r in rows if r["category"] == category]
    if (stock := state.filters.get("stock")) in ("in", "out"):
        rows = [r for r in rows if (r["stock"] > 0) == (stock == "in")]
    if date_from := _parse_date(state.filters.get("date_from")):
        rows = [r for r in rows if r["added"] >= date_from]
    if date_to := _parse_date(state.filters.get("date_to")):
        rows = [r for r in rows if r["added"] <= date_to]
    if state.sort:
        rows = sorted(rows, key=lambda r: (r[state.sort], r["id"]),
                      reverse=state.direction == "desc")
    total = len(rows)
    if state.mode != "none":
        rows = rows[state.offset: state.offset + state.limit]
    return rows, state.with_result(total=total)


@app.get("/tables/export.csv")
async def tables_export(request: Request):
    """TableState.export_url's endpoint: the same state as the table (so the
    same allow-listed filters and sort), every matching row, no paging."""
    state = _records_state(request.query_params, user_settings=_preferences(request),
                           mode="none", scroll=False, base_url="/tables")
    rows, _ = _query_records(state)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["ID", "Name", "Category", "Stock", "Price", "Added"])
    for r in rows:
        writer.writerow([r["id"], r["name"], r["category"], r["stock"], f"{r['price']:.2f}",
                         r["added"].isoformat()])
    return Response(out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="records.csv"'})


@app.get("/tables", response_class=HTMLResponse)
async def tables(request: Request, mode: str = "pages", scroll: int = 0):
    if mode not in greentechhub_ui.table.MODES:
        mode = "pages"
    # pick_for: set when a record picker's "Open full page" opened this tab;
    # kept in base_url so the table's own sort/filter/pager swaps keep it.
    pick_for = request.query_params.get("pick_for", "")
    fixed = {"mode": mode, **({"scroll": 1} if scroll else {}),
             **({"pick_for": pick_for} if pick_for else {})}
    state = _records_state(request.query_params, user_settings=_preferences(request),
                           mode=mode, scroll=bool(scroll),
                           base_url="/tables?" + urlencode(fixed))
    rows, state = _query_records(state)
    context = {"table": state, "records": rows, "scroll": bool(scroll),
               "category_options": CATEGORY_OPTIONS, "pick_for": pick_for}
    if wants_fragment(request.headers):
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
HEALTH_ISSUES_INITIAL = 3
HEALTH_ISSUES = {"open": HEALTH_ISSUES_INITIAL}


@app.get("/layouts/sidebar-badges/health", response_class=HTMLResponse)
async def health_badge():
    count = HEALTH_ISSUES["open"]
    return HTMLResponse(_macro("badge.html", "gth_badge", count, "warn") if count else "")


@app.post("/layouts/sidebar-badges/health/{action}")
async def health_badge_action(action: str):
    if action == "resolve":
        HEALTH_ISSUES["open"] = max(0, HEALTH_ISSUES["open"] - 1)
    elif action == "reset":
        HEALTH_ISSUES["open"] = 3
    else:
        return HTMLResponse("Unknown action", status_code=404)
    return hx_response(greentechhub_ui.toast(
        f"{HEALTH_ISSUES['open']} open issue(s)", kind="info", events=["healthChanged"]
    ))


@app.get("/layouts/sidebar", response_class=HTMLResponse)
@app.get("/layouts/sidebar/{rest:path}", response_class=HTMLResponse)
async def sidebar_demo(request: Request, rest: str = ""):
    return templates.TemplateResponse(request, "sidebar_demo.html", {
        "layout": "sidebar",
        "nav_items": SIDEBAR_DEMO_NAV,
        "nav_breadcrumbs": partial(greentechhub_ui.navigation.breadcrumbs_for, SIDEBAR_DEMO_NAV),
        "command_search_url": "/layouts/sidebar-search",
    })


@app.get("/layouts/sidebar-search", response_class=HTMLResponse)
async def sidebar_search(q: str = ""):
    """gth_command_palette search_url demo: parts matching q."""
    q = q.strip().lower()
    rows = [r for r in RECORDS if q and q in r["name"].lower()][:8]
    return HTMLResponse(Markup("").join(
        _macro("command_palette.html", "gth_command_item", r["name"],
               f"/layouts/sidebar/parts?id={r['id']}", "cpu",
               f"{r['category']} · ${r['price']:.2f}")
        for r in rows
    ))


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
    return HTMLResponse(_macro("tree.html", "gth_tree_nodes", nodes, level, tree, select,
                               f"/tree/nodes?tree={tree}"))


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


@app.get("/demo/widget-rows", response_class=HTMLResponse)
async def demo_widget_rows(request: Request, page: int = 1):
    return templates.TemplateResponse(request, "_widget_rows.html", _widget_rows(page))


@app.get("/demo/widgets", response_class=HTMLResponse)
async def demo_widget_options(request: Request, q: str = ""):
    widgets = [(i, w) for i, w in enumerate(WIDGETS, start=1) if q.strip().lower() in w.lower()]
    return templates.TemplateResponse(request, "_widget_options.html", {"widgets": widgets[:10]})


def _modal_context(widget: str = "", size: str = "S", errors: dict | None = None,
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


@app.get("/demo/modal", response_class=HTMLResponse)
async def demo_modal(request: Request):
    return templates.TemplateResponse(request, "_modal.html", _modal_context())


@app.post("/demo/modal", response_class=HTMLResponse)
async def demo_modal_submit(request: Request, widget: str = Form(""), size: str = Form("S"),
                           widget_search: str = Form(""), record: str = Form(""),
                           record_label: str = Form("")):
    if not widget.isdigit():
        context = _modal_context(widget, size, {"widget": ["Pick a widget from the list."]},
                                     widget_search, record, record_label)
        # Re-render just the form (hx-target="this"); the modal stays open.
        return templates.TemplateResponse(request, "_modal_form.html", context, status_code=422)
    part = _record(record)
    return hx_response(greentechhub_ui.toast(
        f"Saved {WIDGETS[int(widget) - 1]} ({size})" + (f" for {part['name']}" if part else ""),
        events=["closeModal"],
    ))


@app.get("/demo/record-picker", response_class=HTMLResponse)
async def demo_record_picker(request: Request):
    """A gth_record_picker panel body: filter + data table of RECORDS. One
    endpoint serves two pickers, so ?for= keeps their table ids apart."""
    picker = request.query_params.get("for")
    picker = picker if picker in ("modal", "page") else "page"
    state = _records_state(request.query_params, user_settings=_preferences(request),
                           mode="pages", scroll=False,
                           base_url="/demo/record-picker?" + urlencode({"for": picker}),
                           table_id=f"picker-{picker}")
    rows, state = _query_records(state)
    # The first load fills the panel (filter + table); the table's own
    # sort/filter/pager swaps target the table and must get just the table.
    with_filter = not state.is_own_swap(request.headers)
    return templates.TemplateResponse(request, "_record_picker_panel.html",
                                      {"table": state, "records": rows, "with_filter": with_filter})


@app.post("/demo/record-pick", response_class=HTMLResponse)
async def demo_record_pick(part: str = Form(""), part_label: str = Form("")):
    record = _record(part)
    if record is None:
        return HTMLResponse("Nothing picked.")
    return HTMLResponse(f"part={record['id']} ({record['name']})")


@app.get("/demo/tab/{key}", response_class=HTMLResponse)
async def demo_tab(key: str):
    if key not in ("activity", "settings"):
        return HTMLResponse("Unknown tab", status_code=404)
    await asyncio.sleep(0.3)  # long enough to see the skeleton
    return HTMLResponse(f'<p class="mb-0" data-tab-loaded="{key}">Loaded the '
                        f"<strong>{key}</strong> pane from the server.</p>")


@app.post("/demo/date-range", response_class=HTMLResponse)
async def demo_date_range(date_from: str = Form(""), date_to: str = Form("")):
    return HTMLResponse(f"date_from={date_from or '(open)'}, date_to={date_to or '(open)'}")


@app.post("/demo/chips", response_class=HTMLResponse)
async def demo_chips(request: Request):
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


@app.post("/demo/multi", response_class=HTMLResponse)
async def demo_multi(request: Request):
    form = await request.form()
    widgets, tags = form.getlist("widgets"), form.getlist("tags")
    if not widgets:
        context = _multi_context(widgets, tags, {"widgets": ["Pick at least one widget."]})
        return templates.TemplateResponse(request, "_multi_form.html", context, status_code=422)
    context = _multi_context(widgets, tags)
    context["saved"] = f"widgets={','.join(widgets)} tags={','.join(tags) or '-'}"
    return templates.TemplateResponse(request, "_multi_form.html", context)


UPLOAD_ACCEPT = (".csv", ".xlsx")
UPLOAD_MAX_SIZE = 1024 * 1024
UPLOAD_DELAY = 1.0  # seconds; long enough to see the "Processing…" bar


def _upload_context(errors=(), uploaded=None) -> dict:
    return {"accept": UPLOAD_ACCEPT, "max_size": UPLOAD_MAX_SIZE, "errors": list(errors),
            "uploaded": uploaded}


@app.post("/demo/upload", response_class=HTMLResponse)
async def demo_upload(request: Request):
    """gth_file_drop's server side: re-check what the browser already checked.
    Read the form directly: with nothing chosen the browser still sends an
    empty part, which Starlette parses as a str, and list[UploadFile] = File()
    would answer with FastAPI's JSON 422 instead of the form."""
    await asyncio.sleep(UPLOAD_DELAY)
    form = await request.form()
    files = [f for f in form.getlist("files") if isinstance(f, UploadFile) and f.filename]
    errors, done = [], []
    for f in files:
        size = len(await f.read())
        if not f.filename.lower().endswith(UPLOAD_ACCEPT):
            errors.append(f"{f.filename} — not an accepted file type")
        elif size > UPLOAD_MAX_SIZE:
            errors.append(f"{f.filename} — larger than 1 MB")
        else:
            done.append(f"{f.filename} ({size} B)")
    if not files:
        errors.append("Choose at least one file.")
    if errors:
        return templates.TemplateResponse(request, "_upload_form.html", _upload_context(errors),
                                          status_code=422)
    return templates.TemplateResponse(request, "_upload_form.html",
                                      _upload_context(uploaded=", ".join(done)))


@app.post("/demo/slow-job")
async def demo_slow_job():
    await asyncio.sleep(2)
    return hx_response(greentechhub_ui.toast("Slow job finished"))


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8500)))
