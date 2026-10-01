"""settings_page.html / settings_section.html — the ready-made settings page
a service (or greentechhub-fastapi's SettingsViews) renders with data only."""

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui

THEME = {"key": "ui.theme", "type": "choice", "label": "Theme", "default": "system",
         "group": "Appearance", "choices": [("light", "Light"), ("dark", "Dark"),
                                            ("system", "System")]}
PAGE_SIZE = {"key": "ui.page_size", "type": "int", "label": "Rows per page", "default": 25,
             "min": 5, "max": 200, "group": "Tables"}
BANNER = {"key": "site.banner", "type": "str", "label": "Maintenance banner", "default": ""}


def _env() -> Environment:
    env = Environment(loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _section(**overrides) -> dict:
    section = {"id": "preferences", "title": "Preferences", "settings": [THEME, PAGE_SIZE],
               "values": {"ui.theme": "dark"}, "action": "/settings/preferences"}
    return section | overrides


def _render_section(**overrides) -> str:
    return _env().get_template("settings_section.html").render(section=_section(**overrides))


def test_page_renders_every_section_with_default_htmx_wiring():
    html = _env().get_template("settings_page.html").render(
        page_title="Settings", settings_intro="Change how things look.",
        settings_sections=[
            _section(),
            {"id": "app", "title": "App", "settings": [BANNER], "action": "/settings/app"},
        ],
    )
    assert "<h1" in html and "Settings" in html
    assert "Change how things look." in html
    for sid, action in (("preferences", "/settings/preferences"), ("app", "/settings/app")):
        assert f'id="gth-settings-{sid}"' in html
        assert f'hx-post="{action}"' in html
        assert f'hx-target="#gth-settings-{sid}"' in html
    assert 'hx-swap="outerHTML"' in html


def test_values_are_read_by_key_not_the_dict_method():
    html = _render_section()
    assert 'gth-field-ui.theme-2" autocomplete="off" checked' in html


def test_a_section_without_values_uses_the_defaults():
    html = _render_section(values=None)
    assert 'gth-field-ui.theme-3" autocomplete="off" checked' in html  # default "system"
    section = _section()
    del section["values"]
    html = _env().get_template("settings_section.html").render(section=section)
    assert 'gth-field-ui.theme-3" autocomplete="off" checked' in html


def test_explicit_form_attrs_win():
    html = _render_section(form_attrs={"hx-post": "/elsewhere", "hx-target": "body"})
    assert 'hx-post="/elsewhere"' in html
    assert 'hx-target="body"' in html
    assert 'hx-swap="outerHTML"' not in html


def test_errors_and_banner_render_in_the_fragment():
    html = _render_section(values={"ui.page_size": "500"},
                           errors={"ui.page_size": ["Must be between 5 and 200."]},
                           error="Check the highlighted fields.")
    assert "Must be between 5 and 200." in html
    assert "is-invalid" in html
    assert "Check the highlighted fields." in html


def test_section_without_action_has_no_form():
    html = _render_section(action=None)
    assert "<form" not in html
    assert "hx-post" not in html


def test_empty_page_renders():
    html = _env().get_template("settings_page.html").render(page_title="Settings")
    assert "gth-settings-section" not in html


def test_settings_section_snapshot():
    assert_snapshot(_render_section(description="Only you see these."), "settings_section_template")
