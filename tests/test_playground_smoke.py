"""Import/compile-level smoke tests for playground/app.py.

No fastapi.testclient here — starlette's TestClient in this environment
requires a package (httpx2) that couldn't be installed this session (see
session notes). This still catches real regressions — import errors,
Jinja syntax errors, macro signature mismatches — just not full
request/response behavior. Live verification (running the app and curling
each route) covers the rest; the deferred Playwright layer (docs/testing.md)
covers real browser behavior.
"""

from playground.app import _paginate_widgets, _validate_budget, app, templates


def test_app_is_a_fastapi_instance():
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)


def test_every_template_compiles():
    for name in ["index.html", "_tasks_tbody.html", "_pagination_list.html", "_form_demo.html"]:
        templates.env.get_template(name)


def test_index_renders_every_component():
    tasks = [{"id": 1, "title": "Sample", "status": "pending", "priority": 50}]
    html = templates.get_template("index.html").render(
        tasks=tasks,
        field_errors={},
        budget_value=250,
        flashes_demo=[{"message": "x", "kind": "success"}],
        **_paginate_widgets(0),
    )
    assert "gth-stat-card" in html
    assert "gth-card" in html
    assert "gth-table" in html
    assert "gth-pagination" in html
    assert "gth-empty-state" in html
    assert "gth-form-field" in html
    assert "gth-toast" in html


def test_tasks_tbody_partial_has_no_table_wrapper():
    html = templates.get_template("_tasks_tbody.html").render(
        tasks=[{"id": 1, "title": "Sample", "status": "pending", "priority": 50}]
    )
    assert "<table" not in html


def test_tasks_tbody_empty_state():
    html = templates.get_template("_tasks_tbody.html").render(tasks=[])
    assert "No tasks match your search." in html


def test_pagination_partial_first_page_has_next_link():
    html = templates.get_template("_pagination_list.html").render(**_paginate_widgets(0))
    assert "Widget #1" in html
    assert "offset=5" in html


def test_pagination_partial_last_page_has_no_more_button():
    html = templates.get_template("_pagination_list.html").render(**_paginate_widgets(15))
    assert "Widget #16" in html
    assert "gth-pagination-more" not in html


def test_form_partial_shows_inline_error():
    html = templates.get_template("_form_demo.html").render(
        field_errors={"budget": ["Must be greater than or equal to 0"]},
        budget_value=-5,
    )
    assert "is-invalid" in html
    assert "Must be greater than or equal to 0" in html


def test_validate_budget():
    assert _validate_budget(250) is None
    assert _validate_budget(-5) == ["Must be greater than or equal to 0"]
    assert _validate_budget(5000) == ["Must be less than or equal to 1000"]
