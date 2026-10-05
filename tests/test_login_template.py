"""login_page.html — the ready-made local-auth sign-in page on app.html's
layout="auth", rendered with the context greentechhub-fastapi's LoginViews
passes."""

import html5lib
from test_app_shell_renders import _context, _env

LOGO = {"name": "GreenTechHub", "service_name": "PyFinBot", "favicon_url": None,
        "logo_url": "/gth-assets/logo-dark.png", "logo_light_url": "/gth-assets/logo-light.png"}


def _render(**context) -> str:
    return _env().get_template("login_page.html").render(**_context(**context))


def _main(html: str) -> str:
    return html.split("<main")[1].split("</main>")[0]


def _footer(html: str) -> str:
    return html.split('<footer class="gth-auth-footer">')[1].split("</footer>")[0]


def test_auth_layout_has_no_app_navbar():
    html = _render()
    assert '<main class="gth-auth">' in html
    assert "gth-navbar" not in html and "/watchlist" not in html  # no nav items
    assert "gth-command" not in html


def test_bare_page_posts_user_id_and_password_to_login():
    main = _main(_render())
    assert '<form method="post" action="/login" class="gth-form">' in main
    assert "novalidate" not in main  # empty fields stop in the browser
    assert 'name="user_id"' in main and 'autocomplete="username"' in main
    assert 'name="password"' in main and 'type="password"' in main
    assert 'autocomplete="current-password"' in main
    assert main.count('required="required"') == 2
    assert 'autocomplete="username" autofocus="autofocus"' in main
    assert ('<h1 class="h4 mb-1">Sign in '
            '<span class="text-secondary fw-normal">to Playground</span></h1>') in main
    assert "gth-toast" not in main  # no error, no alert


def test_error_is_an_inline_danger_alert_and_escaped():
    main = _main(_render(error="Incorrect <user> ID or password", user_id='bob"&co'))
    assert 'gth-toast-inline gth-toast-danger gth-toast-surface mb-3"\n  role="alert"' in main
    assert "Incorrect &lt;user&gt; ID or password" in main
    assert 'value="bob&#34;&amp;co"' in main  # the prefill, escaped
    # With the user ID filled in, typing starts at the password.
    assert 'autocomplete="current-password" autofocus="autofocus"' in main
    assert 'autocomplete="username" autofocus' not in main


def test_brand_header_without_a_logo_shows_the_mark():
    main = _main(_render())
    assert ('<span class="gth-auth-mark" aria-hidden="true">'
            '<i class="bi bi-shield-lock"></i></span>') in main
    assert '<div class="gth-auth-brand-name">GreenTechHub</div>' in main
    assert '<div class="gth-auth-service">Playground</div>' in main


def test_brand_header_swaps_logos_per_colour_mode():
    main = _main(_render(brand=LOGO))
    for variant, mode in (("dark", "on-dark"), ("light", "on-light")):
        assert (f'src="/gth-assets/logo-{variant}.png" alt="" height="56" '
                f'class="gth-auth-logo gth-logo-{mode}"') in main
    assert "gth-auth-mark" not in main
    assert "to PyFinBot</span>" in main


def test_options_and_footer_links():
    html = _render(login_url="/auth/login", login_title="Log in", user_id_label="Email",
                   login_subtitle="Use your work account.", login_help="No account? Ask an admin.",
                   login_links=[{"label": "Help", "url": "/help"},
                                {"label": "Privacy", "url": "https://example.com/privacy"},
                                {"label": "Bad", "url": "javascript:alert(1)"}])
    main = _main(html)
    assert 'action="/auth/login"' in main
    assert ">Log in <span" in main and "</i> Log in\n" in main
    assert '<label class="form-label" for="gth-field-user_id">Email</label>' in main
    assert "Use your work account." in main and "No account? Ask an admin." in main
    footer = _footer(html)
    assert "GreenTechHub &middot; Playground" in footer
    assert '<a href="/help">Help</a>' in footer
    assert '<a href="https://example.com/privacy">Privacy</a>' in footer
    assert "javascript:" not in footer and "Bad" not in footer


def test_theme_toggle_only_when_the_shell_has_one():
    assert "gth-auth-corner" not in _render()
    assert '<div class="gth-auth-corner">' in _render(show_theme_toggle=True)


def test_page_is_a_well_formed_document():
    html5lib.HTMLParser(strict=True).parse(
        _render(error="Nope", user_id="bob", brand=LOGO, show_theme_toggle=True,
                login_links=[{"label": "Help", "url": "/help"}]))


def test_register_url_adds_a_create_account_link():
    assert "gth-auth-switch" not in _render()
    main = _main(_render(register_url="/register"))
    assert 'No account? <a href="/register">Create one</a>' in main
    html5lib.HTMLParser(strict=True).parse(_render(register_url="/register", login_help="Hi"))


def test_forgot_password_link_only_when_offered():
    assert "Forgot password?" not in _render()
    main = _main(_render(forgot_password_url="/forgot-password"))
    assert '<a href="/forgot-password">Forgot password?</a>' in main


def test_a_refusal_can_offer_the_confirmation_link_again():
    plain = _main(_render(error="Incorrect user ID or password"))
    assert "Send the link again" not in plain
    refused = _main(_render(error="Confirm your email address first.",
                            verify_resend_url="/verify-email/resend"))
    assert "Confirm your email address first." in refused
    action = '<a class="gth-toast-action" href="/verify-email/resend">Send the link again</a>'
    assert action in refused
