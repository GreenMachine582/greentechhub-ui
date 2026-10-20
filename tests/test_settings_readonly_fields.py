"""settings.html's str fields: input_type sets the <input type>, and
readonly locks a field (a profile field an identity provider owns)."""

import re

from test_settings_templates import _render_section

EMAIL = {"key": "email", "type": "str", "label": "Email", "default": "", "input_type": "email",
         "readonly": True, "help_text": "Managed by Authentik."}
NAME = {"key": "display_name", "type": "str", "label": "Display name", "default": ""}


def _input(html: str, key: str) -> str:
    return re.search(rf'<input[^>]*id="gth-field-{key}"[^>]*>', html).group(0)


def _profile() -> str:
    return _render_section(id="profile", settings=[NAME, EMAIL], action="/settings/profile",
                           values={"display_name": "Alice", "email": "a@example.com"})


def test_input_type_and_readonly():
    html = _profile()
    email = _input(html, "email")
    assert 'type="email"' in email and 'readonly="readonly"' in email
    assert 'value="a@example.com"' in email
    assert "Managed by Authentik." in html


def test_other_str_fields_stay_editable_text():
    html = _profile()
    name = _input(html, "display_name")
    assert 'type="text"' in name and "readonly" not in name
