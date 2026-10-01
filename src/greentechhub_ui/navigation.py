from collections.abc import Set as AbstractSet
from typing import NotRequired, TypedDict


class NavBadge(TypedDict):
    label: str
    tone: NotRequired[str]  # gth_badge tone: good|bad|warn|info|neutral|brand


class NavItem(TypedDict):
    label: str
    url: NotRequired[str]  # optional for a group (an item with children)
    icon: NotRequired[str | None]
    # A permission string (e.g. "settings.manage") the viewer needs to see the
    # item; required_scope is the older name and still works.
    required_permission: NotRequired[str | None]
    required_scope: NotRequired[str | None]
    # v0.8 — all optional, so flat v0.4-style lists keep working unchanged.
    children: NotRequired[list["NavItem"]]  # a group (gth_sidebar / navbar dropdown)
    badge: NotRequired[NavBadge]  # static count/status
    badge_url: NotRequired[str]  # live badge: endpoint returning a gth_badge (or nothing)
    badge_event: NotRequired[str]  # HX-Trigger event that re-fetches badge_url
    match: NotRequired[str]  # "prefix" (default) or "exact" active-path matching


# Built-in nav items shared by every consumer. Empty today — no universal
# cross-service nav link exists yet (account links live in the navbar's user
# menu, `user_menu_items`, instead). A future addition here becomes visible to
# every consumer through build_nav_items() without any of them needing to
# change their own code.
DEFAULT_NAV_ITEMS: list[NavItem] = []


def _required_permission(item: NavItem) -> str | None:
    return item.get("required_permission") or item.get("required_scope")


def filter_by_scope(
    nav_items: list[NavItem],
    current_user: object | None,
    granted: AbstractSet[str] | None = None,
) -> list[NavItem]:
    """Permission-filter nav items for the viewer, recursing into groups; a
    group left with no children (and no url of its own) is dropped.

    An item with `required_permission` (or its older name `required_scope`):
      - is hidden from anonymous viewers (`current_user is None`);
      - is shown to any signed-in viewer when `granted is None` — a service
        that hasn't opted into permissions keeps the old behaviour;
      - otherwise is shown only when its permission is in `granted`, the
        viewer's permission strings (e.g. greentechhub-core's
        `RoleResolver.granted()`, which greentechhub-fastapi's
        register_settings supplies as the `granted` context value).

    `current_user` is only ever compared to None, so it can be core's
    Identity, a dict, or anything else.
    """
    result = []
    for item in nav_items:
        needed = _required_permission(item)
        if needed and (current_user is None or (granted is not None and needed not in granted)):
            continue
        if "children" in item:
            children = filter_by_scope(item["children"], current_user, granted)
            if not children and not item.get("url"):
                continue
            item = {**item, "children": children}
        result.append(item)
    return result


_UNSET = object()


def build_nav_items(
    custom_items: list[NavItem],
    current_user: object | None = _UNSET,
    built_in_items: list[NavItem] | None = None,
    granted: AbstractSet[str] | None = None,
) -> list[NavItem]:
    """Combine built-in + consumer-registered nav items, then scope-filter —
    the "built-in + consumer-registered, scope-filtered" merge docs/components.md's
    gth-navbar/gth-sidebar description already promises.

    `built_in_items` defaults to DEFAULT_NAV_ITEMS (currently empty), so this
    reduces to "custom_items, scope-filtered" until a real built-in item exists.

    Without `current_user` (the usual call, once at startup, for install()'s
    global nav_items) nothing is filtered: app.html filters per request
    through the `nav_visible` global, with that request's `current_user` and
    `granted`, so a permissioned item reaches the viewers allowed to see it.
    Pass `current_user` (even None) to filter here instead, for a list built
    per request.
    """
    items = [*(built_in_items if built_in_items is not None else DEFAULT_NAV_ITEMS), *custom_items]
    if current_user is _UNSET:
        return items
    return filter_by_scope(items, current_user, granted)


# ── Active-path helpers (v0.8) ────────────────────────────────────────────


def _url_path(url: str) -> str:
    """The path part of a nav url: an in-page anchor (/forms#combobox) or a
    query string doesn't make it a different page."""
    return url.split("#", 1)[0].split("?", 1)[0] or "/"


def _match_score(item: NavItem, path: str) -> int:
    """How well `item` matches `path`: -1 no match; higher is better. An
    exact match beats any prefix match; a longer prefix beats a shorter one.
    "/" (and match="exact" items) only ever match exactly."""
    url = item.get("url")
    if not url:
        return -1
    target = _url_path(url)
    if path == target:
        return 10_000 + len(target)
    if item.get("match") == "exact" or target == "/":
        return -1
    if path.startswith(target.rstrip("/") + "/"):
        return len(target)
    return -1


def nav_trail(nav_items: list[NavItem], current_path: str | None) -> list[NavItem]:
    """The ancestors-to-item chain of the item best matching current_path
    ([] when nothing matches). Among equal matches the first one wins, and
    an anchor child (/forms#x) never beats its page (/forms) — children
    that only differ by anchor score the same, and the parent comes first."""
    if not current_path:
        return []
    best: tuple[int, list[NavItem]] = (-1, [])

    def walk(items: list[NavItem], ancestors: list[NavItem]):
        nonlocal best
        for item in items:
            score = _match_score(item, current_path)
            if score > best[0]:
                best = (score, [*ancestors, item])
            if item.get("children"):
                walk(item["children"], [*ancestors, item])

    walk(nav_items, [])
    return best[1]


def mark_active(nav_items: list[NavItem], current_path: str | None) -> list[dict]:
    """Copies of nav_items with `active` (the best-matching item) and
    `expanded` (its ancestor groups) flags — what gth_sidebar renders."""
    trail = nav_trail(nav_items, current_path)
    active = trail[-1] if trail else None
    ancestors = trail[:-1]

    def mark(items):
        out = []
        for item in items:
            copy = {**item, "active": item is active,
                    "expanded": any(item is a for a in ancestors)}
            if item.get("children"):
                copy["children"] = mark(item["children"])
            out.append(copy)
        return out

    return mark(nav_items)


def breadcrumbs_for(nav_items: list[NavItem], current_path: str | None) -> list[dict]:
    """gth_page_header breadcrumbs for current_path, derived from the nav
    tree: every ancestor with a url is a link, the matched item is the
    current (last, url-less) entry. [] when nothing matches."""
    trail = nav_trail(nav_items, current_path)
    crumbs = [{"label": item["label"], "url": item["url"]}
              for item in trail[:-1] if item.get("url")]
    if trail:
        crumbs.append({"label": trail[-1]["label"]})
    return crumbs


def flatten(nav_items: list[NavItem], _prefix: tuple[str, ...] = ()) -> list[dict]:
    """Every navigable item as {label, path, url, icon} — path is the
    "Data › Tables" group chain, for gth_command_palette."""
    out = []
    for item in nav_items:
        chain = (*_prefix, item["label"])
        if item.get("url"):
            out.append({"label": item["label"], "path": " › ".join(chain),
                        "url": item["url"], "icon": item.get("icon")})
        if item.get("children"):
            out.extend(flatten(item["children"], chain))
    return out
