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


def test_app_shell_has_modal_host():
    html = _env().get_template("app.html").render(**_context())
    assert 'id="gth-modal-host"' in html


def test_app_shell_optional_component_scripts():
    html = _env().get_template("app.html").render(**_context())
    assert "modal-host.js" not in html and "combobox.js" not in html

    html = _env().get_template("app.html").render(**_context(
        modal_host_js_url="/a/js/modal-host.js", combobox_js_url="/a/js/combobox.js",
    ))
    assert '<script src="/a/js/modal-host.js"></script>' in html
    assert '<script src="/a/js/combobox.js"></script>' in html


def test_app_shell_navbar_follows_color_mode_unless_pinned():
    html = _env().get_template("app.html").render(**_context())
    assert "bg-body-tertiary" in html and "navbar-dark" not in html

    html = _env().get_template("app.html").render(**_context(navbar_theme="dark"))
    pinned = 'navbar-expand-md bg-dark border-bottom gth-navbar" data-bs-theme="dark">'
    assert pinned in html


def test_app_shell_sidebar_layout():
    html = _env().get_template("app.html").render(**_context(
        layout="sidebar", sidebar_js_url="/a/js/sidebar.js",
    ))
    assert 'id="gth-sidebar"' in html and "offcanvas-lg" in html
    assert '<main class="gth-main">' in html
    assert '<script src="/a/js/sidebar.js"></script>' in html
    assert "gth-sidebar-mode" in html  # rail anti-FOUC


def test_app_shell_navbar_layout_ignores_sidebar_bits():
    html = _env().get_template("app.html").render(**_context(sidebar_js_url="/a/js/sidebar.js"))
    assert "gth-sidebar" not in html and "sidebar.js" not in html
    assert '<main class="container py-4">' in html
