"""The playground's Authentik persona: someone signed in through an identity
provider sees the Profile's name and email read-only ("Managed by
Authentik."), as greentechhub-fastapi's account_profile renders them, and a
save keeps their value. Other personas keep an editable profile."""

import re

from test_playground_routes import _as, _post, _run


def _input(html: str, key: str) -> str:
    return re.search(rf'<input[^>]*id="gth-field-{key}"[^>]*>', html).group(0)


def test_the_persona_is_listed():
    page = _run(_as("anonymous", "GET", "/personas")).text
    assert 'data-persona="authentik"' in page or "data-persona=authentik" in page
    assert "Signed in through Authentik" in page


def test_its_profile_is_read_only():
    page = _run(_as("authentik", "GET", "/settings")).text
    for key in ("display_name", "email"):
        assert 'readonly="readonly"' in _input(page, key)
    assert 'type="email"' in _input(page, "email")
    assert page.count("Managed by Authentik.") == 2
    assert 'value="Sam Single-Sign-On"' in _input(page, "display_name")


def test_a_save_keeps_the_locked_values():
    try:
        response = _run(_as("authentik", "POST", "/settings-demo/profile",
                            data={"display_name": "Someone Else", "email": "else@example.com"}))
        assert response.status_code == 200
        assert 'value="Sam Single-Sign-On"' in _input(response.text, "display_name")
        assert 'value="sam@example.com"' in _input(response.text, "email")
    finally:
        _run(_post("/demo/reset"))


def test_other_personas_edit_their_profile():
    page = _run(_as("admin", "GET", "/settings")).text
    assert "readonly" not in _input(page, "display_name")
    email = _input(page, "email")
    assert "readonly" not in email and 'type="email"' in email
    assert "Managed by Authentik." not in page
