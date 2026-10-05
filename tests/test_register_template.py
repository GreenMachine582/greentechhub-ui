"""register_page.html — the ready-made sign-up page on app.html's
layout="auth", rendered with the context greentechhub-fastapi's
RegisterViews passes."""

import html5lib
from test_app_shell_renders import _context, _env
from test_login_template import LOGO

RV = {"register_url": "/register", "login_url": "/login", "min_password_length": 8}


def _render(**context) -> str:
    return _env().get_template("register_page.html").render(**_context(**{**RV, **context}))


def _main(html: str) -> str:
    return html.split("<main")[1].split("</main>")[0]


def test_auth_layout_with_the_brand_and_no_app_navbar():
    html = _render()
    assert '<main class="gth-auth">' in html
    assert "gth-navbar" not in html and "/watchlist" not in html
    assert '<div class="gth-auth-service">Playground</div>' in html
    assert '<footer class="gth-auth-footer">' in html


def test_bare_page_posts_the_three_fields_to_register():
    main = _main(_render())
    assert '<form method="post" action="/register" class="gth-form">' in main
    assert "novalidate" not in main
    assert ('<h1 class="h4 mb-1">Create account '
            '<span class="text-secondary fw-normal">to Playground</span></h1>') in main
    assert 'name="user_id"' in main and 'autocomplete="username" autofocus="autofocus"' in main
    assert 'name="password"' in main and 'name="password_confirm"' in main
    assert main.count('autocomplete="new-password"') == 2
    assert main.count('required="required"') == 3
    assert 'minlength="8"' in main
    help_text = '<div class="form-text" id="gth-field-password-help">At least 8 characters.</div>'
    assert help_text in main
    assert "</i> Create account\n" in main and "bi-person-plus" in main
    assert 'Already have an account? <a href="/login">Sign in</a>' in main
    assert "gth-toast" not in main


def test_no_length_hint_without_a_minimum():
    main = _main(_render(min_password_length=None))
    assert "minlength" not in main and "At least" not in main


def test_field_errors_show_under_their_fields_and_keep_the_user_id():
    main = _main(_render(user_id='bob"&co', errors={"user_id": ["That user ID is taken."]}))
    assert 'value="bob&#34;&amp;co"' in main
    assert 'id="gth-field-user_id" name="user_id"' in main
    assert 'aria-invalid="true"' in main and "That user ID is taken." in main
    assert 'autocomplete="username" autofocus="autofocus"' in main  # fix the user ID first


def test_a_refused_password_moves_focus_to_the_password():
    refused = {"password_confirm": ["The passwords don't match."]}
    main = _main(_render(user_id="bob", errors=refused))
    assert "The passwords don't match." in main
    assert 'autocomplete="new-password" minlength="8" autofocus="autofocus"' in main
    assert 'autocomplete="username" autofocus' not in main


def test_errors_for_other_keys_are_an_inline_danger_alert():
    main = _main(_render(errors={"__all__": ["Sign-up is <closed>."]}))
    assert "gth-toast-inline gth-toast-danger" in main
    assert "Sign-up is &lt;closed&gt;." in main


def test_options_and_footer_links():
    html = _render(register_url="/join", login_url=None, register_title="Join",
                   register_subtitle="It takes a minute.", user_id_label="Email",
                   register_help="We never share it.",
                   register_links=[{"label": "Terms", "url": "/terms"},
                                   {"label": "Bad", "url": "javascript:alert(1)"}])
    main = _main(html)
    assert 'action="/join"' in main and ">Join <span" in main
    assert '<label class="form-label" for="gth-field-user_id">Email</label>' in main
    assert "It takes a minute." in main and "We never share it." in main
    assert "Already have an account?" not in main  # no login_url
    footer = html.split('<footer class="gth-auth-footer">')[1].split("</footer>")[0]
    assert '<a href="/terms">Terms</a>' in footer and "javascript:" not in footer


def test_page_is_a_well_formed_document():
    html5lib.HTMLParser(strict=True).parse(
        _render(user_id="bob", brand=LOGO, show_theme_toggle=True,
                errors={"user_id": ["Taken."], "__all__": ["Nope."]},
                register_links=[{"label": "Terms", "url": "/terms"}]))
