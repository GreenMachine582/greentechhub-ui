from typing import NotRequired, TypedDict


class NavItem(TypedDict):
    label: str
    url: str
    icon: NotRequired[str | None]
    required_scope: NotRequired[str | None]


# Built-in nav items shared by every consumer. Empty today — no universal
# cross-service nav concept exists yet (no greentechhub-core auth, no shared
# "Account"/"Docs"-style link). A future addition here becomes visible to
# every consumer through build_nav_items() without any of them needing to
# change their own code.
DEFAULT_NAV_ITEMS: list[NavItem] = []


def filter_by_scope(nav_items: list[NavItem], current_user: dict | None) -> list[NavItem]:
    """Scope-filter nav items against the current user.

    No-op today: neither BottleBot nor greentechhub-core's permission system
    supplies a real `current_user`/scope check yet. Once one does, this is
    where `required_scope` gets checked against it (see docs/extensibility.md).
    """
    if current_user is None:
        return [item for item in nav_items if not item.get("required_scope")]
    return nav_items


def build_nav_items(
    custom_items: list[NavItem],
    current_user: dict | None = None,
    built_in_items: list[NavItem] | None = None,
) -> list[NavItem]:
    """Combine built-in + consumer-registered nav items, then scope-filter —
    the "built-in + consumer-registered, scope-filtered" merge docs/components.md's
    gth-navbar/gth-sidebar description already promises.

    `built_in_items` defaults to DEFAULT_NAV_ITEMS (currently empty), so this
    reduces to "custom_items, scope-filtered" until a real built-in item exists.
    """
    items = [*(built_in_items if built_in_items is not None else DEFAULT_NAV_ITEMS), *custom_items]
    return filter_by_scope(items, current_user)
