"""The notification centre: notifications_page.html, notifications_panel.html
and notification_badge.html with the context greentechhub-fastapi's
NotificationViews passes, and the navbar bell (notifications_url)."""

from datetime import UTC, datetime

from test_app_shell_renders import _context, _env

NOW = datetime(2026, 1, 31, 9, 30, tzinfo=UTC)


def _n(id, message, *, read=False, **extra):
    return {"id": id, "message": message, "kind": "info", "title": None, "icon": None,
            "action_label": None, "action_url": None, "category": "general",
            "created_at": NOW, "read_at": NOW if read else None, "read": read,
            "read_url": f"/notifications/{id}/read", **extra}


ITEMS = [
    _n("a", "Sync <finished>", kind="success", title="Sync", action_label="Open stocks",
       action_url="/stocks"),
    _n("b", "Old news", read=True, kind="warn", action_url="javascript:alert(1)"),
]
NV = {"page_title": "Notifications", "unread_count": 1, "unread_only": False,
      "page_url": "/notifications", "mark_all_url": "/notifications/read-all"}
USER = {"username": "alice", "email": None}


def _render(template, **context):
    return _env().get_template(template).render(**_context(**{**NV, **context}))


def _main(html):
    return html.split("<main")[1].split("</main>")[0]


def test_the_page_lists_notifications_with_unread_markers_and_actions():
    main = _main(_render("notifications_page.html", notifications=ITEMS))
    assert main.count('class="list-group-item gth-notification ') == 2
    assert "gth-notification-success gth-notification-unread" in main
    assert '<span class="visually-hidden">Unread: </span>' in main
    assert "Sync &lt;finished&gt;" in main and "<finished>" not in main
    assert '<a class="gth-notification-action" href="/stocks">Open stocks</a>' in main
    assert "javascript:" not in main  # an unsafe action URL isn't linked
    assert main.count('class="gth-notification-read"') == 1  # only the unread one
    assert 'hx-post="/notifications/a/read"' in main
    assert '<input type="hidden" name="next" value="/notifications">' in main
    # htmx blanks `next`, so the server answers 204 + the event, not a redirect
    assert "hx-vals='{\"next\": \"\"}'" in main


def test_mark_all_read_shows_only_with_unread_and_the_switch_reflects_the_filter():
    with_unread = _main(_render("notifications_page.html", notifications=ITEMS))
    assert 'action="/notifications/read-all"' in with_unread
    assert 'href="/notifications" aria-current="page">All</a>' in with_unread
    none_unread = _main(_render("notifications_page.html", notifications=ITEMS[1:],
                                unread_count=0))
    assert "Mark all read" not in none_unread
    filtered = _main(_render("notifications_page.html", notifications=ITEMS[:1],
                             unread_only=True))
    assert 'href="/notifications?unread=1" aria-current="page">Unread' in filtered
    assert 'hx-get="/notifications?unread=1"' in filtered  # the list reloads its own view


def test_an_empty_list_says_so():
    assert "re all caught up." in _render("notifications_page.html", notifications=[])
    assert "No unread notifications." in _render("notifications_page.html", notifications=[],
                                                 unread_only=True, unread_count=0)


def test_the_panel_is_a_partial_with_see_all():
    panel = _env().get_template("notifications_panel.html").render(notifications=ITEMS, **NV)
    assert "<html" not in panel and "gth-navbar" not in panel
    assert '<a class="small" href="/notifications">See all</a>' in panel
    assert 'action="/notifications/read-all"' in panel
    assert panel.count('class="list-group-item gth-notification ') == 2


def test_the_badge_hides_at_zero_and_caps_at_99():
    badge = _env().get_template("notification_badge.html")
    assert badge.render(count=0) == ""
    assert ">3</span>" in badge.render(count=3) and "unread" in badge.render(count=3)
    assert ">99+</span>" in badge.render(count=150)


def test_the_navbar_bell_needs_notifications_url_and_a_user():
    shell = _env().get_template("app.html")
    with_bell = shell.render(**_context(current_user=USER, notifications_url="/notifications"))
    assert 'class="dropdown gth-notification-bell"' in with_bell
    assert 'hx-get="/notifications/badge"' in with_bell
    assert 'hx-trigger="load, gth:notifications from:body"' in with_bell
    assert 'hx-get="/notifications/panel"' in with_bell
    assert "gth-notification-bell" not in shell.render(**_context(current_user=USER))
    assert "gth-notification-bell" not in shell.render(
        **_context(notifications_url="/notifications"))
    sidebar = shell.render(**_context(current_user=USER, notifications_url="/n", layout="sidebar"))
    assert 'hx-get="/n/badge"' in sidebar
