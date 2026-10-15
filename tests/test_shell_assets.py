"""app.html's Bootstrap and htmx assets (v0.19): no public-CDN fallback. With
the globals unset (no install()/shell_globals()), the shell still renders —
error pages and Django's default 500 handler pass no context — but points
nowhere off-origin, and says in an HTML comment what's missing."""

import re

from jinja2 import Environment
from test_app_shell_renders import _context, _env

import greentechhub_ui
from greentechhub_ui import shell_globals

ASSET_GLOBALS = ("bootstrap_css_url", "htmx_js_url", "bootstrap_js_url")


def _off_origin(html: str) -> list[str]:
    return re.findall(r'(?:href|src)="(https?://[^"]+)"', html)


def test_unset_asset_globals_render_no_cdn_tags_but_say_what_is_missing():
    html = _env().get_template("app.html").render(**_context())
    assert "jsdelivr" not in html and "unpkg" not in html
    assert _off_origin(html) == []
    assert not re.search(r'<link[^>]*bootstrap', html)
    assert not re.search(r'<script src="[^"]*(?:htmx|bootstrap)', html)
    for name in ASSET_GLOBALS:
        assert (f"<!-- gth-ui: {name} is unset; mount greentechhub_ui.static_dirs() and use "
                "install() / shell_globals() -->") in html


def test_shell_globals_point_every_asset_at_the_vendored_copies():
    globals_ = shell_globals(service_name="Svc", nav_items=[])
    html = _env().get_template("app.html").render(**_context(**globals_))
    assert f'<link rel="stylesheet" href="{globals_["bootstrap_css_url"]}">' in html
    assert f'<script src="{globals_["htmx_js_url"]}"' in html
    assert f'<script src="{globals_["bootstrap_js_url"]}"' in html
    assert "gth-ui: " not in html
    assert _off_origin(html) == []


def test_install_with_shell_kwargs_sets_them():
    env = greentechhub_ui.install(Environment(), service_name="Svc", nav_items=[])
    html = env.get_template("app.html").render(current_user=None, flashes=[], extra_head=[],
                                               url_for=lambda name, **kw: "/")
    for name in ASSET_GLOBALS:
        assert env.globals[name].startswith("/gth-assets/")
        assert f"{name} is unset" not in html
