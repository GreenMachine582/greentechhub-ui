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
    assert "modal-host.js" not in html and "combobox.js" not in html and "date-range.js" not in html

    html = _env().get_template("app.html").render(**_context(
        modal_host_js_url="/a/js/modal-host.js", combobox_js_url="/a/js/combobox.js",
        date_range_js_url="/a/js/date-range.js", file_drop_js_url="/a/js/file-drop.js",
        table_select_js_url="/a/js/table-select.js", table_view_js_url="/a/js/table-view.js",
        char_counter_js_url="/a/js/char-counter.js",
    ))
    assert '<script src="/a/js/char-counter.js"></script>' in html
    assert '<script src="/a/js/table-view.js"></script>' in html
    assert '<script src="/a/js/table-select.js"></script>' in html
    assert '<script src="/a/js/date-range.js"></script>' in html
    assert '<script src="/a/js/file-drop.js"></script>' in html
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


def test_app_shell_command_palette_inclusion():
    palette = {"command_palette_js_url": "/a/js/command-palette.js"}
    assert "gth-command" not in _env().get_template("app.html").render(**_context(**palette))
    html = _env().get_template("app.html").render(**_context(**palette, show_command_palette=True))
    assert "<dialog" in html and "data-gth-command-open" in html
    html = _env().get_template("app.html").render(**_context(**palette, layout="sidebar"))
    assert "<dialog" in html and "data-gth-command-open" in html


def test_app_shell_back_to_top_only_when_configured():
    assert "gth-back-to-top" not in _env().get_template("app.html").render(**_context())
    html = _env().get_template("app.html").render(**_context(back_to_top_js_url="/a/js/b.js"))
    assert "data-gth-back-to-top" in html and '<script src="/a/js/b.js"></script>' in html


def _render_shell(**overrides) -> str:
    return _env().get_template("app.html").render(**_context(**overrides))


def test_app_shell_without_theme_keys_keeps_the_local_only_behaviour():
    html = _render_shell()
    assert "var server = null;" in html
    assert "data-gth-theme-save-url" not in html
    assert '<html lang="en" data-bs-theme="dark">' in html


def test_app_shell_seeds_the_anti_fouc_script_from_theme_mode():
    html = _render_shell(theme_mode="light")
    assert 'var server = "light";' in html


def test_app_shell_renders_the_theme_save_url_on_html():
    html = _render_shell(theme_save_url="/settings/theme")
    assert '<html lang="en" data-bs-theme="dark" data-gth-theme-save-url="/settings/theme">' in html


def test_app_shell_theme_mode_cannot_break_out_of_the_script():
    html = _render_shell(theme_mode='</script><script>alert(1)</script>')
    assert "<script>alert(1)" not in html
    assert "\\u003c/script\\u003e" in html


def test_app_shell_escapes_the_theme_save_url():
    html = _render_shell(theme_save_url='/x" onload="alert(1)')
    assert 'onload="alert(1)"' not in html


# ── v0.12: per-request permission filtering + user menu ───────────────────

def _installed_env(layout="navbar"):
    env = _env()
    greentechhub_ui.install(env, service_name="Playground", layout=layout, nav_items=[
        {"label": "Deals", "url": "/"},
        {"label": "Admin", "url": "/admin", "required_permission": "settings.manage"},
    ])
    return env


def _render_installed(layout="navbar", **context):
    base = {"flashes": [], "url_for": lambda name, **kwargs: "/", "extra_head": []}
    return _installed_env(layout).get_template("app.html").render(**base, **context)


def test_permissioned_nav_item_follows_granted_per_request():
    for layout in ("navbar", "sidebar"):
        allowed = _render_installed(layout, current_user={"username": "alice"},
                                    granted={"settings.manage"})
        denied = _render_installed(layout, current_user={"username": "bob"}, granted=set())
        anonymous = _render_installed(layout)
        assert 'href="/admin"' in allowed, layout
        assert 'href="/admin"' not in denied, layout
        assert 'href="/admin"' not in anonymous, layout


def test_permissioned_item_is_left_out_of_the_command_palette_index():
    denied = _render_installed("sidebar", current_user={"username": "bob"}, granted=set())
    allowed = _render_installed("sidebar", current_user={"username": "a"},
                                granted={"settings.manage"})
    assert "/admin" not in denied
    assert allowed.count("/admin") > denied.count("/admin")


def test_signed_in_without_granted_keeps_old_behaviour():
    html = _render_installed(current_user={"username": "alice"})
    assert 'href="/admin"' in html


def test_user_menu_renders_only_when_signed_in():
    signed_in = _render_installed(current_user={"username": "alice"}, logout_url="/logout",
                                  user_menu_items=[{"label": "Settings", "url": "/settings"}])
    assert "gth-user-menu" in signed_in
    assert ">alice<" in signed_in
    assert 'action="/logout"' in signed_in
    assert 'href="/settings"' in signed_in
    assert "gth-user-menu" not in _render_installed()


def test_user_menu_items_are_permission_filtered():
    html = _render_installed(
        current_user={"username": "bob"}, granted=set(),
        user_menu_items=[
            {"label": "Settings", "url": "/settings"},
            {"label": "Roles", "url": "/roles", "required_permission": "users.manage"},
        ],
    )
    assert 'href="/settings"' in html
    assert 'href="/roles"' not in html
