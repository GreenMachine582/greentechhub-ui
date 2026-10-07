"""gth_form_actions and gth_modal_form: a form's Cancel/Save row, and a
form in a modal that re-renders itself on a 422 (form_only=True)."""

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "form.html" import gth_form_actions, gth_modal_form, gth_form_field %}"""


def test_default_actions_cancel_the_modal_and_save():
    rendered = _render(IMPORT + "{{ gth_form_actions() }}")
    assert '<div class="d-flex justify-content-end gap-2 gth-form-actions">' in rendered
    assert ('<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">'
            "Cancel</button>") in rendered
    assert '<button type="submit" class="btn btn-primary">Save</button>' in rendered
    assert rendered.index("Cancel") < rendered.index("Save")


def test_cancel_as_a_link_or_none():
    link = _render(IMPORT + """{{ gth_form_actions("Create", cancel="/stocks?a=1&b=2") }}""")
    assert '<a class="btn btn-secondary" href="/stocks?a=1&amp;b=2">Cancel</a>' in link
    assert ">Create</button>" in link
    alone = _render(IMPORT + """{{ gth_form_actions(cancel=False, actions_class="mt-3") }}""")
    assert "Cancel" not in alone and "gth-form-actions mt-3" in alone


def test_busy_label_makes_a_busy_submit():
    rendered = _render(IMPORT + """{{ gth_form_actions("Import", busy_label="Importing…") }}""")
    assert '<button type="submit" class="btn btn-primary gth-busy-button"' in rendered
    assert "Importing…" in rendered


def test_submit_attrs_skip_none():
    rendered = _render(IMPORT + """{{ gth_form_actions("Delete", submit_type="button",
        submit_class="btn-danger", submit_attrs={"hx-delete": "/x/1", "hx-target": None}) }}""")
    delete = '<button type="button" class="btn btn-danger" hx-delete="/x/1">Delete</button>'
    assert delete in rendered


def test_modal_form():
    rendered = _render(IMPORT + """
        {% call gth_modal_form("stock-modal", "New stock", "/stocks") %}
          {{ gth_form_field("name", "Name") }}
        {% endcall %}""")
    assert_snapshot(rendered, "modal_form")
    assert 'class="modal fade gth-modal" id="stock-modal"' in rendered
    assert 'hx-post="/stocks" hx-target="this" hx-swap="outerHTML"' in rendered
    assert rendered.index('name="name"') < rendered.index("gth-form-actions")
    assert "hx-disabled-elt" not in rendered


def test_modal_form_only_renders_the_form_with_errors():
    rendered = _render(IMPORT + """
        {% call gth_modal_form("stock-modal", "New stock", "/stocks", form_only=True,
                               error="Symbol taken", busy_label="Saving…") %}
          {{ gth_form_field("symbol", "Symbol", errors=["Already exists"]) }}
        {% endcall %}""")
    assert "gth-modal" not in rendered
    assert rendered.strip().startswith('<form method="post" action="/stocks"')
    assert "Symbol taken" in rendered and "Already exists" in rendered
    assert 'hx-disabled-elt="find button[type=submit]"' in rendered
    assert "gth-busy-button" in rendered
