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


def test_build_nav_items_no_op_scope_filtering_with_a_current_user():
    # Matches filter_by_scope's current documented behavior: a populated
    # current_user doesn't yet perform a real scope check (no
    # greentechhub-core permission system exists) — not something this
    # task changes, just confirming build_nav_items doesn't alter it.
    custom = [{"label": "Admin", "url": "/admin", "required_scope": "admin"}]
    result = build_nav_items(custom_items=custom, current_user={"id": 1})
    assert result == custom


def test_filter_by_scope_still_works_standalone():
    items = [
        {"label": "Deals", "url": "/"},
        {"label": "Admin", "url": "/admin", "required_scope": "admin"},
    ]
    assert filter_by_scope(items, None) == [{"label": "Deals", "url": "/"}]


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
