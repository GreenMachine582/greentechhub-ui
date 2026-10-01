from greentechhub_ui.navigation import build_nav_items, filter_by_scope


def test_build_nav_items_with_custom_items_only():
    custom = [{"label": "Deals", "url": "/"}]
    assert build_nav_items(custom_items=custom) == custom


def test_build_nav_items_combines_built_in_and_custom_with_built_in_first():
    built_in = [{"label": "Docs", "url": "/docs"}]
    custom = [{"label": "Deals", "url": "/"}]
    result = build_nav_items(custom_items=custom, built_in_items=built_in)
    assert result == [*built_in, *custom]


def test_build_nav_items_scope_filters_when_no_current_user():
    custom = [
        {"label": "Deals", "url": "/"},
        {"label": "Admin", "url": "/admin", "required_scope": "admin"},
    ]
    result = build_nav_items(custom_items=custom, current_user=None)
    assert result == [{"label": "Deals", "url": "/"}]


def test_build_nav_items_signed_in_without_granted_keeps_permissioned_items():
    # A service that hasn't opted into permissions (no `granted`) shows a
    # permissioned item to any signed-in viewer, as before.
    custom = [{"label": "Admin", "url": "/admin", "required_scope": "admin"}]
    result = build_nav_items(custom_items=custom, current_user={"id": 1})
    assert result == custom


def test_filter_by_scope_still_works_standalone():
    items = [
        {"label": "Deals", "url": "/"},
        {"label": "Admin", "url": "/admin", "required_scope": "admin"},
    ]
    assert filter_by_scope(items, None) == [{"label": "Deals", "url": "/"}]


def test_build_nav_items_without_a_viewer_leaves_filtering_to_the_page():
    # The startup call for install()'s global nav_items: app.html filters per request.
    custom = [{"label": "Admin", "url": "/admin", "required_permission": "settings.manage"}]
    assert build_nav_items(custom_items=custom) == custom


# ── v0.12: permissions (required_permission + granted) ────────────────────

ADMIN = {"label": "Admin", "url": "/admin", "required_permission": "settings.manage"}
HOME = {"label": "Home", "url": "/"}


def test_granted_permission_shows_the_item():
    assert filter_by_scope([HOME, ADMIN], {"id": 1}, {"settings.manage"}) == [HOME, ADMIN]


def test_missing_permission_hides_the_item():
    assert filter_by_scope([HOME, ADMIN], {"id": 1}, {"reports.view"}) == [HOME]
    assert filter_by_scope([HOME, ADMIN], {"id": 1}, frozenset()) == [HOME]


def test_anonymous_never_sees_a_permissioned_item_even_with_granted():
    assert filter_by_scope([HOME, ADMIN], None, {"settings.manage"}) == [HOME]


def test_granted_none_keeps_the_old_signed_in_behaviour():
    assert filter_by_scope([HOME, ADMIN], {"id": 1}, None) == [HOME, ADMIN]


def test_required_scope_is_an_alias_and_required_permission_wins():
    legacy = {"label": "Ops", "url": "/ops", "required_scope": "ops.view"}
    both = {"label": "Both", "url": "/b", "required_scope": "ops.view",
            "required_permission": "settings.manage"}
    assert filter_by_scope([legacy], {"id": 1}, {"ops.view"}) == [legacy]
    assert filter_by_scope([legacy], {"id": 1}, set()) == []
    assert filter_by_scope([both], {"id": 1}, {"ops.view"}) == []
    assert filter_by_scope([both], {"id": 1}, {"settings.manage"}) == [both]


def test_a_group_emptied_by_permissions_is_dropped():
    group = {"label": "Settings", "children": [ADMIN]}
    with_url = {"label": "Settings", "url": "/settings", "children": [ADMIN]}
    assert filter_by_scope([HOME, group], {"id": 1}, set()) == [HOME]
    assert filter_by_scope([with_url], {"id": 1}, set()) == [{**with_url, "children": []}]


def test_current_user_can_be_any_object():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Identity:
        subject: str
        username: str

    viewer = Identity(subject="u1", username="alice")
    assert filter_by_scope([ADMIN], viewer, {"settings.manage"}) == [ADMIN]


# ── v0.8: nested items, active trail, breadcrumbs, flatten ────────────────

from greentechhub_ui.navigation import (  # noqa: E402
    breadcrumbs_for,
    flatten,
    mark_active,
    nav_trail,
)

TREE = [
    {"label": "Home", "url": "/"},
    {"label": "Data", "children": [
        {"label": "Tables", "url": "/tables"},
        {"label": "Tree", "url": "/tree"},
    ]},
    {"label": "Forms", "url": "/forms", "children": [
        {"label": "Combobox", "url": "/forms#combobox"},
        {"label": "Admin", "url": "/forms/admin", "required_scope": "admin"},
    ]},
    {"label": "Exact", "url": "/exact", "match": "exact"},
]


def _labels(items):
    return [i["label"] for i in items]


def test_trail_exact_and_nested():
    assert _labels(nav_trail(TREE, "/tables")) == ["Data", "Tables"]
    assert _labels(nav_trail(TREE, "/")) == ["Home"]


def test_trail_prefix_and_deepest_wins():
    assert _labels(nav_trail(TREE, "/tables/7")) == ["Data", "Tables"]
    assert _labels(nav_trail(TREE, "/forms/admin/users")) == ["Forms", "Admin"]
    assert _labels(nav_trail(TREE, "/forms/other")) == ["Forms"]


def test_trail_root_and_exact_items_only_match_exactly():
    assert nav_trail(TREE, "/nothing") == []
    assert nav_trail(TREE, "/exact/sub") == []
    assert nav_trail(TREE, None) == []


def test_anchor_child_never_beats_its_page():
    assert _labels(nav_trail(TREE, "/forms")) == ["Forms"]


def test_mark_active_flags_item_and_expands_ancestors():
    marked = mark_active(TREE, "/tree")
    data = marked[1]
    assert data["expanded"] and not data["active"]
    assert [c["active"] for c in data["children"]] == [False, True]
    assert not marked[2]["expanded"]
    assert "active" not in TREE[1]  # originals untouched


def test_breadcrumbs():
    assert breadcrumbs_for(TREE, "/forms/admin") == [
        {"label": "Forms", "url": "/forms"}, {"label": "Admin"}]
    # A url-less group is skipped as a link.
    assert breadcrumbs_for(TREE, "/tables") == [{"label": "Tables"}]
    assert breadcrumbs_for(TREE, "/nope") == []


def test_flatten_paths():
    flat = flatten(TREE)
    assert {"label": "Tables", "path": "Data › Tables", "url": "/tables", "icon": None} in flat
    assert [f["label"] for f in flat] == ["Home", "Tables", "Tree", "Forms", "Combobox", "Admin",
                                          "Exact"]


def test_scope_filter_recurses_and_drops_empty_groups():
    items = [
        {"label": "Ops", "children": [{"label": "Admin", "url": "/a", "required_scope": "admin"}]},
        *TREE,
    ]
    filtered = filter_by_scope(items, None)
    assert "Ops" not in _labels(filtered)  # group emptied → dropped
    forms = next(i for i in filtered if i["label"] == "Forms")
    assert _labels(forms["children"]) == ["Combobox"]
