"""The app shell's CSRF token (v0.17, greentechhub-fastapi's register_csrf +
ui_context): with csrf_token in the context, <body> carries it in hx-headers
for every htmx request (as csrf_header, default X-CSRF-Token) and the
navbar's logout form carries it as a hidden field, in both layouts; without
one, nothing changes."""

import json
import re
from html import unescape
from pathlib import Path

import pytest
from test_app_shell_renders import _context, _env

import greentechhub_ui

TOKEN = "tok_" + "a" * 28
USER = {"username": "alice", "email": None}


def _html(layout="navbar", **context) -> str:
    return _env().get_template("app.html").render(
        **_context(layout=layout, current_user=USER, logout_url="/logout", **context))


def _hx_headers(html: str) -> dict | None:
    match = re.search(r"<body hx-headers='([^']*)'>", html)
    return json.loads(unescape(match.group(1))) if match else None


def _logout_form(html: str) -> str:
    return html.split('<form method="post" action="/logout">')[1].split("</form>")[0]


@pytest.mark.parametrize("layout", ["navbar", "sidebar"])
def test_the_token_goes_on_every_htmx_request_and_the_logout_form(layout):
    html = _html(layout, csrf_token=TOKEN)
    assert _hx_headers(html) == {"X-CSRF-Token": TOKEN}
    assert f'<input type="hidden" name="csrf_token" value="{TOKEN}">' in _logout_form(html)


@pytest.mark.parametrize("layout", ["navbar", "sidebar"])
def test_nothing_changes_without_a_token(layout):
    html = _html(layout)
    assert "<body>" in html and "hx-headers" not in html.split("<body", 1)[1].split(">", 1)[0]
    assert "csrf_token" not in _logout_form(html)


def test_the_header_name_is_configurable():
    html = _html(csrf_token=TOKEN, csrf_header="X-CSRFToken")  # Django's
    assert _hx_headers(html) == {"X-CSRFToken": TOKEN}


def test_a_lazy_token_object_is_rendered_as_text():
    class Lazy:  # like Django's csrf_token
        def __str__(self):
            return TOKEN

    assert _hx_headers(_html(csrf_token=Lazy())) == {"X-CSRF-Token": TOKEN}


def test_a_hostile_token_cant_break_out_of_the_attribute():
    html = _html(csrf_token="x'><script>alert(1)</script>")
    assert "<script>alert(1)" not in html
    assert _hx_headers(html) == {"X-CSRF-Token": "x'><script>alert(1)</script>"}


def test_the_theme_toggle_fetch_fallback_sends_the_pages_hx_headers():
    js = (Path(greentechhub_ui.static_path) / "js" / "theme-toggle.js").read_text(encoding="utf-8")
    assert 'document.body.getAttribute("hx-headers")' in js
