"""gth_copy_button (copy_button.html) and gth_form_field(copy=True): a
copy-to-clipboard button that renders only when copy.js is loaded
(copy_js_url), and the new API token's Copy button."""

import re
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui

COPY_JS = "/a/js/copy.js"


def _env(copy_js_url=COPY_JS) -> Environment:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    if copy_js_url:
        env.globals["copy_js_url"] = copy_js_url
    return env


def _render(source: str, copy_js_url=COPY_JS, **context) -> str:
    return _env(copy_js_url).from_string(source).render(**context)


BUTTON = '{% from "copy_button.html" import gth_copy_button %}'


def test_copies_a_target():
    html = _render(BUTTON + '{{ gth_copy_button(target="#api-key") }}')
    assert_snapshot(html, "copy_button_target")
    assert 'data-gth-copy data-gth-copy-target="#api-key"' in html
    assert "data-gth-copy-text" not in html
    assert 'class="btn btn-sm btn-outline-secondary gth-copy-button"' in html


def test_copies_literal_text_escaped():
    html = _render(BUTTON + '{{ gth_copy_button(text=link, label="Copy link") }}',
                   link='https://x.test/?a=1&b="2"')
    assert 'data-gth-copy-text="https://x.test/?a=1&amp;b=&#34;2&#34;"' in html
    assert "data-gth-copy-target" not in html
    assert '<span class="gth-copy-label">Copy link</span>' in html


def test_icon_only_keeps_the_label_as_the_accessible_name():
    html = _render(BUTTON + '{{ gth_copy_button(target="#k", icon_only=True, size=None) }}')
    assert '<span class="gth-copy-label visually-hidden">Copy</span>' in html
    assert 'class="btn btn-outline-secondary gth-copy-button"' in html


def test_renders_nothing_without_the_script():
    html = _render(BUTTON + '{{ gth_copy_button(target="#k") }}', copy_js_url=None)
    assert html.strip() == ""


def test_form_field_copy_puts_the_button_in_the_input_group():
    source = ('{% from "form.html" import gth_form_field %}'
              '{{ gth_form_field("webhook", "Webhook URL", value="https://x.test/hook",'
              ' suffix="URL", input_attrs={"readonly": "readonly"}, copy=True) }}')
    html = _render(source)
    group = html.split('<div class="input-group">', 1)[1].split("</div>", 1)[0]
    assert 'id="gth-field-webhook"' in group
    # after the suffix, inside the group, sized like the field
    assert group.index("gth-field-webhook-suffix") < group.index("gth-copy-button")
    assert ('class="btn btn-outline-secondary gth-copy-button" data-gth-copy'
            ' data-gth-copy-target="#gth-field-webhook"') in group


def test_form_field_copy_without_the_script_is_a_plain_field():
    source = ('{% from "form.html" import gth_form_field %}'
              '{{ gth_form_field("webhook", "Webhook URL", value="x", copy=True) }}')
    html = _render(source, copy_js_url=None)
    assert "input-group" not in html and "gth-copy-button" not in html


def test_the_new_api_token_has_a_copy_button():
    env = _env(copy_js_url=None)
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])  # sets copy_js_url too
    html = env.get_template("api_tokens_section.html").render(section={
        "id": "api_tokens", "action": "/settings/api-tokens",
        "created": {"name": "backup script", "token": "s3cr3t"},
    })
    alert = html.split("gth-api-token-created", 1)[1].split("</div>\n  </div>", 1)[0]
    assert re.search(r'id="gth-settings-api_tokens-new-token" value="s3cr3t"\s+readonly', alert)
    assert 'data-gth-copy-target="#gth-settings-api_tokens-new-token"' in alert


def test_the_script_ships_with_the_package():
    js = Path(greentechhub_ui.__file__).parent / "static" / "js" / "copy.js"
    source = js.read_text(encoding="utf-8")
    assert "[data-gth-copy]" in source and "navigator.clipboard" in source
    assert "showToast" in source  # the fallback toast, through toast.js
    assert "getElementById" in source  # "#gth-field-ui.theme" isn't a class selector


SETTING_FIELD = ('{% from "settings.html" import gth_setting_field %}'
                 '{{ gth_setting_field(s, value) }}')


def test_a_copyable_str_setting_gets_a_copy_button_targeting_its_field():
    setting = {"key": "api.base_url", "type": "str", "label": "Base URL", "default": "",
               "readonly": True, "copyable": True}
    html = _render(SETTING_FIELD, s=setting, value="https://api.example.test")
    group = html.split('<div class="input-group">', 1)[1]
    assert 'id="gth-field-api.base_url"' in group and "readonly" in group
    # "#gth-field-api.base_url": copy.js looks a "#…" target up by id, so the dot is fine
    assert 'data-gth-copy-target="#gth-field-api.base_url"' in group


def test_settings_without_copyable_get_no_button():
    plain = {"key": "site.banner", "type": "str", "label": "Banner", "default": ""}
    # a dict's .copy is a method: only a real `copyable: True` counts
    for setting in (plain, plain | {"copyable": "yes"}, plain | {"copyable": False}):
        assert "gth-copy-button" not in _render(SETTING_FIELD, s=setting, value="x")


def test_copyable_is_ignored_on_a_secret_and_without_the_script():
    secret = {"key": "smtp.password", "type": "str", "label": "Password", "default": "",
              "secret": True, "copyable": True}
    assert "gth-copy-button" not in _render(SETTING_FIELD, s=secret, value=None)
    setting = {"key": "k", "type": "str", "label": "K", "default": "", "copyable": True}
    html = _render(SETTING_FIELD, copy_js_url=None, s=setting, value="v")
    assert "gth-copy-button" not in html and "input-group" not in html


def test_the_playground_profile_has_a_copyable_user_id():
    import asyncio

    import httpx

    from playground.app import app

    async def go():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies={"playground-user": "admin"}) as client:
            return (await client.get("/settings")).text

    profile = asyncio.run(go()).split('id="gth-settings-profile"', 1)[1].split("</section>", 1)[0]
    assert re.search(r'id="gth-field-user_id" name="user_id"\s+class="form-control"'
                     r'\s+value="admin"', profile)
    assert 'data-gth-copy-target="#gth-field-user_id"' in profile
