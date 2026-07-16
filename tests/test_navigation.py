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
