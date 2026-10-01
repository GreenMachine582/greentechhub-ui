"""roles_page.html / roles_section.html — the ready-made role assignment page
a service (or greentechhub-fastapi's RoleAdminViews) renders with data only."""

import re
from collections import Counter

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui

OPTIONS = [{"value": "viewer", "label": "Viewer"}, {"value": "admin", "label": "Admin"}]
ASSIGNMENTS = [{"subject": "alice", "roles": ["admin"]},
               {"subject": "bob/ops", "roles": ["viewer", "admin"]}]


def _env() -> Environment:
    env = Environment(loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _section(**context) -> str:
    base = {"roles_url": "/admin/roles", "roles_options": OPTIONS,
            "roles_assignments": ASSIGNMENTS}
    return _env().get_template("roles_section.html").render(**(base | context))


def test_section_is_swapped_whole_by_every_form():
    html = _section()
    assert re.search(r'<section[^>]*id="gth-roles"[^>]*hx-target="#gth-roles"[^>]*'
                     r'hx-swap="outerHTML"', html, re.S)
    assert 'hx-post="/admin/roles"' in html  # Assign


def test_one_row_per_subject_with_its_roles_checked():
    html = _section()
    assert 'hx-post="/admin/roles/alice"' in html
    assert 'hx-delete="/admin/roles/alice"' in html
    # alice: viewer unchecked, admin checked; bob: both checked
    assert re.search(r'id="gth-roles-1-1" autocomplete="off">', html)
    assert 'id="gth-roles-1-2" autocomplete="off" checked' in html
    assert 'id="gth-roles-2-1" autocomplete="off" checked' in html


def test_subjects_are_urlencoded_including_slashes():
    html = _section()
    assert 'hx-post="/admin/roles/bob%2Fops"' in html
    assert 'hx-delete="/admin/roles/bob%2Fops"' in html


def test_element_ids_are_unique_across_rows():
    ids = Counter(re.findall(r'\bid="([^"]+)"', _section()))
    assert [i for i, n in ids.items() if n > 1] == []


def test_assign_form_echoes_a_422():
    html = _section(roles_form={"subject": "carol", "roles": ["viewer"],
                                "errors": {"roles": ["Pick at least one role."],
                                           "subject": ["Unknown user."]}})
    assert 'value="carol"' in html
    assert "Unknown user." in html and "is-invalid" in html
    assert "Pick at least one role." in html
    assert 'id="gth-roles-add-1" autocomplete="off" checked' in html


def test_error_banner_and_empty_state():
    html = _section(roles_assignments=[], roles_error="Couldn't save.")
    assert "Couldn't save." in html
    assert "No roles assigned here yet." in html
    assert "<table" not in html


def test_page_wraps_the_section():
    html = _env().get_template("roles_page.html").render(
        page_title="Roles", roles_url="/roles", roles_options=OPTIONS,
        roles_assignments=ASSIGNMENTS)
    assert "<h1" in html and 'id="gth-roles"' in html


def test_roles_section_snapshot():
    assert_snapshot(_section(), "roles_section_template")
