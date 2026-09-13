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
