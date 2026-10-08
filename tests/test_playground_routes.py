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
import re
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


async def _as(persona, method, path, **kwargs):
    """One request as a playground persona (its cookie set on the client)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                 cookies={"playground-user": persona}) as client:
        return await client.request(method, path, **kwargs)


def test_index_returns_200():
    response = _run(_get("/"))
    assert response.status_code == 200


def test_every_sidebar_link_returns_200():
    from greentechhub_ui.navigation import flatten
    from playground.app import PLAYGROUND_NAV

    paths = {entry["url"].split("#")[0] for entry in flatten(PLAYGROUND_NAV)}
    assert {"/layout", "/data", "/forms", "/tables", "/tree", "/roles"} <= paths
    async def get_as_admin(path):
        # as the demo admin, so permission-gated links (Roles) are reachable too
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "admin"}) as client:
            return await client.get(path)

    for path in sorted(paths):
        response = _run(get_as_admin(path))
        assert response.status_code == 200, path
        if path == "/login-demo":  # layout="auth": no sidebar to mark it
            continue
        assert 'aria-current="page"' in response.text, path  # the sidebar marks it


def test_every_demo_section_is_in_the_sidebar():
    # A demo section the nav doesn't link is missing from the sidebar, the
    # command palette and the overview cards alike.
    from pathlib import Path

    from greentechhub_ui.navigation import flatten
    from playground.app import PLAYGROUND_NAV

    linked = {entry["url"] for entry in flatten(PLAYGROUND_NAV)}
    pages = Path(playground_app.__file__).parent / "templates" / "pages"
    for category in PLAYGROUND_NAV:
        if not category.get("children"):
            continue  # a single-page entry (Extensibility, Personas) links the page itself
        page = pages / (category["url"].lstrip("/") + ".html")
        if not page.exists():
            continue  # e.g. /settings renders a shipped template
        ids = re.findall(r'<section\b[^>]*\sid="([^"]+)"', page.read_text(encoding="utf-8"))
        missing = [i for i in ids if f"{category['url']}#{i}" not in linked]
        assert not missing, (category["url"], missing)


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
    assert "gth-modal" not in response.text  # just the form, swapped into the open modal
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


CSRF = {"csrf_token": "playground-demo-token"}


def test_register_demo_with_an_email_confirms_before_sign_in():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            form = {"user_id": "ada", "password": "long-enough",
                    "password_confirm": "long-enough", **CSRF}
            bad = await client.post("/register-demo", data={**form, "email": "nope"})
            assert bad.status_code == 422 and 'value="nope"' in bad.text
            sent = await client.post("/register-demo", data={**form, "email": "ada@example.com"})
            assert sent.status_code == 200 and "Check your email" in sent.text
            link = re.search(r"/verify-email-demo/\S+", playground_app.OUTBOX.outbox[-1].text)
            login = {"user_id": "ada", "password": "long-enough", **CSRF}
            assert (await client.post("/login-demo", data=login)).status_code == 403
            assert "is confirmed" in (await client.get(link.group(0))).text
            signed_in = await client.post("/login-demo", data=login, follow_redirects=False)
            assert signed_in.status_code == 303
            no_email = await client.post("/register-demo", follow_redirects=False,
                                         data={**form, "user_id": "bea"})
            assert no_email.status_code == 303
            await client.post("/demo/reset")

    _run(flow())
    assert "ada" not in playground_app.DEMO_EMAILS


def test_login_and_register_demos_refuse_a_missing_csrf_token():
    page = _run(_get("/login-demo")).text
    assert '<input type="hidden" name="csrf_token" value="playground-demo-token">' in page
    refused = _run(_post("/login-demo", data={"user_id": "demo", "password": "demo"}))
    assert refused.status_code == 403 and "Your session expired" in refused.text
    forged = _run(_post("/register-demo", data={"user_id": "newbie2", "password": "long-enough",
                                                "password_confirm": "long-enough",
                                                "csrf_token": "forged"}))
    assert forged.status_code == 403 and "Your session expired" in forged.text
    ok = _run(_post("/register-demo", data={"user_id": "newbie2", "password": "long-enough",
                                            "password_confirm": "long-enough", **CSRF}))
    assert ok.status_code == 303


def test_login_demo_mirrors_login_views():
    page = _run(_get("/login-demo"))
    assert page.status_code == 200 and 'action="/login-demo"' in page.text
    assert "gth-toast-danger" not in page.text
    bad = _run(_post("/login-demo", data={"user_id": "bob", "password": "nope", **CSRF}))
    assert bad.status_code == 401
    assert "Incorrect user ID or password." in bad.text and 'value="bob"' in bad.text
    assert "Demo accounts: demo / demo" in bad.text
    good = _run(_post("/login-demo", data={"user_id": "demo", "password": "demo", **CSRF}))
    assert good.status_code == 303 and good.headers["location"] == "/"


def test_tables_stock_filter(monkeypatch):
    records = [dict(r) for r in playground_app.RECORDS]
    records[0]["stock"] = records[1]["stock"] = 0
    monkeypatch.setattr(playground_app, "RECORDS", records)
    def total(stock):
        return _run(_get("/tables", params={"stock": stock}, headers=HX)).text

    assert "of 2" in total("out")
    assert f"of {len(records) - 2}" in total("in")
    assert f"of {len(records)}" in total("x")  # anything else is no filter
    page = _run(_get("/tables", params={"stock": "out"})).text
    assert '<label class="form-label visually-hidden" for="gth-field-stock">Stock</label>' in page
    assert '<option value="out" selected>Sold out</option>' in page


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
    assert response.content[:3] == bytes([0xEF, 0xBB, 0xBF])  # csv_download's BOM, for Excel
    lines = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert lines[0] == ["ID", "Name", "Category", "Stock", "Price", "Added"]
    rows = lines[1:]
    assert len(rows) == 30 and {r[2] for r in rows} == {"Cable"}
    prices = [float(r[4]) for r in rows]
    assert prices == sorted(prices, reverse=True)


def test_report_pane_shows_the_year_with_amounts_and_its_csv_link():
    pane = _run(_get("/demo/report", params={"fy": "2023"})).text
    assert 'class="d-flex flex-wrap align-items-end gap-2 gth-filter-bar mb-3"' in pane
    assert '<option value="2023" selected>2023–24</option>' in pane
    assert 'href="/demo/report.csv?fy=2023" download>' in pane
    assert "gth-stat-grid" in pane and "Net gain/loss, FY 2023–24" in pane
    assert '<span class="gth-amount text-success">$711.30</span>' in pane  # the year's total
    assert '<span class="gth-amount text-danger">-$131.20</span>' in pane
    latest = _run(_get("/demo/report", params={"fy": "1999"})).text  # unknown: the latest year
    assert '<option value="2024" selected>' in latest
    assert '<span class="gth-amount">$0.00</span>' in latest


def test_report_csv_is_a_download_with_plain_decimals():
    response = _run(_get("/demo/report.csv", params={"fy": "2024"}))
    assert response.headers["content-disposition"] == 'attachment; filename="gains-2024.csv"'
    lines = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert lines == [["Stock", "Units", "Gain/loss"], ["WES", "40", "1210"],
                     ["TLS", "1000", "-385.75"], ["CSL", "2.5", "0"]]


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
    page = _run(_as("admin", "GET", "/settings"))  # the App section needs settings.manage
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
    assert "playground-prefs=" in response.headers["set-cookie"]  # per browser, not shared
    assert "ui.page_size" not in playground_app.SETTINGS_VALUES
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
    response = _run(_as("admin", "POST", "/settings-demo/app", data=unchecked))
    assert response.status_code == 200
    assert playground_app.SETTINGS_VALUES["site.maintenance"] is False
    checked = _run(_as("admin", "POST", "/settings-demo/app",
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


def test_demo_sign_in_drives_the_user_menu_and_permissioned_nav():
    app_link = 'href="/settings#gth-settings-app"'

    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            signed_out = await client.get("/settings")
            await client.post("/demo/sign-in", data={"as": "viewer"})
            viewer = await client.get("/settings")
            await client.post("/demo/sign-in", data={"as": "admin"})
            admin = await client.get("/settings")
            logout = await client.post("/demo/logout")
            after = await client.get("/settings")
            bad = await client.post("/demo/sign-in", data={"as": "root"})
            return signed_out, viewer, admin, logout, after, bad

    signed_out, viewer, admin, logout, after, bad = _run(flow())
    assert "gth-user-menu" not in signed_out.text and app_link not in signed_out.text
    assert "gth-user-menu" in viewer.text and ">viewer<" in viewer.text
    assert app_link not in viewer.text
    assert app_link in admin.text and 'action="/demo/logout"' in admin.text
    assert logout.status_code == 303
    assert "gth-user-menu" not in after.text and app_link not in after.text
    assert bad.status_code == 422


def test_saved_preferences_drive_dates_and_the_records_page_size():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            before = (await client.get("/data")).text, (await client.get("/tables")).text
            saved = await client.post("/settings-demo/preferences", data={
                "ui.theme": "dark", "locale.timezone": "Australia/Sydney",
                "locale.date_format": "dmy", "ui.page_size": "50"})
            after = (await client.get("/data")).text, (await client.get("/tables")).text
        # another browser (no cookie) still gets the defaults
        other = (await _get("/data")).text, (await _get("/tables")).text
        return before, saved, after, other

    before, saved, after, other = _run(flow())
    assert saved.status_code == 200
    for data, tables in (before, other):
        assert "5 Feb 2025 23:30" in data
        assert '<option value="10" selected>' in tables
    data, tables = after
    assert "06/02/2025 10:30" in data  # the aware 23:30 UTC example, in Sydney
    assert '<option value="50" selected>' in tables


def test_roles_demo_admin_only_and_assign_set_remove():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as anon:
            denied = await anon.get("/roles")
            denied_post = await anon.post("/roles", data={"subject": "x", "roles": "viewer"})
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "viewer"}) as viewer:
            viewer_page = await viewer.get("/roles")
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "admin"}) as admin:
            page = await admin.get("/roles")
            bad = await admin.post("/roles", data={"subject": " "})
            added = await admin.post("/roles", data={"subject": "carol",
                                                     "roles": ["viewer", "editor"]})
            changed = await admin.post("/roles/carol", data={"roles": ["admin"]})
            removed = await admin.delete("/roles/carol")
        return denied, denied_post, viewer_page, page, bad, added, changed, removed

    playground_app.ROLE_GRANTS.clear()
    try:
        denied, denied_post, viewer_page, page, bad, added, changed, removed = _run(flow())
        # a page sends you to pick a persona; a POST can't redirect, so it's a 403
        persona_url = "/personas?next=%2Froles&need=settings.manage"
        assert (denied.status_code, denied.headers["location"]) == (303, persona_url)
        assert (viewer_page.status_code, viewer_page.headers["location"]) == (303, persona_url)
        assert denied_post.status_code == 403
        assert page.status_code == 200 and 'id="gth-roles"' in page.text
        assert bad.status_code == 422
        assert "Enter a user ID." in bad.text and "Pick at least one role." in bad.text
        assert added.status_code == 200 and "Roles assigned to carol" in added.headers["HX-Trigger"]
        assert 'hx-post="/roles/carol"' in added.text
        assert changed.status_code == 200
        assert removed.status_code == 200 and "No roles assigned here yet." in removed.text
        assert playground_app.ROLE_GRANTS == {}
    finally:
        playground_app.ROLE_GRANTS.clear()


def test_personas_impersonate_and_return_to_next():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            picker = await client.get("/personas?next=/roles&need=settings.manage")
            as_admin = await client.post("/demo/sign-in", data={"as": "admin", "next": "/roles"})
            roles = await client.get("/roles")
            current = await client.get("/personas")
            htmx = await client.get("/roles", headers={"HX-Request": "true"})
            out = await client.post("/demo/sign-in", data={"as": "anonymous"})
            after = await client.get("/personas")
            return picker, as_admin, roles, current, htmx, out, after

    picker, as_admin, roles, current, htmx, out, after = _run(flow())
    assert picker.status_code == 200
    assert 'id="gth-persona-need"' in picker.text and "settings.manage" in picker.text
    assert '<input type="hidden" name="next" value="/roles">' in picker.text
    assert 'data-persona="anonymous"' in picker.text and 'data-persona="admin"' in picker.text
    assert (as_admin.status_code, as_admin.headers["location"]) == (303, "/roles")
    assert roles.status_code == 200 and htmx.status_code == 200
    assert 'Switch persona' in current.text  # the user menu's item
    assert re.search(r'data-persona="admin">.*?Current', current.text, re.S)
    assert (out.status_code, out.headers["location"]) == (303, "/personas")
    assert "gth-user-menu" not in after.text


def test_persona_next_must_stay_on_site():
    for evil in ("//evil.example/x", "https://evil.example", "/\\evil.example", "roles"):
        response = _run(_post("/demo/sign-in", data={"as": "viewer", "next": evil}))
        assert response.headers["location"] == "/personas", evil
    picker = _run(_get("/personas", params={"next": "//evil.example"}))
    assert 'name="next"' not in picker.text


def test_viewer_htmx_or_post_to_a_gated_page_is_a_403():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "viewer"}) as client:
            return (await client.get("/roles", headers={"HX-Request": "true"}),
                    await client.delete("/roles/carol"))

    htmx, delete = _run(flow())
    assert (htmx.status_code, delete.status_code) == (403, 403)


def test_app_settings_section_needs_settings_manage():
    playground_app.SETTINGS_VALUES.clear()
    data = {"site.banner": "Viewer was here", "site.maintenance": "true"}
    try:
        for persona in ("anonymous", "viewer"):
            page = _run(_as(persona, "GET", "/settings"))
            assert 'id="gth-settings-preferences"' in page.text, persona
            assert 'id="gth-settings-app"' not in page.text, persona
            denied = _run(_as(persona, "POST", "/settings-demo/app", data=data))
            assert denied.status_code == 403, persona
        assert playground_app.SETTINGS_VALUES == {}
        assert 'id="gth-settings-app"' in _run(_as("admin", "GET", "/settings")).text
        assert _run(_as("admin", "POST", "/settings-demo/app", data=data)).status_code == 200
        assert playground_app.SETTINGS_VALUES["site.banner"] == "Viewer was here"
    finally:
        playground_app.SETTINGS_VALUES.clear()


def test_app_section_uses_cores_site_banner_settings():
    from greentechhub_core.settings.builtins import (
        SITE_BANNER_KEY,
        SITE_BANNER_TONE_KEY,
        SITE_BANNER_TONES,
    )

    _, _, settings = playground_app.SETTINGS_DEMO["app"]
    banner, tone = settings[0], settings[1]
    assert (banner["key"], tone["key"]) == (SITE_BANNER_KEY, SITE_BANNER_TONE_KEY)
    assert (banner["type"], tone["type"]) == ("str", "choice")
    assert dict(tone["choices"]) == SITE_BANNER_TONES and tone["default"] == "warn"


def test_app_site_banner_shows_on_every_page_until_cleared():
    playground_app.SETTINGS_VALUES.clear()
    try:
        # No banner set: pages other than /feedback have no banner strip. (The
        # pre-paint script names the class, so look for the element's markup.)
        assert 'class="alert alert-' not in _run(_get("/data")).text
        saved = _run(_as("admin", "POST", "/settings-demo/app",
                         data={"site.banner": "Maintenance at 9pm", "site.banner_tone": "bad"}))
        assert saved.status_code == 200
        for path in ("/data", "/forms"):
            html = _run(_get(path)).text
            assert 'data-gth-banner="site"' in html, path
            assert "alert-danger" in html and "Maintenance at 9pm" in html, path
        # An unknown tone is a field error, not a broken banner.
        bad = _run(_as("admin", "POST", "/settings-demo/app", data={"site.banner_tone": "shout"}))
        assert bad.status_code == 422
        # Emptying it, or the demo reset, removes it.
        _run(_as("admin", "POST", "/settings-demo/app", data={"site.banner": "  "}))
        assert 'data-gth-banner="site"' not in _run(_get("/data")).text
        _run(_as("admin", "POST", "/settings-demo/app", data={"site.banner": "Back soon"}))
        assert "Back soon" in _run(_get("/data")).text
        _run(_post("/demo/reset"))
        assert 'data-gth-banner="site"' not in _run(_get("/data")).text
    finally:
        playground_app.SETTINGS_VALUES.clear()


def test_personas_only_send_a_persona_back_to_a_page_it_can_open():
    html = _run(_get("/personas", params={"next": "/roles", "need": "settings.manage"})).text
    cards = {key: html.split(f'data-persona="{key}"', 1)[1].split("</form>", 1)[0]
             for key in ("anonymous", "viewer", "admin")}
    assert 'name="next" value="/roles"' in cards["admin"]
    for key in ("anonymous", "viewer"):
        assert 'name="next"' not in cards[key], key
        assert "Can&#39;t open" in cards[key] or "Can't open" in cards[key], key


def test_saved_density_and_motion_reach_the_html_tag():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # a partial form: fields that weren't submitted keep their saved values
            saved = await client.post("/settings-demo/preferences",
                                      data={"ui.density": "compact", "ui.motion": "reduce"})
            page = await client.get("/forms")
            return saved, page

    saved, page = _run(flow())
    assert saved.status_code == 200
    tag = page.text[page.text.index("<html"):page.text.index(">", page.text.index("<html"))]
    assert 'data-gth-density="compact"' in tag and 'data-gth-motion="reduce"' in tag


def test_saved_sidebar_default_reaches_the_pre_paint_script():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            before = await client.get("/forms")
            await client.post("/settings-demo/preferences", data={"ui.sidebar_default": "rail"})
            after = await client.get("/forms")
            return before, after

    before, after = _run(flow())
    assert "var preferred = null;" in before.text
    assert 'var preferred = "rail";' in after.text



def test_saved_number_format_changes_money_and_number_for_that_browser():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/settings-demo/preferences",
                              data={"locale.number_format": "dot_comma"})
            mine = (await client.get("/data")).text
        other = (await _get("/data")).text
        return mine, other

    mine, other = _run(flow())
    assert "$1.234,50" in mine and "1.234.567,891" in mine
    assert "$1,234.50" in other and "1,234,567.891" in other


# gth_action_menu demo


async def _delete(path, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.delete(path, **kwargs)


def test_action_menu_archive_and_delete_answer_with_toasts():
    archived = _run(_post("/demo/tasks/2/archive"))
    assert archived.status_code == 204 and "Archived" in archived.headers["HX-Trigger"]
    deleted = _run(_delete("/demo/tasks/2"))
    assert deleted.status_code == 204 and "Deleted" in deleted.headers["HX-Trigger"]
    assert "warning" in deleted.headers["HX-Trigger"]
    assert _run(_post("/demo/tasks/99/archive")).status_code == 404
    assert _run(_delete("/demo/tasks/99")).status_code == 404


def test_action_rows_follow_inline():
    menu_only = _run(_get("/demo/action-rows?inline=0")).text
    two = _run(_get("/demo/action-rows?inline=2")).text
    every = _run(_get("/demo/action-rows?inline=all")).text
    assert "gth-action-menu-button" not in menu_only and "gth-action-menu-toggle" in menu_only
    assert two.count("gth-action-menu-button") == 2 * 8
    assert "gth-action-menu-toggle" not in every
    assert _run(_get("/demo/action-rows?inline=bogus")).text == menu_only


# gth_progress live demo


def test_progress_demo_polls_until_done():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            started = await client.post("/demo/progress/start")
            polls = [await client.get("/demo/progress") for _ in range(4)]
            return started, polls

    started, polls = _run(flow())
    assert 'aria-valuenow="0"' in started.text and 'hx-get="/demo/progress"' in started.text
    assert 'aria-valuenow="75"' in polls[2].text and "hx-trigger" in polls[2].text
    done = polls[3]
    assert 'aria-valuenow="100"' in done.text
    assert "hx-trigger" not in done.text  # no poll_url: polling stops
    assert "Sync complete" in done.headers["HX-Trigger"]
    assert "HX-Trigger" not in polls[2].headers


def test_notification_centre_demo_follows_the_fastapi_contract():
    playground_app._seed_notifications()
    page = _run(_as("viewer", "GET", "/notifications"))
    assert page.status_code == 200
    assert page.text.count('class="list-group-item gth-notification ') == 3
    assert ">2</span>" in _run(_as("viewer", "GET", "/notifications/badge")).text
    assert _run(_get("/notifications/badge")).status_code == 204
    unread = playground_app.NOTIFICATIONS.list_for_sync("viewer", unread_only=True)
    marked = _run(_as("viewer", "POST", f"/notifications/{unread[0].id}/read"))
    assert marked.status_code == 204
    assert json.loads(marked.headers["HX-Trigger"]) == {"gth:notifications": {"unread": 1}}
    redirected = _run(_as("viewer", "POST", "/notifications/read-all",
                          data={"next": "/notifications?unread=1"}))
    assert redirected.status_code == 303
    assert redirected.headers["location"] == "/notifications?unread=1"
    assert _run(_as("viewer", "GET", "/notifications/badge")).text.strip() == ""
    assert _run(_as("admin", "GET", "/notifications/badge")).text.strip() != ""  # per persona
    playground_app._seed_notifications()


def test_password_reset_and_verification_demos_use_fastapis_views():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            sent = await client.post("/forgot-password-demo", data={"identifier": "demo"})
            assert sent.status_code == 200 and "Check your email" in sent.text
            (message,) = playground_app.OUTBOX.outbox
            link = re.search(r"/reset-password-demo/\S+", message.text).group(0)
            assert (await client.get(link)).status_code == 200
            done = await client.post(link, data={"password": "brand-new-1",
                                                 "password_confirm": "brand-new-1"})
            assert "has been changed" in done.text
            login = await client.post("/login-demo", follow_redirects=False,
                                      data={"user_id": "demo", "password": "brand-new-1", **CSRF})
            assert login.status_code == 303
            refused = await client.post("/login-demo",
                                        data={"user_id": "newbie", "password": "newbie", **CSRF})
            assert refused.status_code == 403 and "Send the link again" in refused.text
            await client.post("/verify-email-demo/resend", data={"identifier": "newbie"})
            verify = re.search(r"/verify-email-demo/\S+", playground_app.OUTBOX.outbox[-1].text)
            assert "is confirmed" in (await client.get(verify.group(0))).text
            login = await client.post("/login-demo", follow_redirects=False,
                                      data={"user_id": "newbie", "password": "newbie", **CSRF})
            assert login.status_code == 303
            await client.post("/demo/reset")

    _run(flow())
    assert playground_app.DEMO_PASSWORDS["demo"] == "demo" and playground_app.OUTBOX.outbox == []


def test_profile_and_password_sections_as_settings_views_sends_them():
    async def flow():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "viewer"}) as client:
            page = (await client.get("/settings")).text
            assert re.findall(r'id="gth-settings-(\w+)"', page) == [
                "profile", "preferences", "password"]
            saved = await client.post("/settings-demo/profile",
                                      data={"display_name": " Vera Viewer ", "email": ""})
            assert saved.status_code == 200 and "Profile saved" in saved.headers["HX-Trigger"]
            assert ">VV</span>" in (await client.get("/layout")).text
            long = await client.post("/settings-demo/profile",
                                     data={"display_name": "x" * 81, "email": ""})
            assert long.status_code == 422 and "at most 80" in long.text
            wrong = await client.post("/settings-demo/password", data={
                "current_password": "guess-123", "new_password": "brand-new-1",
                "new_password_confirm": "brand-new-1"})
            assert wrong.status_code == 422 and "current password" in wrong.text
            assert "brand-new-1" not in wrong.text and "guess-123" not in wrong.text
            changed = await client.post("/settings-demo/password", data={
                "current_password": "password", "new_password": "brand-new-1",
                "new_password_confirm": "brand-new-1"})
            assert "Password changed" in changed.headers["HX-Trigger"]
            await client.post("/demo/reset")
        anonymous = (await _get("/settings")).text
        assert "gth-settings-profile" not in anonymous
        assert 'id="gth-settings-password"' not in anonymous

    _run(flow())
    assert playground_app.PROFILES["viewer"]["display_name"] == ""
