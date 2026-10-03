"""login_page.html — the ready-made local-auth login page, rendered with the
context greentechhub-fastapi's LoginViews passes."""

import html5lib
from test_app_shell_renders import _context, _env


def _render(**context) -> str:
    return _env().get_template("login_page.html").render(**_context(**context))


def _main(html: str) -> str:
    return html.split("<main")[1].split("</main>")[0]


def test_bare_page_posts_user_id_and_password_to_login():
    main = _main(_render())
    assert '<form method="post" action="/login" class="gth-form">' in main
    assert "novalidate" not in main  # empty fields stop in the browser
    assert 'name="user_id"' in main and 'autocomplete="username"' in main
    assert 'name="password"' in main and 'type="password"' in main
    assert 'autocomplete="current-password"' in main
    assert main.count('required="required"') == 2
    assert '<h1 class="h3 mb-3">Log in</h1>' in main
    assert "gth-toast" not in main  # no error, no alert


def test_error_is_an_inline_danger_alert_and_escaped():
    main = _main(_render(error="Incorrect <user> ID or password", user_id='bob"&co'))
    assert 'gth-toast-inline gth-toast-danger gth-toast-surface mb-3"\n  role="alert"' in main
    assert "Incorrect &lt;user&gt; ID or password" in main
    assert 'value="bob&#34;&amp;co"' in main  # the prefill, escaped


def test_labels_and_action_are_configurable():
    main = _main(_render(login_url="/auth/login", login_title="Sign in", user_id_label="Email"))
    assert 'action="/auth/login"' in main
    assert '<h1 class="h3 mb-3">Sign in</h1>' in main and ">Sign in</button>" in main
    assert '<label class="form-label" for="gth-field-user_id">Email</label>' in main


def test_page_is_a_well_formed_document():
    html5lib.HTMLParser(strict=True).parse(_render(error="Nope", user_id="bob"))
