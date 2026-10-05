"""The navbar's user menu: the name (greentechhub-fastapi's
user_display_name first) and an avatar of its initials, in both layouts."""

from test_app_shell_renders import _context, _env


def _menu(layout="navbar", **context) -> str:
    html = _env().get_template("app.html").render(
        **_context(layout=layout, logout_url="/logout", **context))
    return html.split('class="dropdown gth-user-menu"')[1].split("</button>")[0]


def test_the_display_name_wins_with_its_initials():
    menu = _menu(current_user={"username": "alice", "email": None},
                 user_display_name="Ada Lovelace")
    assert '<span class="gth-avatar" aria-hidden="true">AL</span>' in menu
    assert '<span class="gth-user-menu-name">Ada Lovelace</span>' in menu
    assert "alice" not in menu


def test_without_one_the_user_id_or_the_emails_local_part():
    by_id = _menu(current_user={"username": "admin", "email": "admin@example.com"})
    assert ">A</span>" in by_id and '<span class="gth-user-menu-name">admin</span>' in by_id
    by_email = _menu(current_user={"username": None, "email": "bob.smith@example.com"})
    assert ">B</span>" in by_email and ">bob.smith</span>" in by_email


def test_a_nameless_user_keeps_the_person_icon():
    menu = _menu(current_user={"username": None, "email": None})
    assert 'bi-person-circle' in menu and "gth-avatar" not in menu
    assert '<span class="gth-user-menu-name">Account</span>' in menu


def test_the_sidebar_layout_shows_it_too():
    menu = _menu("sidebar", current_user={"username": "alice", "email": None},
                 user_display_name="  Grace   Brewster Hopper ")
    assert ">GH</span>" in menu
