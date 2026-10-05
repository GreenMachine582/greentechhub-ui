"""The password reset and email verification pages, on app.html's
layout="auth", rendered with the contexts greentechhub-fastapi's
PasswordResetViews and EmailVerificationViews pass."""

import html5lib
from test_app_shell_renders import _context, _env


def _render(template, **context) -> str:
    return _env().get_template(template).render(**_context(**context))


def _main(html: str) -> str:
    return html.split("<main")[1].split("</main>")[0]


def _valid(html: str) -> None:
    html5lib.HTMLParser(strict=True).parse(html)


FORGOT = {"forgot_url": "/forgot-password", "login_url": "/login"}
RESET = {"action": "/reset-password/tok", "login_url": "/login", "min_password_length": 8}
RESEND = {"resend_url": "/verify-email/resend", "login_url": "/login"}


# ── forgot password ────────────────────────────────────────────────────────


def test_the_forgot_form_posts_an_identifier():
    html = _render("forgot_password_page.html", **FORGOT)
    _valid(html)
    main = _main(html)
    assert '<main class="gth-auth">' in html and "gth-navbar" not in html
    assert ('<h1 class="h4 mb-1">Reset your password '
            '<span class="text-secondary fw-normal">to Playground</span></h1>') in main
    assert '<form method="post" action="/forgot-password" class="gth-form">' in main
    assert 'name="identifier"' in main and 'autocomplete="username"' in main
    assert '<a href="/login">Back to sign in</a>' in main


def test_after_a_request_it_says_check_your_email_whoever_asked():
    main = _main(_render("forgot_password_page.html", sent=True, identifier="<alice>", **FORGOT))
    assert "Check your email" in main and "If an account matches &lt;alice&gt;" in main
    assert "<alice>" not in main
    assert "<form" not in main


def test_errors_show_under_the_field_with_the_value_kept():
    main = _main(_render("forgot_password_page.html", identifier="al",
                         errors={"identifier": ["Too many reset requests."]}, **FORGOT))
    assert "Too many reset requests." in main and 'value="al"' in main


# ── choose a new password ──────────────────────────────────────────────────


def test_the_reset_form_posts_both_passwords_to_the_link():
    html = _render("reset_password_page.html", **RESET)
    _valid(html)
    main = _main(html)
    assert '<form method="post" action="/reset-password/tok" class="gth-form">' in main
    assert 'name="password"' in main and 'name="password_confirm"' in main
    assert main.count('autocomplete="new-password"') == 2 and 'minlength="8"' in main
    assert "At least 8 characters." in main


def test_a_refused_password_shows_its_field_error():
    main = _main(_render("reset_password_page.html",
                         errors={"password_confirm": ["The passwords don't match."]}, **RESET))
    assert "The passwords don&#39;t match." in main or "The passwords don't match." in main
    assert 'id="gth-field-password_confirm-error"' in main


def test_done_and_invalid_offer_the_next_step():
    done = _main(_render("reset_password_page.html", done=True, **RESET))
    assert "Your password has been changed." in done and 'href="/login"' in done
    assert "<form" not in done
    invalid = _main(_render("reset_password_page.html", invalid=True,
                            forgot_url="/forgot-password", **RESET))
    assert "expired or was already used" in invalid and 'href="/forgot-password"' in invalid
    assert "<form" not in invalid


# ── email verification ─────────────────────────────────────────────────────


def test_the_link_page_confirms_or_offers_a_new_link():
    done = _render("verify_email_page.html", done=True, login_url="/login")
    _valid(done)
    assert "Your email address is confirmed." in _main(done) and 'href="/login"' in done
    invalid = _main(_render("verify_email_page.html", invalid=True, login_url="/login",
                            resend_url="/verify-email/resend"))
    assert "expired or was already used" in invalid
    assert 'href="/verify-email/resend"' in invalid and "confirmed." not in invalid


def test_the_resend_form_and_its_answer():
    html = _render("verify_email_resend_page.html", **RESEND)
    _valid(html)
    main = _main(html)
    assert '<form method="post" action="/verify-email/resend" class="gth-form">' in main
    assert "Send the link again" in main
    sent = _main(_render("verify_email_resend_page.html", sent=True, identifier="newbie", **RESEND))
    assert "If an account matches newbie and still needs confirming" in sent and "<form" not in sent
