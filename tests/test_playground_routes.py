"""Route-level regression tests for playground/app.py via a real ASGI client.

Plain httpx is enough — starlette.testclient's fallback import (httpx2) only
raises when *neither* httpx nor httpx2 is installed; httpx alone satisfies it
(see docs/testing.md). Complements tests/test_playground_smoke.py, which
stays at the Jinja-render level and is faster for catching macro drift.
"""

import asyncio
import json

import httpx

from playground.app import app


async def _get(path, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, **kwargs)


async def _post(path, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, **kwargs)


def test_index_returns_200():
    response = asyncio.run(_get("/"))
    assert response.status_code == 200


def test_table_filter_returns_matching_rows_only():
    response = asyncio.run(_get("/table-demo/filter", params={"q": "release"}))
    assert response.status_code == 200
    assert "Write release notes" in response.text
    assert "Design onboarding flow" not in response.text


def test_table_filter_empty_query_returns_all_rows():
    response = asyncio.run(_get("/table-demo/filter"))
    assert response.status_code == 200
    assert "Design onboarding flow" in response.text


def test_pagination_list_first_page_has_next_link():
    response = asyncio.run(_get("/pagination-demo/list"))
    assert response.status_code == 200
    assert "Widget #1" in response.text
    assert "offset=5" in response.text


def test_pagination_list_last_page_has_no_more_link():
    response = asyncio.run(_get("/pagination-demo/list", params={"offset": 15}))
    assert response.status_code == 200
    assert "gth-pagination-more" not in response.text


def test_toast_demo_returns_204_with_hx_trigger():
    response = asyncio.run(_post("/toast-demo"))
    assert response.status_code == 204
    assert "Demo toast triggered!" in response.headers["HX-Trigger"]


def test_form_demo_success_returns_200_with_hx_trigger():
    response = asyncio.run(_post("/form-demo", data={"budget": "250"}))
    assert response.status_code == 200
    assert "Saved budget" in response.headers["HX-Trigger"]


def test_form_demo_below_min_returns_422_body_with_no_trigger():
    response = asyncio.run(_post("/form-demo", data={"budget": "-5"}))
    assert response.status_code == 422
    assert "is-invalid" in response.text
    assert "Must be greater than or equal to 0" in response.text
    assert "HX-Trigger" not in response.headers


def test_form_demo_above_max_returns_422():
    response = asyncio.run(_post("/form-demo", data={"budget": "5000"}))
    assert response.status_code == 422
    assert "Must be less than or equal to 1000" in response.text

def test_index_renders_v07_demos_with_vendored_assets():
    response = asyncio.run(_get("/"))
    assert 'id="gth-modal-host"' in response.text
    assert '<script src="/gth-assets/js/modal-host.js"></script>' in response.text
    assert '<script src="/gth-assets/js/combobox.js"></script>' in response.text
    assert "gth-busy-button" in response.text
    assert "gth-table-load-more" in response.text


def test_widget_rows_load_more_pages_through_and_stops():
    first = asyncio.run(_get("/v07-demo/widget-rows", params={"page": 1}))
    assert "Widget #1<" in first.text and "page=2" in first.text
    last = asyncio.run(_get("/v07-demo/widget-rows", params={"page": 4}))
    assert "Widget #16<" in last.text and "gth-table-load-more" not in last.text


def test_widget_options_filter_and_empty_state():
    response = asyncio.run(_get("/v07-demo/widgets", params={"q": "#1"}))
    assert 'data-label="Widget #1"' in response.text and 'data-value="1"' in response.text
    assert "Widget #2<" not in response.text
    empty = asyncio.run(_get("/v07-demo/widgets", params={"q": "zzz"}))
    assert "No matching widgets" in empty.text


def test_modal_submit_without_pick_rerenders_form_with_422():
    data = {"widget": "", "widget_search": "Wid", "size": "L"}
    response = asyncio.run(_post("/v07-demo/modal", data=data))
    assert response.status_code == 422
    assert response.text.lstrip().startswith("<form")
    assert "Pick a widget from the list." in response.text
    assert 'value="Wid"' in response.text


def test_modal_submit_closes_modal_via_hx_trigger():
    response = asyncio.run(_post("/v07-demo/modal", data={"widget": "3", "size": "L"}))
    assert response.status_code == 204
    trigger = json.loads(response.headers["HX-Trigger"])
    assert trigger["closeModal"] is True
    assert trigger["showToast"]["message"] == "Saved Widget #3 (L)"
