"""Route-level regression tests for playground/app.py via a real ASGI client.

Plain httpx is enough — starlette.testclient's fallback import (httpx2) only
raises when *neither* httpx nor httpx2 is installed; httpx alone satisfies it
(see docs/testing.md). Complements tests/test_playground_smoke.py, which
stays at the Jinja-render level and is faster for catching macro drift.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import httpx

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

def test_index_renders_v07_demos_with_vendored_assets():
    response = _run(_get("/"))
    assert 'id="gth-modal-host"' in response.text
    assert '<script src="/gth-assets/js/modal-host.js"></script>' in response.text
    assert '<script src="/gth-assets/js/combobox.js"></script>' in response.text
    assert "gth-busy-button" in response.text
    assert "gth-table-load-more" in response.text


def test_widget_rows_load_more_pages_through_and_stops():
    first = _run(_get("/v07-demo/widget-rows", params={"page": 1}))
    assert "Widget #1<" in first.text and "page=2" in first.text
    last = _run(_get("/v07-demo/widget-rows", params={"page": 4}))
    assert "Widget #16<" in last.text and "gth-table-load-more" not in last.text


def test_widget_options_filter_and_empty_state():
    response = _run(_get("/v07-demo/widgets", params={"q": "#1"}))
    assert 'data-label="Widget #1"' in response.text and 'data-value="1"' in response.text
    assert "Widget #2<" not in response.text
    empty = _run(_get("/v07-demo/widgets", params={"q": "zzz"}))
    assert "No matching widgets" in empty.text


def test_modal_submit_without_pick_rerenders_form_with_422():
    data = {"widget": "", "widget_search": "Wid", "size": "L"}
    response = _run(_post("/v07-demo/modal", data=data))
    assert response.status_code == 422
    assert response.text.lstrip().startswith("<form")
    assert "Pick a widget from the list." in response.text
    assert 'value="Wid"' in response.text


def test_modal_submit_closes_modal_via_hx_trigger():
    response = _run(_post("/v07-demo/modal", data={"widget": "3", "size": "L"}))
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


def test_tables_infinite_rows_only_append():
    response = _run(_get("/tables", params={"mode": "infinite", "page": 12, "partial": "rows"},
                         headers=HX))
    assert "<thead>" not in response.text
    assert response.text.count("data-record-id=") == 10
    assert "gth-table-load-more" not in response.text  # last page: no trailing row


def test_tables_unknown_mode_falls_back_to_pages():
    assert 'data-gth-table-mode="pages"' in _run(_get("/tables", params={"mode": "bogus"})).text


def test_record_picker_panel_first_load_has_filter_then_swaps_do_not():
    first = _run(_get("/v07-demo/record-picker", params={"for": "page"}, headers=HX))
    assert "gth-table-filter" in first.text and 'id="picker-page"' in first.text
    assert first.text.count("data-gth-pick") == 10

    swap = _run(_get("/v07-demo/record-picker", params={"for": "page", "page": 2},
                     headers={**HX, "HX-Target": "picker-page"}))
    assert "gth-table-filter" not in swap.text
    assert "11–20 of 120" in swap.text


def test_record_picker_ids_are_per_picker():
    modal = _run(_get("/v07-demo/record-picker", params={"for": "modal"}, headers=HX))
    assert 'id="picker-modal"' in modal.text
    bogus = _run(_get("/v07-demo/record-picker", params={"for": "<x>"}, headers=HX))
    assert 'id="picker-page"' in bogus.text
