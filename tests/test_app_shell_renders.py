from jinja2 import ChoiceLoader, Environment, FileSystemLoader

import greentechhub_ui
from greentechhub_ui.theme import brand_context


def _env() -> Environment:
    return Environment(
        loader=ChoiceLoader(
            [
                FileSystemLoader(greentechhub_ui.templates_path),
                FileSystemLoader(greentechhub_ui.components_path),
            ]
        )
    )


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


def test_app_shell_renders_without_error():
    html = _env().get_template("app.html").render(**_context())
    assert "<nav" in html
    assert "GreenTechHub" in html
    assert "Playground" in html


def test_app_shell_renders_nav_items():
    html = _env().get_template("app.html").render(**_context())
    assert "Watchlist" in html
    assert 'href="/watchlist"' in html


def test_app_shell_has_toast_container():
    html = _env().get_template("app.html").render(**_context())
    assert 'id="gth-toast-container"' in html


def test_app_shell_has_anti_fouc_script_and_no_toggle_by_default():
    html = _env().get_template("app.html").render(**_context())
    assert "gth-theme-mode" in html
    # show_theme_toggle defaults to False — no toggle button unless opted in
    assert "gth-theme-toggle" not in html


def test_app_shell_renders_theme_toggle_when_enabled():
    context = _context(show_theme_toggle=True)
    html = _env().get_template("app.html").render(**context)
    assert "gth-theme-toggle" in html


def test_app_shell_renders_extra_head_list():
    context = _context(extra_head=['<meta name="gth-extra-head-demo" content="works">'])
    html = _env().get_template("app.html").render(**context)
    assert '<meta name="gth-extra-head-demo" content="works">' in html


def test_app_shell_renders_extra_css_urls():
    context = _context(extra_css=["https://example.com/custom.css"])
    html = _env().get_template("app.html").render(**context)
    assert '<link rel="stylesheet" href="https://example.com/custom.css">' in html


def test_app_shell_renders_extra_js_urls():
    context = _context(extra_js=["https://example.com/custom.js"])
    html = _env().get_template("app.html").render(**context)
    assert '<script src="https://example.com/custom.js"></script>' in html


def test_app_shell_accepts_populated_flashes():
    # Contract test (docs/testing.md): a consumer supplying a non-empty
    # `flashes` list must not break rendering, even though app.html doesn't
    # render it itself (that's gth_toast_flashes's job) — catches an
    # accidental new required key, which would be a breaking contract change.
    context = _context(flashes=[{"message": "Saved", "kind": "success"}])
    html = _env().get_template("app.html").render(**context)
    assert "<nav" in html
