"""Import/compile-level smoke tests for playground/app.py.

Deliberately stays at the Jinja-render level rather than going through a real
HTTP client — fast, and catches import errors, Jinja syntax errors, and macro
signature mismatches. Real request/response behavior (status codes,
`HX-Trigger` headers, 422 bodies) is covered by tests/test_playground_routes.py
via `httpx`/`ASGITransport`; real browser behavior by the Playwright layer
(docs/testing.md).
"""

from playground.app import (
    _multi_context,
    _paginate_widgets,
    _validate_budget,
    _widget_rows,
    app,
    templates,
)


def test_app_is_a_fastapi_instance():
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)


def test_every_template_compiles():
    for name in ["pages/overview.html", "pages/layout.html", "pages/data.html", "pages/forms.html",
                 "pages/feedback.html", "pages/overlays.html", "pages/navigation.html",
                 "pages/extensibility.html", "_tasks_tbody.html", "_pagination_list.html",
                 "_form_demo.html",
                 "tables.html", "_records_table.html", "_multi_form.html",
                 "_record_picker_panel.html", "_v07_form.html"]:
        templates.env.get_template(name)


def _page_html(name, path, **context):
    return templates.get_template(f"pages/{name}.html").render(
        current_path=path, page_title=name.title(), page_subtitle="", **context)


def test_pages_render_every_component():
    """What the single index page used to prove, per category page."""
    tasks = [{"id": 1, "title": "Sample", "status": "pending", "priority": 50}]
    html = {
        "layout": _page_html("layout", "/layout"),
        "data": _page_html("data", "/data", tasks=tasks, **_paginate_widgets(0), **_widget_rows(1)),
        "forms": _page_html("forms", "/forms", field_errors={}, budget_value=250,
                            **_multi_context(tags=["urgent"])),
        "feedback": _page_html("feedback", "/feedback",
                               flashes_demo=[{"message": "x", "kind": "success"}]),
        "overlays": _page_html("overlays", "/overlays", watchlist=[{"id": 1, "name": "W"}]),
    }
    assert "gth-stat-card" in html["layout"]
    assert "gth-card" in html["layout"]
    assert "gth-empty-state" in html["layout"]
    assert "gth-badge" in html["layout"] and "gth-tabs" in html["layout"]
    assert "gth-skeleton" in html["layout"]
    assert "gth-table" in html["data"]
    assert "gth-pagination" in html["data"]
    assert "gth-form-field" in html["forms"]
    assert "gth-multiselect" in html["forms"] and "gth-record-picker" in html["forms"]
    assert "gth-toast" in html["feedback"]
    assert "gth-confirm-delete" in html["overlays"] and "gth-modal" in html["overlays"]
    # Every page sits in the sidebar layout.
    assert all('class="gth-shell"' in page for page in html.values())


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
