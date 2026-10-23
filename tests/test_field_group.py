"""gth_field_group (field_group.html): a fieldset of form fields with its
title as the legend — and where it's used: gth_settings_section's
setting.group, and the API tokens section's "New token" form."""

import re

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui

IMPORT = '{% from "field_group.html" import gth_field_group %}'


def _env() -> Environment:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _render(source: str, **context) -> str:
    return _env().from_string(IMPORT + source).render(**context)


def test_a_titled_described_group():
    html = _render('{% call gth_field_group("Delivery", description="Where it goes.",'
                   ' id="delivery") %}<input name="email">{% endcall %}')
    assert_snapshot(html, "field_group")
    assert ('<fieldset class="gth-field-group" id="delivery"'
            ' aria-describedby="delivery-description">') in html
    assert '<legend class="gth-field-group-legend h6 text-secondary mb-2">Delivery</legend>' in html
    assert 'id="delivery-description">Where it goes.</p>' in html
    order = [html.index(s) for s in ("</legend>", "Where it goes.", '<input name="email">')]
    assert order == sorted(order)


def test_description_without_an_id_is_not_referenced():
    html = _render('{% call gth_field_group("Delivery", description="Hint") %}x{% endcall %}')
    assert "aria-describedby" not in html and " id=" not in html
    assert "Hint" in html


def test_untitled_group_has_no_legend_and_classes_append():
    html = _render('{% call gth_field_group(group_class="mb-0") %}x{% endcall %}')
    assert '<fieldset class="gth-field-group mb-0">' in html
    assert "<legend" not in html


def test_title_and_description_are_escaped():
    html = _render('{% call gth_field_group(title, description=title) %}x{% endcall %}',
                   title="<b>Bold</b>")
    assert "<b>" not in html and html.count("&lt;b&gt;Bold&lt;/b&gt;") == 2


SETTINGS = [
    {"key": "site.banner", "type": "str", "label": "Banner", "default": ""},
    {"key": "ui.theme", "type": "choice", "label": "Theme", "default": "system",
     "group": "Appearance", "choices": [("light", "Light"), ("dark", "Dark")]},
    {"key": "ui.page_size", "type": "int", "label": "Rows", "default": 25, "group": "Tables"},
]


def test_settings_groups_are_fieldsets_and_ungrouped_fields_come_first_outside():
    html = _env().from_string(
        '{% from "settings.html" import gth_settings_section %}'
        '{{ gth_settings_section("prefs", "Preferences", settings, action="/s") }}'
    ).render(settings=SETTINGS)
    assert "<h3" not in html
    legends = re.findall(r'<legend class="gth-field-group-legend[^"]*">([^<]+)</legend>', html)
    assert legends == ["Appearance", "Tables"]
    assert html.index('name="site.banner"') < html.index("<fieldset")
    appearance = html.split(">Appearance</legend>", 1)[1]
    assert 'name="ui.theme"' in appearance.split("</fieldset>", 1)[0]
    # ids are unique per section, so two sections can share a group name
    assert 'id="gth-settings-prefs-group-2"' in html and 'id="gth-settings-prefs-group-3"' in html


def test_the_new_token_form_is_a_field_group():
    html = _env().get_template("api_tokens_section.html").render(section={
        "id": "api_tokens", "action": "/settings/api-tokens", "scope_choices": ["stock.read"],
        "expiry_choices": [30, None],
    })
    form = html.split('class="gth-form gth-api-tokens-add', 1)[1].split("</form>", 1)[0]
    group = form.split("<fieldset", 1)[1].split("</fieldset>", 1)[0]
    assert ">New token</legend>" in group
    assert 'name="name"' in group and 'name="scopes"' in group and 'name="expires_in_days"' in group
    assert "<h3" not in html
    # the Create button follows the group
    assert form.index("</fieldset>") < form.index('<button type="submit"')
