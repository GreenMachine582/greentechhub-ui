"""shell_globals — the app.html context contract's shell globals in one call.

Every FastAPI consumer (BottleBot, PyFinBot, this repo's playground) was
setting the same ~10 `templates.env.globals[...]` lines by hand: brand,
nav_items, and one URL per vendored asset. This builds them from the two
mount prefixes a consumer already chose when mounting `static_path` and
`theme_path` (see docs/contract.md), pointing every asset at the vendored
copy rather than app.html's CDN fallbacks:

    templates.env.globals.update(greentechhub_ui.shell_globals(
        service_name="PyFinBot",
        nav_items=greentechhub_ui.navigation.build_nav_items(custom_items=[...]),
    ))

The consumer still mounts the directories itself — this only knows the
prefixes, it doesn't own the app.
"""

from functools import partial

from greentechhub_ui import navigation
from greentechhub_ui.theme import brand_context


def shell_globals(
    *,
    service_name: str,
    nav_items: list,
    assets_prefix: str = "/gth-assets",
    theme_prefix: str = "/gth-static",
    theme_toggle: bool = True,
    show_logo: bool = False,
    navbar_theme: str | None = None,
    layout: str = "navbar",
) -> dict:
    """Globals for app.html: brand, nav_items, and every asset URL.

    `assets_prefix` is where `greentechhub_ui.static_path` is mounted,
    `theme_prefix` where `greentechhub_ui.theme_path` is. `navbar_theme="dark"`
    pins gth_navbar dark; by default it follows the color mode.
    `layout="sidebar"` moves nav_items into gth_sidebar (see app.html).

    Also installs two nav helpers as globals: `nav_breadcrumbs(path)` (the
    gth_page_header breadcrumbs derived from nav_items) and
    `nav_mark_active(items, path)` (used by gth_sidebar).
    """
    if layout not in ("navbar", "sidebar"):
        raise ValueError(f"layout must be 'navbar' or 'sidebar', got {layout!r}")
    globals_ = {
        "brand": brand_context(
            service_name=service_name, show_logo=show_logo, static_url_prefix=assets_prefix
        ),
        "nav_items": nav_items,
        "theme_css_url": f"{theme_prefix}/theme.css",
        "icons_css_url": f"{assets_prefix}/icons/bootstrap-icons.min.css",
        "bootstrap_css_url": f"{assets_prefix}/css/bootstrap.min.css",
        "bootstrap_js_url": f"{assets_prefix}/js/bootstrap.bundle.min.js",
        "htmx_js_url": f"{assets_prefix}/js/htmx.min.js",
        "toast_js_url": f"{assets_prefix}/js/toast.js",
        "modal_host_js_url": f"{assets_prefix}/js/modal-host.js",
        "combobox_js_url": f"{assets_prefix}/js/combobox.js",
        "record_picker_js_url": f"{assets_prefix}/js/record-picker.js",
        "sidebar_js_url": f"{assets_prefix}/js/sidebar.js",
        "command_palette_js_url": f"{assets_prefix}/js/command-palette.js",
        "tree_js_url": f"{assets_prefix}/js/tree.js",
        "show_theme_toggle": theme_toggle,
        "navbar_theme": navbar_theme,
        "layout": layout,
        "nav_breadcrumbs": partial(navigation.breadcrumbs_for, nav_items),
        "nav_mark_active": navigation.mark_active,
        "nav_flatten": navigation.flatten,
    }
    if theme_toggle:
        globals_["theme_toggle_js_url"] = f"{assets_prefix}/js/theme-toggle.js"
    return globals_
