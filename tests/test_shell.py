from pathlib import Path

import greentechhub_ui
from greentechhub_ui import shell_globals

NAV = [{"label": "Home", "url": "/"}]


def test_every_asset_points_at_the_vendored_copies():
    g = shell_globals(service_name="Svc", nav_items=NAV)
    assert g["nav_items"] is NAV
    assert g["brand"]["service_name"] == "Svc"
    assert g["theme_css_url"] == "/gth-static/theme.css"
    assert g["htmx_js_url"] == "/gth-assets/js/htmx.min.js"
    assert g["bootstrap_css_url"] == "/gth-assets/css/bootstrap.min.css"
    assert g["show_theme_toggle"] is True
    assert g["theme_toggle_js_url"] == "/gth-assets/js/theme-toggle.js"


def test_every_asset_url_exists_in_the_package():
    g = shell_globals(service_name="Svc", nav_items=NAV)
    roots = {
        "/gth-assets/": greentechhub_ui.static_path,
        "/gth-static/": greentechhub_ui.theme_path,
    }
    urls = [v for k, v in g.items() if k.endswith("_url") and isinstance(v, str)]
    assert urls
    for url in urls:
        prefix = next(p for p in roots if url.startswith(p))
        assert (Path(roots[prefix]) / url[len(prefix):]).is_file(), url


def test_custom_prefixes_and_no_theme_toggle():
    g = shell_globals(service_name="Svc", nav_items=NAV, assets_prefix="/static/gth",
                      theme_prefix="/static/theme", theme_toggle=False, show_logo=True)
    assert g["toast_js_url"] == "/static/gth/js/toast.js"
    assert g["theme_css_url"] == "/static/theme/theme.css"
    assert g["show_theme_toggle"] is False
    assert "theme_toggle_js_url" not in g
    assert g["brand"]["logo_url"].startswith("/static/gth/")
