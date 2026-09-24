"""Proves the framework-agnostic template contract (docs/contract.md) holds
from Django, not just FastAPI: app.html and the gth-* macros render the same
way through django.template.backends.jinja2.Jinja2 as they do through a plain
jinja2.Environment (see tests/test_app_shell_renders.py, whose minimal
contract context this mirrors).
"""

import pytest

django = pytest.importorskip("django")

from django.conf import settings  # noqa: E402

import greentechhub_ui  # noqa: E402
from greentechhub_ui.theme import brand_context  # noqa: E402

if not settings.configured:
    settings.configure(
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.jinja2.Jinja2",
                "DIRS": [str(greentechhub_ui.templates_path), str(greentechhub_ui.components_path)],
                "APP_DIRS": False,
                "OPTIONS": {},
            }
        ],
    )
    django.setup()

from django.template.loader import get_template  # noqa: E402


def _context(**overrides) -> dict:
    context = {
        "nav_items": [
            {"label": "Deals", "url": "/"},
            {"label": "Watchlist", "url": "/watchlist"},
        ],
        "current_user": None,
        "flashes": [],
        "url_for": lambda name, **kwargs: "/",
        "brand": brand_context(service_name="Playground"),
        "extra_head": [],
    }
    context.update(overrides)
    return context


def test_app_shell_renders_via_django_jinja2_backend():
    html = get_template("app.html").render(_context())
    assert "<nav" in html
    assert "GreenTechHub" in html


def test_app_shell_renders_nav_items_via_django_jinja2_backend():
    html = get_template("app.html").render(_context())
    assert "Watchlist" in html
    assert 'href="/watchlist"' in html


def test_app_shell_has_toast_container_via_django_jinja2_backend():
    html = get_template("app.html").render(_context())
    assert 'id="gth-toast-container"' in html


def _gth_environment(**options):
    """A Django Jinja2 `environment` callable, as a consumer would write it."""
    from jinja2 import Environment

    return greentechhub_ui.install(
        Environment(**options), service_name="Django app",
        nav_items=[{"label": "Home", "url": "/"}, {"label": "Parts", "url": "/parts"}],
        layout="sidebar",
    )


def test_install_and_template_dirs_via_djangos_environment_option():
    from django.template.backends.jinja2 import Jinja2

    engine = Jinja2({
        "NAME": "gth-install",
        "DIRS": [str(d) for d in greentechhub_ui.template_dirs()],
        "APP_DIRS": False,
        "OPTIONS": {"environment": f"{__name__}._gth_environment"},
    })
    html = engine.get_template("app.html").render({
        "current_user": None, "flashes": [], "url_for": lambda *a, **k: "/",
        "current_path": "/parts",
    })
    assert 'id="gth-sidebar"' in html  # shell globals installed (layout="sidebar")
    assert 'aria-current="page"' in html and "Parts" in html
    assert "/gth-assets/js/sidebar.js" in html  # asset URLs from the shared prefixes


def test_static_dirs_as_prefixed_staticfiles_dirs():
    dirs = [(prefix.strip("/"), str(path))
            for prefix, path in greentechhub_ui.static_dirs().items()]
    assert dirs[0][0] == "gth-assets" and dirs[1][0] == "gth-static"
