"""Route-level regression tests for playground/app.py via a real ASGI client.

Plain httpx is enough — starlette.testclient's fallback import (httpx2) only
raises when *neither* httpx nor httpx2 is installed; httpx alone satisfies it
(see docs/testing.md). Complements tests/test_playground_smoke.py, which
stays at the Jinja-render level and is faster for catching macro drift.
"""

import asyncio
import csv
import io
import json
from concurrent.futures import ThreadPoolExecutor

import httpx

from playground import app as playground_app
from playground.app import app


def _run(coro):
    """asyncio.run on a worker thread. In a session that also runs the e2e
    suite, pytest-playwright's sync API leaves an event loop running on the
    main thread, and asyncio.run refuses to start there."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def _get(path, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, **kwargs)


async def _post(path, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, **kwargs)


def test_index_returns_200():
    response = _run(_get("/"))
    assert response.status_code == 200


def test_every_sidebar_link_returns_200():
    from greentechhub_ui.navigation import flatten
    from playground.app import PLAYGROUND_NAV

    paths = {entry["url"].split("#")[0] for entry in flatten(PLAYGROUND_NAV)}
    assert {"/layout", "/data", "/forms", "/tables", "/tree"} <= paths
    for path in sorted(paths):
        response = _run(_get(path))
        assert response.status_code == 200, path
        assert 'aria-current="page"' in response.text, path  # the sidebar marks it


def test_table_filter_returns_matching_rows_only():
    response = _run(_get("/table-demo/filter", params={"q": "release"}))
    assert response.status_code == 200
    assert "Write release notes" in response.text
    assert "Design onboarding flow" not in response.text


def test_table_filter_empty_query_returns_all_rows():
    response = _run(_get("/table-demo/filter"))
    assert response.status_code == 200
    assert "Design onboarding flow" in response.text


def test_pagination_list_first_page_has_next_link():
    response = _run(_get("/pagination-demo/list"))
    assert response.status_code == 200
    assert "Widget #1" in response.text
    assert "offset=5" in response.text


def test_pagination_list_last_page_has_no_more_link():
    response = _run(_get("/pagination-demo/list", params={"offset": 15}))
    assert response.status_code == 200
    assert "gth-pagination-more" not in response.text


def test_toast_demo_returns_204_with_hx_trigger():
    response = _run(_post("/toast-demo"))
    assert response.status_code == 204
    assert "Demo toast triggered!" in response.headers["HX-Trigger"]


def test_form_demo_success_returns_200_with_hx_trigger():
    response = _run(_post("/form-demo", data={"budget": "250"}))
    assert response.status_code == 200
    assert "Saved budget" in response.headers["HX-Trigger"]


def test_form_demo_below_min_returns_422_body_with_no_trigger():
    response = _run(_post("/form-demo", data={"budget": "-5"}))
    assert response.status_code == 422
    assert "is-invalid" in response.text
    assert "Must be greater than or equal to 0" in response.text
    assert "HX-Trigger" not in response.headers


def test_form_demo_above_max_returns_422():
    response = _run(_post("/form-demo", data={"budget": "5000"}))
    assert response.status_code == 422
    assert "Must be less than or equal to 1000" in response.text

def test_pages_render_demos_with_vendored_assets():
    overlays = _run(_get("/overlays")).text
    assert 'id="gth-modal-host"' in overlays
    assert '<script src="/gth-assets/js/modal-host.js"></script>' in overlays
    assert '<script src="/gth-assets/js/combobox.js"></script>' in overlays
    assert "gth-busy-button" in _run(_get("/forms")).text
    assert "gth-table-load-more" in _run(_get("/data")).text


def test_playground_runs_in_the_sidebar_layout():
    html = _run(_get("/forms")).text
    assert 'id="gth-sidebar"' in html
    assert '<script src="/gth-assets/js/sidebar.js"></script>' in html
    assert "<dialog" in html  # the command palette comes with the sidebar layout
    # Breadcrumbs derived from the nav: /tables sits under the Data group.
    tables = _run(_get("/tables")).text
    assert '<a href="/data">Data</a>' in tables


def test_widget_rows_load_more_pages_through_and_stops():
    first = _run(_get("/demo/widget-rows", params={"page": 1}))
    assert "Widget #1<" in first.text and "page=2" in first.text
    last = _run(_get("/demo/widget-rows", params={"page": 4}))
    assert "Widget #16<" in last.text and "gth-table-load-more" not in last.text


def test_widget_options_filter_and_empty_state():
    response = _run(_get("/demo/widgets", params={"q": "#1"}))
    assert 'data-label="Widget #1"' in response.text and 'data-value="1"' in response.text
    assert "Widget #2<" not in response.text
    empty = _run(_get("/demo/widgets", params={"q": "zzz"}))
    assert "No matching widgets" in empty.text


def test_modal_submit_without_pick_rerenders_form_with_422():
    data = {"widget": "", "widget_search": "Wid", "size": "L"}
    response = _run(_post("/demo/modal", data=data))
    assert response.status_code == 422
    assert response.text.lstrip().startswith("<form")
    assert "Pick a widget from the list." in response.text
    assert 'value="Wid"' in response.text


def test_modal_submit_closes_modal_via_hx_trigger():
    response = _run(_post("/demo/modal", data={"widget": "3", "size": "L"}))
    assert response.status_code == 204
    trigger = json.loads(response.headers["HX-Trigger"])
    assert trigger["closeModal"] is True
    assert trigger["showToast"]["message"] == "Saved Widget #3 (L)"


HX = {"HX-Request": "true"}


def test_tables_full_page_then_htmx_fragment():
    page = _run(_get("/tables"))
    assert page.status_code == 200
    assert "<html" in page.text and 'id="records"' in page.text and "gth-table-filter" in page.text

    fragment = _run(_get("/tables", params={"mode": "pages", "page": 2}, headers=HX))
    assert "<html" not in fragment.text and "gth-table-filter" not in fragment.text
    assert fragment.text.strip().startswith('<div id="records"')
    assert "11–20 of 120" in fragment.text


def test_tables_history_restore_gets_the_whole_page():
    headers = {**HX, "HX-History-Restore-Request": "true"}
    response = _run(_get("/tables", params={"page": 3}, headers=headers))
    assert "<html" in response.text


def test_tables_sort_and_filter():
    response = _run(_get("/tables", params={"sort": "price", "dir": "desc", "category": "Motor",
                                             "q": "part"}, headers=HX))
    assert 'aria-sort="descending"' in response.text
    assert "Sensor" not in response.text.split("<tbody")[1]


def test_tables_date_range_filter():
    fy = {"date_from": "2025-07-01", "date_to": "2026-06-30"}
    assert "of 73" in _run(_get("/tables", params=fy, headers=HX)).text
    assert "of 36" in _run(_get("/tables", params={"date_to": "2025-06-30"}, headers=HX)).text
    # A malformed date is ignored, not a 500.
    assert "of 120" in _run(_get("/tables", params={"date_from": "nope"}, headers=HX)).text


def test_demo_upload_rechecks_type_and_size(monkeypatch):
    monkeypatch.setattr(playground_app, "UPLOAD_DELAY", 0)

    def upload(files):
        return _run(_post("/demo/upload", files=files))

    csv = ("a.csv", b"x,y\n1,2\n", "text/csv")
    ok = upload([("files", csv)])
    assert ok.status_code == 200 and "Uploaded: <code>a.csv (8 B)</code>" in ok.text

    bad = upload([("files", ("n.txt", b"hi", "text/plain")),
                  ("files", ("big.csv", b"x" * (1024 * 1024 + 1), "text/csv"))])
    assert bad.status_code == 422
    assert "n.txt — not an accepted file type" in bad.text
    assert "big.csv — larger than 1 MB" in bad.text

    # A browser submits an empty file part when nothing was chosen.
    empty = upload([("files", ("", b"", "application/octet-stream"))])
    assert empty.status_code == 422 and "Choose at least one file." in empty.text


def test_bulk_record_actions_then_reset():
    records = playground_app.RECORDS
    before = (records[0]["stock"], records[1]["stock"], records[2]["stock"])
    try:
        response = _run(_post("/demo/records/restock", data={"ids": ["1", "2", "x"]}))
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["showToast"]["message"] == "Restocked 2 records."
        assert "recordsChanged" in trigger
        assert (records[0]["stock"], records[1]["stock"]) == (before[0] + 50, before[1] + 50)
        assert records[2]["stock"] == before[2]

        _run(_post("/demo/records/sold-out", data={"ids": "3"}))
        assert records[2]["stock"] == 0
    finally:
        _run(_post("/demo/reset"))
    assert (records[0]["stock"], records[1]["stock"], records[2]["stock"]) == before


def test_tables_export_csv_honours_filters_and_sort_not_paging():
    params = {"category": "Cable", "sort": "price", "dir": "desc", "page": "3", "size": "10"}
    response = _run(_get("/tables/export.csv", params=params))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="records.csv"'
    lines = list(csv.reader(io.StringIO(response.text)))
    assert lines[0] == ["ID", "Name", "Category", "Stock", "Price", "Added"]
    rows = lines[1:]
    assert len(rows) == 30 and {r[2] for r in rows} == {"Cable"}
    prices = [float(r[4]) for r in rows]
    assert prices == sorted(prices, reverse=True)


def test_tables_page_links_the_export_with_the_current_filters():
    page = _run(_get("/tables", params={"category": "Motor", "sort": "stock", "page": "2"})).text
    assert 'href="/tables/export.csv?category=Motor&amp;sort=stock&amp;dir=asc" download>' in page


def test_form_demo_keeps_notes_and_rechecks_their_length():
    ok = _run(_post("/form-demo", data={"budget": "250", "notes": "Hello"}))
    assert ok.status_code == 200 and ">Hello</textarea>" in ok.text
    assert ">5 / 140</div>" in ok.text
    long = _run(_post("/form-demo", data={"budget": "250", "notes": "x" * 141}))
    assert long.status_code == 422 and "Keep notes to 140 characters." in long.text


def test_formatting_filters_render_in_the_playground():
    data = _run(_get("/data")).text
    for out in ("$1,234.50", "-$1,234.50", "€100", "100.5", "1,234,567.891", "2.50", "5 Feb 2025",
                "05/02/2025 10:30", "(empty)"):
        assert out in data, out
    table = _run(_get("/tables", params={"sort": "name"}, headers=HX)).text
    assert "$36.79" in table and "31 Jan 2025" in table  # money / date in the records table


def test_tables_infinite_rows_only_append():
    response = _run(_get("/tables", params={"mode": "infinite", "page": 12, "partial": "rows"},
                         headers=HX))
    assert "<thead>" not in response.text
    assert response.text.count("data-record-id=") == 10
    assert "gth-table-load-more" not in response.text  # last page: no trailing row


def test_tables_unknown_mode_falls_back_to_pages():
    assert 'data-gth-table-mode="pages"' in _run(_get("/tables", params={"mode": "bogus"})).text


def test_record_picker_panel_first_load_has_filter_then_swaps_do_not():
    first = _run(_get("/demo/record-picker", params={"for": "page"}, headers=HX))
    assert "gth-table-filter" in first.text and 'id="picker-page"' in first.text
    assert first.text.count("data-gth-pick") == 10

    swap = _run(_get("/demo/record-picker", params={"for": "page", "page": 2},
                     headers={**HX, "HX-Target": "picker-page"}))
    assert "gth-table-filter" not in swap.text
    assert "11–20 of 120" in swap.text


def test_record_picker_ids_are_per_picker():
    modal = _run(_get("/demo/record-picker", params={"for": "modal"}, headers=HX))
    assert 'id="picker-modal"' in modal.text
    bogus = _run(_get("/demo/record-picker", params={"for": "<x>"}, headers=HX))
    assert 'id="picker-page"' in bogus.text


def test_tree_lazy_nodes_and_unknown_tree():
    r = _run(_get("/tree/nodes", params={"tree": "reorder", "parent": "a:Motor:Bravo", "level": 3}))
    assert r.status_code == 200
    assert r.text.count('role="treeitem"') == 10
    assert 'aria-level="3"' in r.text and 'aria-checked="false"' in r.text
    unknown = _run(_get("/tree/nodes", params={"tree": "x", "parent": "a:Motor:Bravo"}))
    assert unknown.status_code == 404


def test_tree_reorder_resolves_top_most_ids_and_422s_when_empty():
    ok = _run(_post("/tree/reorder", data={"nodes": ["c:Motor", "p:12"]}))
    assert ok.status_code == 200 and "31 parts" in ok.text  # 30 motors + one sensor part
    empty = _run(_post("/tree/reorder", data={}))
    assert empty.status_code == 422 and "Tick at least one" in empty.text


def test_tree_reorder_rerender_keeps_checked_part_in_place():
    r = _run(_post("/tree/reorder", data={"nodes": ["p:1"]}))
    # p:1's assembly is rendered expanded with its parts inline (not lazy),
    # so the checked part is there to show.
    assert 'data-gth-node="p:1"' in r.text
    part = r.text.split('data-gth-node="p:1"')[1].split(">")[0]
    assert 'aria-checked="true"' in part


def test_demo_reset_restores_state_and_refreshes_views():
    from playground.app import HEALTH_ISSUES, WATCHLIST_DEMO

    WATCHLIST_DEMO.clear()
    HEALTH_ISSUES["open"] = 0
    assert _run(_get("/nav-badges/watchlist")).text == ""  # zero hides the badge
    response = _run(_post("/demo/reset"))
    assert response.status_code == 204 and response.text == ""
    trigger = json.loads(response.headers["HX-Trigger"])
    assert {"watchlistChanged", "healthChanged", "watchlistReset"} <= set(trigger)
    assert [item["name"] for item in WATCHLIST_DEMO] == ["Widget A", "Widget B", "Widget C"]
    assert HEALTH_ISSUES["open"] == 3
    assert ">3</span>" in _run(_get("/nav-badges/watchlist")).text
    assert "Widget A" in _run(_get("/demo/watchlist")).text


def test_playground_pages_get_current_path_from_the_context_processor():
    # No route passes current_path any more: greentechhub_fastapi's ui_context does.
    html = _run(_get("/tree")).text
    assert 'aria-current="page"' in html and '<a href="/data">Data</a>' in html


def test_settings_page_renders_each_widget():
    page = _run(_get("/settings"))
    assert page.status_code == 200
    for marker in ('id="gth-settings-preferences"', 'id="gth-settings-app"', "gth-segmented",
                   "gth-select", 'type="number"', 'role="switch"'):
        assert marker in page.text, marker


def test_settings_demo_saves_and_toasts():
    playground_app.SETTINGS_VALUES.clear()
    data = {"ui.theme": "dark", "locale.timezone": "Asia/Tokyo", "locale.date_format": "dmy",
            "ui.page_size": "50"}
    response = _run(_post("/settings-demo/preferences", data=data))
    assert response.status_code == 200
    assert "Preferences saved" in response.headers["HX-Trigger"]
    assert playground_app.SETTINGS_VALUES["ui.page_size"] == 50
    assert '<option value="Asia/Tokyo" selected>' in response.text
    playground_app.SETTINGS_VALUES.clear()


def test_settings_demo_returns_422_with_field_errors():
    data = {"ui.theme": "dark", "locale.timezone": "UTC", "locale.date_format": "iso",
            "ui.page_size": "500"}
    response = _run(_post("/settings-demo/preferences", data=data))
    assert response.status_code == 422
    assert "Must be between 5 and 200." in response.text
    assert 'value="500"' in response.text
    assert "HX-Trigger" not in response.headers


def test_settings_demo_unchecked_switch_submits_false():
    playground_app.SETTINGS_VALUES.clear()
    # what the browser sends for an unchecked gth_switch(off_value="false"): only the hidden input
    unchecked = {"site.banner": "", "site.maintenance": "false"}
    response = _run(_post("/settings-demo/app", data=unchecked))
    assert response.status_code == 200
    assert playground_app.SETTINGS_VALUES["site.maintenance"] is False
    checked = _run(_post("/settings-demo/app",
                         data={"site.banner": "Back soon", "site.maintenance": ["false", "true"]}))
    assert checked.status_code == 200
    assert playground_app.SETTINGS_VALUES["site.maintenance"] is True
    playground_app.SETTINGS_VALUES.clear()


def test_theme_demo_saves_to_a_cookie_and_seeds_the_next_page():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/forms")
            saved = await client.post("/demo/theme", data={"theme": "light"})
            second = await client.get("/forms")
            bad = await client.post("/demo/theme", data={"theme": "purple"})
            return first, saved, second, bad

    first, saved, second, bad = _run(flow())
    assert 'data-gth-theme-save-url="/demo/theme"' in first.text
    assert "var server = null;" in first.text
    assert saved.status_code == 204
    assert 'var server = "light";' in second.text
    assert bad.status_code == 422


def test_settings_theme_shares_the_toggles_store_and_applies_without_reload():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            saved = await client.post("/settings-demo/preferences", data={
                "ui.theme": "light", "locale.timezone": "UTC", "locale.date_format": "iso",
                "ui.page_size": "25"})
            page = await client.get("/settings")
            toggled = await client.post("/demo/theme", data={"theme": "dark"})
            after_toggle = await client.get("/settings")
            return saved, page, toggled, after_toggle

    playground_app.SETTINGS_VALUES.clear()
    saved, page, toggled, after_toggle = _run(flow())
    assert saved.status_code == 200
    assert json.loads(saved.headers["HX-Trigger"])["gth:theme"] == "light"
    assert "playground-theme=light" in saved.headers["set-cookie"]
    assert 'gth-field-ui.theme-1" autocomplete="off" checked' in saved.text
    assert 'var server = "light";' in page.text
    assert 'gth-field-ui.theme-1" autocomplete="off" checked' in page.text
    assert "ui.theme" not in playground_app.SETTINGS_VALUES
    # the navbar toggle writes the same store, so the form follows it
    assert toggled.status_code == 204
    assert 'gth-field-ui.theme-2" autocomplete="off" checked' in after_toggle.text
    playground_app.SETTINGS_VALUES.clear()
