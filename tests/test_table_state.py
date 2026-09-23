import pytest

from greentechhub_ui import TableState


def _state(query=None, **kwargs):
    kwargs.setdefault("id", "t")
    kwargs.setdefault("base_url", "/rows")
    return TableState.from_query(query or {}, **kwargs)


def test_defaults():
    s = _state()
    assert (s.mode, s.page, s.page_size, s.sort, s.direction) == ("load_more", 1, 25, None, "asc")
    assert s.filters == {} and not s.rows_only
    assert (s.offset, s.limit) == (0, 25)


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        _state(mode="scroll")


@pytest.mark.parametrize("raw, page", [("3", 3), ("0", 1), ("-2", 1), ("abc", 1), (None, 1)])
def test_page_is_clamped(raw, page):
    assert _state({"page": raw} if raw is not None else {}).page == page


def test_size_only_from_allow_list():
    assert _state({"size": "50"}, page_sizes=(10, 50)).page_size == 50
    assert _state({"size": "10000"}, page_sizes=(10, 50)).page_size == 25
    assert _state({"size": "50"}).page_size == 25  # no page_sizes: fixed size


def test_sort_only_from_allow_list():
    s = _state({"sort": "price", "dir": "desc"}, sortable=("price",))
    assert (s.sort, s.direction) == ("price", "desc")
    s = _state({"sort": "password", "dir": "desc"}, sortable=("price",), default_sort="name")
    assert (s.sort, s.direction) == ("name", "asc")


def test_filters_are_stripped_and_limited_to_filter_params():
    s = _state({"q": "  bolt ", "status": "x", "category": ""}, filter_params=("q", "category"))
    assert s.filters == {"q": "bolt"}


def test_rows_only_only_for_append_modes():
    assert _state({"partial": "rows"}, mode="infinite").rows_only
    assert _state({"partial": "rows"}, mode="load_more").rows_only
    assert not _state({"partial": "rows"}, mode="pages").rows_only


def test_url_keeps_filters_and_sort_and_omits_defaults():
    s = _state({"q": "a b", "sort": "price", "dir": "desc", "page": "2"},
               sortable=("price",), default_sort="name", page_sizes=(25, 50))
    assert s.url() == "/rows?q=a+b&sort=price&dir=desc&page=2"
    assert s.url(page=None) == "/rows?q=a+b&sort=price&dir=desc"
    assert s.url(q=None, sort=None) == "/rows?page=2"
    assert s.url(size=50) == "/rows?q=a+b&sort=price&dir=desc&size=50&page=2"


def test_url_appends_to_a_base_url_with_a_query():
    s = _state({"page": "2"}, base_url="/tables?mode=pages")
    assert s.url() == "/tables?mode=pages&page=2"
    assert s.url(page=1) == "/tables?mode=pages"


def test_default_sort_is_left_out_of_urls():
    s = _state(sortable=("name",), default_sort="name")
    assert s.url(page=2) == "/rows?page=2"
    assert s.sort_url("name") == "/rows?sort=name&dir=desc"


def test_next_url_per_mode():
    assert _state(mode="load_more").with_result(total=60).next_url == "/rows?page=2&partial=rows"
    assert _state(mode="infinite").with_result(total=60).next_url == "/rows?page=2&partial=rows"
    assert _state(mode="pages").with_result(total=60).next_url == "/rows?page=2"
    assert _state(mode="none").with_result(total=60).next_url is None
    assert _state({"page": "3"}, mode="pages").with_result(total=60).next_url is None


def test_has_next_without_total():
    s = _state(mode="pages").with_result(has_next=True)
    assert s.total_pages is None and s.next_url == "/rows?page=2" and s.page_links() == []
    assert _state(mode="pages").with_result(has_next=False).next_url is None


def test_prev_url():
    assert _state().prev_url is None
    assert _state({"page": "2"}).prev_url == "/rows"
    assert _state({"page": "3"}).prev_url == "/rows?page=2"


def test_sort_url_toggles_and_resets_page():
    s = _state({"page": "4", "sort": "price"}, sortable=("price", "name"))
    assert s.sort_url("price") == "/rows?sort=price&dir=desc"
    assert s.sort_url("name") == "/rows?sort=name&dir=asc"
    assert s.aria_sort("price") == "ascending" and s.aria_sort("name") is None


def test_filter_and_size_urls_drop_what_the_control_supplies():
    s = _state({"q": "x", "page": "3", "size": "50"}, page_sizes=(25, 50))
    assert s.filter_url == "/rows?size=50"
    assert s.size_url == "/rows?q=x"


@pytest.mark.parametrize("page, links", [
    (1, [1, 2, 3, None, 12]),
    (6, [1, None, 4, 5, 6, 7, 8, None, 12]),
    (4, [1, 2, 3, 4, 5, 6, None, 12]),  # a one-page gap shows the page, not "…"
    (12, [1, None, 10, 11, 12]),
])
def test_page_links_window(page, links):
    s = _state({"page": str(page)}, mode="pages", page_size=10).with_result(total=120)
    assert s.total_pages == 12
    assert s.page_links() == links


def test_total_pages_is_at_least_one():
    assert _state().with_result(total=0).total_pages == 1
