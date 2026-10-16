"""gth_timeline (v0.20): an activity feed over AuditViews' rows, grouped by
day, an icon and tone per action prefix, "System" for no actor, relative
times in <time datetime>, "Load older" through gth_pagination; and the
relative_time function and filter it uses."""

import re
from datetime import UTC, date, datetime, timedelta

import pytest
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot
from test_playground_routes import _get, _run

import greentechhub_ui
from greentechhub_ui.formatting import relative_time

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
# Over a week old, so their relative time is the (fixed) date.
ENTRIES = [
    {"at": datetime(2025, 3, 9, 14, 30, tzinfo=UTC), "actor": "root", "action": "roles.granted",
     "target": "user:bob", "summary": "Granted admin to bob"},
    {"at": datetime(2025, 3, 9, 9, 0, tzinfo=UTC), "actor": None, "action": "auth.sign_in_failed",
     "target": None, "summary": "Failed sign-in as <script>"},
    {"at": datetime(2025, 3, 8, 9, 0, tzinfo=UTC), "actor": "bob", "action": "sync.emails",
     "target": None, "summary": ""},
]


def _env() -> Environment:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _render(entries=ENTRIES, **kwargs) -> str:
    return _env().from_string(
        '{% from "timeline.html" import gth_timeline %}{{ gth_timeline(entries, **kwargs) }}'
    ).render(entries=entries, kwargs=kwargs)


# ── relative_time ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("delta,expected", [
    (timedelta(seconds=20), "just now"), (timedelta(minutes=1), "1 minute ago"),
    (timedelta(minutes=5), "5 minutes ago"), (timedelta(hours=3), "3 hours ago"),
    (timedelta(hours=30), "yesterday"), (timedelta(days=4), "4 days ago"),
    (timedelta(minutes=-5), "in 5 minutes"), (timedelta(hours=-30), "tomorrow"),
    (timedelta(days=-3), "in 3 days"),
])
def test_relative_time(delta, expected):
    assert relative_time(NOW - delta, now=NOW) == expected


def test_a_week_or_more_is_the_date():
    assert relative_time(NOW - timedelta(days=8), now=NOW) == "8 Oct 2026"
    assert relative_time(NOW - timedelta(days=8), now=NOW, date_format="iso") == "2026-10-08"


def test_naive_datetimes_count_as_utc_and_dates_compare_by_day():
    assert relative_time(datetime(2026, 10, 16, 11, 0), now=NOW) == "1 hour ago"
    assert relative_time(date(2026, 10, 16), now=NOW) == "today"
    assert relative_time(date(2026, 10, 15), now=NOW) == "yesterday"
    assert relative_time(date(2026, 10, 13), now=NOW) == "3 days ago"


@pytest.mark.parametrize("value,expected", [(None, ""), ("", ""), ("soon", "soon")])
def test_empty_in_empty_out(value, expected):
    assert relative_time(value, now=NOW) == expected


def test_the_filter_follows_the_viewers_date_format():
    template = _env().from_string("{{ at|relative_time }}")
    old = datetime(2025, 3, 8, 9, 0, tzinfo=UTC)
    assert template.render(at=old) == "8 Mar 2025"
    assert template.render(at=old, user_settings={"locale.date_format": "iso"}) == "2025-03-08"
    assert template.render(at=datetime.now(UTC)) == "just now"


# ── gth_timeline ──────────────────────────────────────────────────────────────

def test_entries_are_grouped_by_day_newest_first():
    html = _render()
    days = re.findall(r'<h3 class="gth-timeline-day-heading">([^<]+)</h3>', html)
    assert days == ["9 Mar 2025", "8 Mar 2025"]
    assert html.count('class="gth-timeline-item"') == 3
    assert html.index("Granted admin to bob") < html.index("Failed sign-in")


def test_icons_and_tones_by_action_prefix_with_service_kinds_merged():
    html = _render(kinds={"sync": ("arrow-repeat", "good")})
    expected = (("primary", "people"), ("info", "box-arrow-in-right"), ("success", "arrow-repeat"))
    for tone, icon in expected:
        assert (f'bg-{tone}-subtle text-{tone}-emphasis" aria-hidden="true">'
                f'<i class="bi bi-{icon}"></i>') in html
    # without the service's kinds, an unknown prefix falls back to a neutral dot
    assert '<i class="bi bi-dot"></i>' in _render()


def test_actor_system_target_time_and_escaping():
    html = _render()
    assert '<span class="gth-timeline-actor">root</span>' in html
    assert '<span class="gth-timeline-actor text-secondary">System</span>' in html
    assert '<span class="gth-timeline-target">user:bob</span>' in html
    assert '<time datetime="2025-03-09T14:30:00+00:00" title="9 Mar 2025 14:30">' in html
    assert "<script>" not in html and "&lt;script&gt;" in html
    # an empty summary shows the action
    assert '<div class="gth-timeline-summary">sync.emails</div>' in html


def test_load_older_and_the_empty_state():
    next_url = "/feed?before=2025-03-08T09%3A00%3A00%2B00%3A00"
    html = _render(next_url=next_url)
    assert f'hx-get="{next_url}"' in html and "Load older" in html
    assert "Load older" not in _render()
    empty = _render(entries=[], empty_message="Nothing happened.")
    assert "Nothing happened." in empty and "gth-timeline-item" not in empty


def test_it_renders_without_install():
    env = Environment(autoescape=True, loader=FileSystemLoader(greentechhub_ui.components_path))
    source = '{% from "timeline.html" import gth_timeline %}{{ gth_timeline(entries) }}'
    html = env.from_string(source).render(entries=ENTRIES)
    assert html.count('class="gth-timeline-item"') == 3
    assert '<time datetime="2025-03-09T14:30:00+00:00"' in html


def test_snapshot():
    assert_snapshot(_render(next_url="/feed?before=x", kinds={"sync": ("arrow-repeat", "good")}),
                    "timeline")


# ── the playground's feed ─────────────────────────────────────────────────────

def test_the_playground_feed_pages_back():
    page = _run(_get("/data"))
    assert 'id="timeline"' in page.text and page.text.count('class="gth-timeline-item"') == 4
    next_url = re.search(r'hx-get="(/timeline-demo/feed\?before=[^"]+)"', page.text).group(1)
    older = _run(_get(next_url.replace("&amp;", "&")))
    assert older.status_code == 200 and older.text.count('class="gth-timeline-item"') == 4
    assert "<html" not in older.text  # a fragment, swapped in for the button
    last = re.search(r'hx-get="(/timeline-demo/feed\?before=[^"]+)"', older.text)
    assert last is None or _run(_get(last.group(1).replace("&amp;", "&"))).status_code == 200
