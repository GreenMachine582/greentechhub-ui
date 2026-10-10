"""audit_page.html — the ready-made audit log page a service (or
greentechhub-fastapi's AuditViews) renders with data only: a GET filter
form that keeps what was submitted, entries newest first with the system
shown for a missing actor, and the older-page link."""

import re
from datetime import UTC, datetime

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

import greentechhub_ui

ENTRIES = [
    {"at": datetime(2026, 10, 9, 14, 30, tzinfo=UTC), "actor": "root", "action": "roles.granted",
     "target": "user:bob", "summary": "Granted admin to bob"},
    {"at": datetime(2026, 10, 8, 9, 0, tzinfo=UTC), "actor": None, "action": "auth.sign_in_failed",
     "target": None, "summary": "Failed sign-in as <script>"},
]


def _render(**context) -> str:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    base = {"page_title": "Audit log", "audit_url": "/admin/audit",
            "audit_filters": {"actor": "", "action": "", "on_or_before": ""},
            "audit_entries": ENTRIES, "audit_next_url": None}
    return env.get_template("audit_page.html").render(**(base | context))


def test_a_get_filter_form_that_keeps_the_filters():
    html = _render(audit_filters={"actor": "alice", "action": "auth.",
                                  "on_or_before": "2026-10-03"})
    assert re.search(r'<form method="get" action="/admin/audit"[^>]*role="search"', html)
    assert 'name="actor"\n        value="alice"' in html
    assert 'name="action"\n        value="auth."' in html
    assert 'type="date" id="gth-audit-date" name="on_or_before"\n        value="2026-10-03"' in html
    assert 'class="btn btn-sm btn-link gth-audit-clear" href="/admin/audit"' in html


def test_no_clear_link_without_filters():
    assert "gth-audit-clear" not in _render()


def test_one_row_per_entry_newest_first():
    html = _render()
    body = html.split("<tbody", 1)[1].split("</tbody>", 1)[0]
    rows = re.findall(r"<tr>(.*?)</tr>", body, re.S)
    assert len(rows) == 2
    assert '<time datetime="2026-10-09T14:30:00+00:00">' in rows[0]
    assert "root" in rows[0] and "roles.granted" in rows[0] and "user:bob" in rows[0]
    assert '<span class="text-secondary">System</span>' in rows[1]


def test_values_are_escaped():
    html = _render()
    assert "Failed sign-in as <script>" not in html
    assert "Failed sign-in as &lt;script&gt;" in html


def test_empty_states():
    assert "Nothing has been recorded yet." in _render(audit_entries=[])
    filtered = _render(audit_entries=[], audit_filters={"actor": "zed", "action": "",
                                                        "on_or_before": ""})
    assert "No entries match these filters." in filtered


def test_the_older_page_link():
    assert "gth-audit-older" not in _render()
    cursor = "before=2026-10-08T09%3A00%3A00%2B00%3A00"
    html = _render(audit_next_url=f"/admin/audit?action=auth.&{cursor}")
    assert f'href="/admin/audit?action=auth.&amp;{cursor}"' in html


CELL = '<code class="gth-audit-action">'


def _playground_get(path, user="admin"):
    import asyncio

    import httpx

    from playground.app import app

    async def go():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": user}) as client:
            return await client.get(path)

    return asyncio.run(go())


def test_the_playground_demo_filters_and_pages_back():
    first = _playground_get("/audit")
    assert first.status_code == 200 and first.text.count(CELL) == 5
    older = re.search(r'gth-audit-older" href="([^"]+)"', first.text).group(1).replace("&amp;", "&")
    assert _playground_get(older).text.count(CELL) == 3
    auth = _playground_get("/audit?action=auth.")
    assert re.findall(re.escape(CELL) + r"([^<]+)<", auth.text) == [
        "auth.password_changed", "auth.signed_in", "auth.sign_in_failed", "auth.signed_in"]


def test_the_playground_demo_is_admin_only():
    assert _playground_get("/audit", user="viewer").status_code in (302, 303, 403)
