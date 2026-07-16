from typing import NotRequired, TypedDict


class NavItem(TypedDict):
    label: str
    url: str
    icon: NotRequired[str | None]
    required_scope: NotRequired[str | None]


def filter_by_scope(nav_items: list[NavItem], current_user: dict | None) -> list[NavItem]:
    """Scope-filter nav items against the current user.

    No-op today: neither BottleBot nor greentechhub-core's permission system
    supplies a real `current_user`/scope check yet. Once one does, this is
    where `required_scope` gets checked against it (see docs/extensibility.md).
    """
    if current_user is None:
        return [item for item in nav_items if not item.get("required_scope")]
    return nav_items
