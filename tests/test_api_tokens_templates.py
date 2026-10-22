"""api_tokens_section.html — the settings page's "API tokens" section
(greentechhub-fastapi's ApiTokenViews supplies the data), and
settings_page.html including a section through its own `template`."""

from datetime import UTC, datetime

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui

T0 = datetime(2026, 10, 1, 9, 30, tzinfo=UTC)
TOKEN = {"id": "a" * 32, "name": "backup script", "scopes": ["stock.read", "stock.write"],
         "created_at": T0, "expires_at": datetime(2027, 1, 1, tzinfo=UTC), "last_used_at": T0,
         "expired": False, "revoke_url": "/settings/api-tokens/" + "a" * 32}


def _env() -> Environment:
    env = Environment(loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _section(**overrides) -> dict:
    section = {"id": "api_tokens", "title": "API tokens", "description": "Tokens for your scripts.",
               "template": "api_tokens_section.html", "action": "/settings/api-tokens",
               "tokens": [TOKEN], "scope_choices": ["stock.read", "stock.write"],
               "expiry_choices": [30, 90, 365, None], "default_expiry_days": 90, "values": {},
               "created": None, "errors": None}
    return section | overrides


def _render(**overrides) -> str:
    return _env().get_template("api_tokens_section.html").render(section=_section(**overrides))


def test_settings_page_includes_a_sections_own_template():
    html = _env().get_template("settings_page.html").render(
        page_title="Settings",
        settings_sections=[
            {"id": "preferences", "title": "Preferences", "settings": [], "action": "/settings/p"},
            _section(),
        ],
    )
    assert 'id="gth-settings-preferences"' in html  # still settings_section.html
    assert 'id="gth-settings-api_tokens"' in html and "backup script" in html


def test_the_section_swaps_itself_and_posts_the_form():
    html = _render()
    assert 'hx-target="#gth-settings-api_tokens" hx-swap="outerHTML"' in html
    assert 'hx-post="/settings/api-tokens"' in html and 'action="/settings/api-tokens"' in html
    assert "Tokens for your scripts." in html
    assert 'name="name"' in html and 'maxlength="80"' in html
    for scope in ("stock.read", "stock.write"):
        assert f'name="scopes" value="{scope}"' in html


def test_expiry_offers_never_and_selects_the_default():
    html = _render()
    assert '<option value="90" selected>90 days</option>' in html
    assert '<option value="">Never</option>' in html
    assert '<option value="" selected>Never</option>' in _render(default_expiry_days=None)


def test_a_token_row_shows_its_details_and_a_revoke_modal():
    html = _render()
    assert "backup script" in html and "stock.read" in html and "stock.write" in html
    assert "1 Oct 2026" in html and "1 Jan 2027" in html
    assert f'hx-delete="{TOKEN["revoke_url"]}"' in html
    assert 'data-bs-target="#gth-settings-api_tokens-revoke-1"' in html
    assert "Delete the backup script token?" in html


def test_revoke_modals_sit_outside_the_table():
    # inside the row's text-end cell they'd inherit its right alignment
    html = _render()
    table = html.split("<table", 1)[1].split("</table>", 1)[0]
    assert "gth-modal" not in table
    assert 'id="gth-settings-api_tokens-revoke-1"' in html.split("</table>", 1)[1]


def test_expired_never_and_unused_tokens():
    html = _render(tokens=[TOKEN | {"expired": True},
                           TOKEN | {"name": "forever", "expires_at": None, "last_used_at": None,
                                    "scopes": []}])
    assert "Expired" in html
    assert html.count('<span class="text-secondary">Never</span>') == 2  # never expires or used
    assert "No scopes" in html


def test_a_new_token_is_shown_once_in_a_readonly_field():
    created = _render(created={"name": "backup script", "token": "s3cr3t-token-value"})
    assert 'value="s3cr3t-token-value"' in created and "readonly" in created
    assert "You won't see it again" in created
    assert "s3cr3t-token-value" not in _render()
    assert "gth-api-token-created" not in _render()


def test_a_422_echoes_the_form_and_its_errors():
    html = _render(values={"name": "x" * 81, "scopes": ["stock.write"], "expires_in_days": "365"},
                   errors={"name": ["At most 80 characters."],
                           "scopes": ["You can't give a token users.manage."],
                           "expires_in_days": ["Choose one of the offered expiries."]})
    assert "At most 80 characters." in html and "offered expiries" in html
    assert "users.manage." in html
    assert '<option value="365" selected>365 days</option>' in html
    assert html.count("checked") == 1  # only stock.write


def test_empty_states():
    html = _render(tokens=[], scope_choices=[])
    assert "No API tokens yet." in html
    assert "gth-api-tokens-no-scopes" in html and 'name="scopes"' not in html


def test_snapshot():
    assert_snapshot(_render(created={"name": "backup script", "token": "s3cr3t-token-value"}),
                    "api_tokens_section_template")
