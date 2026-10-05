"""gth_csrf_field and the auth pages: with a csrf_token in the context every
auth form posts it as a hidden field; without one nothing changes."""

import pytest
from test_app_shell_renders import _context, _env

FIELD = '<input type="hidden" name="csrf_token" value="tok-123">'

PAGES = {
    "login_page.html": {},
    "register_page.html": {"register_url": "/register", "min_password_length": 8},
    "forgot_password_page.html": {"forgot_url": "/forgot-password"},
    "reset_password_page.html": {"action": "/reset-password/t", "min_password_length": 8},
    "verify_email_resend_page.html": {"resend_url": "/verify-email/resend"},
}


def _macro(**kwargs) -> str:
    template = _env().from_string(
        '{% from "form.html" import gth_csrf_field %}{{ gth_csrf_field(**kw) }}')
    return template.render(kw=kwargs)


def test_the_macro_renders_only_with_a_token():
    assert _macro() == "" and _macro(token="") == ""
    assert _macro(token="tok-123") == FIELD
    assert _macro(token='a"b<c') == '<input type="hidden" name="csrf_token" value="a&#34;b&lt;c">'
    assert _macro(token="t", name="_csrf") == '<input type="hidden" name="_csrf" value="t">'


@pytest.mark.parametrize("template", PAGES)
def test_each_auth_form_posts_the_token(template):
    page = _env().get_template(template)
    with_token = page.render(**_context(csrf_token="tok-123", **PAGES[template]))
    form = with_token.split('<form method="post"')[1].split("</form>")[0]
    assert FIELD in form
    without = page.render(**_context(**PAGES[template]))
    assert 'name="csrf_token"' not in without


def test_the_field_name_can_change():
    page = _env().get_template("login_page.html").render(
        **_context(csrf_token="tok-123", csrf_field_name="_csrf"))
    assert '<input type="hidden" name="_csrf" value="tok-123">' in page
