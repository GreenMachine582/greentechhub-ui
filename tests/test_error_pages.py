"""403.html / 404.html / 500.html on error_page.html: they render with
nothing but install()'s globals (Django's default 500 handler passes no
context), and take the optional context a FastAPI handler passes."""

import html5lib
import pytest
from jinja2 import Environment

import greentechhub_ui

NAV = [{"label": "Home", "url": "/"}, {"label": "Reports", "url": "/reports"}]


def _env() -> Environment:
    return greentechhub_ui.install(Environment(autoescape=True), service_name="Svc", nav_items=NAV)


def _render(name: str, **context) -> str:
    return _env().get_template(name).render(**context)


def _main(html: str) -> str:
    return html[html.index("<main"):html.index("</main>")]


@pytest.mark.parametrize("name, code, title, message", [
    ("403.html", "403", "Access denied", "You don&#39;t have access to this page."),
    ("404.html", "404", "Page not found", "There&#39;s no page at this address."),
    ("500.html", "500", "Something went wrong", "Something went wrong on our side."),
])
def test_renders_with_an_empty_context(name, code, title, message):
    html = _render(name)
    html5lib.HTMLParser(strict=True).parse(html)
    main = _main(html)
    assert f'<p class="gth-error-page-code" aria-hidden="true">{code}</p>' in main
    assert f'<h1 class="gth-page-header-title">{title}</h1>' in main
    assert f'<p class="lead mb-2">{message}</p>' in main
    assert '<a class="btn btn-primary" href="/">Go to the home page</a>' in main
    assert f"<title>Svc {title}</title>" in html
    assert "<nav" in html  # the service's own shell, not a bare page


def test_messages_and_home_url_can_be_overridden():
    main = _main(_render("404.html", error_message="No such stock.",
                         error_detail="Check the symbol.", home_url="/stocks"))
    assert '<p class="lead mb-2">No such stock.</p>' in main
    assert '<p class="text-secondary">Check the symbol.</p>' in main
    assert 'href="/stocks">Go to the home page' in main


def test_reference_is_shown_when_given():
    assert "Reference" not in _main(_render("500.html"))
    main = _main(_render("500.html", error_reference="req-123"))
    assert '<code class="user-select-all">req-123</code>' in main


def test_500_offers_a_retry_of_the_failed_path():
    main = _main(_render("500.html", current_path="/reports"))
    assert '<a class="btn btn-outline-secondary" href="/reports">Try again</a>' in main
    assert main.index("Try again") < main.index("Go to the home page")


def test_403_signed_out_with_a_login_url_offers_sign_in():
    main = _main(_render("403.html", login_url="/login", current_path="/reports/gains"))
    assert 'href="/login?next=/reports/gains">Sign in</a>' in main
    assert "You may need to sign in first." in main


def test_403_signed_in_asks_for_access_instead():
    main = _main(_render("403.html", login_url="/login", current_user={"username": "ann"}))
    assert "Sign in" not in main
    assert "Ask an admin for access if you need it." in main


def test_values_are_escaped():
    main = _main(_render("500.html", error_reference="<b>x</b>", current_path='/a"b',
                         home_url='/"x'))
    assert "<b>x</b>" not in main and "&lt;b&gt;x&lt;/b&gt;" in main
    assert 'href="/a&#34;b"' in main and 'href="/&#34;x"' in main


# Django: its default handlers (django.views.defaults) render 403.html,
# 404.html and 500.html through the configured Jinja2 engine; with install()
# in that engine's environment callable they get the brand and nav.

django = pytest.importorskip("django")


def _django_environment(**options):
    return greentechhub_ui.install(Environment(**options), service_name="Svc", nav_items=NAV)


def _django_engine():
    from django.conf import settings
    from django.template.backends.jinja2 import Jinja2

    if not settings.configured:  # as test_contract_django does, whichever runs first
        settings.configure(TEMPLATES=[{
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "DIRS": [str(greentechhub_ui.templates_path), str(greentechhub_ui.components_path)],
            "APP_DIRS": False, "OPTIONS": {}}])
        django.setup()
    return Jinja2({"NAME": "gth-errors", "DIRS": [], "APP_DIRS": False,
                   "OPTIONS": {"environment": "test_error_pages._django_environment"}})


@pytest.mark.parametrize("name, context", [
    ("404.html", {"request_path": "/missing", "exception": "Resolver404"}),  # page_not_found's
    ("403.html", {"exception": "PermissionDenied"}),                       # permission_denied's
    ("500.html", {}),                                                        # server_error's: none
])
def test_renders_through_djangos_jinja2_backend(name, context):
    html = _django_engine().get_template(name).render(context)
    assert '<p class="gth-error-page-code" aria-hidden="true">' + name[:3] + "</p>" in html
    assert "<nav" in html
