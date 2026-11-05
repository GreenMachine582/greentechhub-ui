"""activity_page.html — the audit log as a gth_timeline activity feed, over
the same context as audit_page.html (greentechhub-fastapi's AuditViews with
page_template="activity_page.html"): an action filter that keeps what was
submitted, entries by day with icons per kind, and a "Load older" button
that picks the next page's entries out with hx-select."""

import re
from datetime import UTC, datetime

import html5lib
from jinja2 import ChoiceLoader, Environment, FileSystemLoader

import greentechhub_ui

ENTRIES = [
    {"at": datetime(2025, 3, 9, 14, 30, tzinfo=UTC), "actor": "local", "action": "jobs.succeeded",
     "target": "job:7", "summary": "Scan music finished"},
    {"at": datetime(2025, 3, 9, 9, 0, tzinfo=UTC), "actor": None, "action": "plan.applied",
     "target": None, "summary": "Applied <12> moves"},
    {"at": datetime(2025, 3, 8, 9, 0, tzinfo=UTC), "actor": "local", "action": "settings.changed",
     "target": None, "summary": ""},
]


def _render(**context) -> str:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    base = {"page_title": "Activity", "audit_url": "/activity",
            "audit_filters": {"actor": "", "action": "", "on_or_before": ""},
            "audit_entries": ENTRIES, "audit_next_url": None}
    return env.get_template("activity_page.html").render(**(base | context))


def _feed(html: str) -> str:
    return html.split('id="gth-activity-feed"', 1)[1]


def test_entries_are_a_timeline_grouped_by_day():
    html = _feed(_render())
    assert html.count('class="gth-timeline-day"') == 2
    assert html.count('class="gth-timeline-item"') == 3
    assert "Scan music finished" in html and '<span class="gth-timeline-actor">local</span>' in html
    assert '<span class="gth-timeline-actor text-secondary">System</span>' in html
    assert "<div class=\"gth-timeline-summary\">settings.changed</div>" in html


def test_icons_for_local_app_actions_and_overrides():
    html = _render()
    assert "bi-hourglass-split" in html and "bi-list-check" in html and "bi-sliders" in html
    custom = _render(activity_kinds={"jobs": ("cpu", "warn")})
    assert "bi-cpu" in custom and "bg-warning-subtle" in custom


def test_values_are_escaped():
    html = _render()
    assert "Applied <12> moves" not in html and "Applied &lt;12&gt; moves" in html


def test_an_action_filter_that_keeps_the_value():
    html = _render(audit_filters={"action": "jobs."})
    assert re.search(r'<form method="get" action="/activity"[^>]*role="search"', html)
    assert 'name="action"\n        value="jobs."' in html
    assert 'class="btn btn-sm btn-link gth-activity-clear" href="/activity"' in html
    assert "gth-activity-clear" not in _render()
    assert "gth-activity-filters" not in _render(activity_filter=False)


def test_load_older_selects_the_next_pages_entries():
    html = _render(audit_next_url="/activity?before=2025-03-08T09%3A00%3A00%2B00%3A00")
    button = html.split("gth-pagination-more", 1)[1].split("Load older", 1)[0]
    assert 'hx-get="/activity?before=2025-03-08T09%3A00%3A00%2B00%3A00"' in button
    assert 'hx-target="closest .gth-activity-more"' in button
    assert 'hx-select="#gth-activity-feed > *"' in button
    assert "Load older" in html
    assert "gth-pagination-more" not in _render()


def test_empty_states():
    assert "No activity yet." in _render(audit_entries=[])
    assert "Nothing matches this filter." in _render(audit_entries=[],
                                                     audit_filters={"action": "x."})


def test_the_page_is_a_well_formed_document():
    html5lib.HTMLParser(strict=True).parse(_render(audit_next_url="/activity?before=x"))
