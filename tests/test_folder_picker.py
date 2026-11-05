"""gth_folder_picker (v0.21): a path input with a Browse modal, and
gth_folder_browser / folder_browser.html, the modal body greentechhub-
fastapi's FolderPickerViews renders: breadcrumbs from "This computer",
Up, the hidden-folders switch, folders that navigate by hx-get keeping the
target and toggle, errors, and "Choose this folder"."""

import re
from urllib.parse import parse_qs, urlsplit

import html5lib
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from markupsafe import Markup
from test_macros_snapshot import assert_snapshot

import greentechhub_ui


def _env() -> Environment:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _field(**kwargs) -> str:
    return _env().from_string(
        '{% from "folder_picker.html" import gth_folder_picker %}'
        '{{ gth_folder_picker("library", "Library folder", "/folders", **kwargs) }}'
    ).render(kwargs=kwargs)


LISTING = {
    "path": "D:/Music/Albums", "parent": "D:/Music", "at_roots": False,
    "breadcrumbs": [{"label": "D:/", "path": "D:/"}, {"label": "Music", "path": "D:/Music"},
                    {"label": "Albums", "path": "D:/Music/Albums"}],
    "entries": [{"name": "2024 <live>", "path": "D:/Music/Albums/2024 <live>", "hidden": False},
                {"name": ".covers", "path": "D:/Music/Albums/.covers", "hidden": True}],
    "hidden_count": 0, "truncated": False, "error": None, "error_message": None,
}


def _browser(listing=None, **context) -> str:
    base = {"listing": LISTING if listing is None else listing, "browse_url": "/folders",
            "target": "gth-field-library", "show_hidden": False, "roots_label": "This computer"}
    return _env().get_template("folder_browser.html").render(**(base | context))


def _query(url: str) -> dict:
    query = urlsplit(Markup(url).unescape()).query
    return {k: v[0] for k, v in parse_qs(query, keep_blank_values=True).items()}


def _get(fragment: str) -> str:
    return re.search(r'hx-get="([^"]+)"', fragment).group(1)


# the field

def test_a_text_input_with_a_browse_button_and_its_modal():
    html = _field(value="D:/Music", help_text="Where your music lives", placeholder="D:/Music")
    assert 'data-gth-folder-picker-url="/folders"' in html
    assert '<label class="form-label" for="gth-field-library">Library folder</label>' in html
    assert 'id="gth-field-library"\n      name="library" value="D:/Music"' in html
    assert 'aria-describedby="gth-field-library-help"' in html
    assert 'aria-controls="gth-field-library-dialog">Browse…</button>' in html
    assert 'id="gth-field-library-dialog"' in html
    assert 'data-gth-folder-picker-for="gth-field-library"' in html
    assert ">Choose library folder</h1>" in html


def test_errors_mark_the_input_invalid():
    html = _field(errors=["That folder doesn't exist."])
    assert "is-invalid" in html and 'aria-invalid="true"' in html
    assert 'aria-describedby=" gth-field-library-error"' in html
    assert 'id="gth-field-library-error"' in html


def test_field_snapshot_and_well_formed():
    html = _field(value="D:/Music", help_text="Where your music lives", id="lib")
    assert 'id="lib"' in html and 'id="lib-dialog"' in html
    assert_snapshot(html, "folder_picker")
    html5lib.HTMLParser(strict=True).parseFragment(html)


# the browser

def test_breadcrumbs_start_at_this_computer():
    crumbs = _browser().split('<ol class="breadcrumb', 1)[1].split("</ol>", 1)[0]
    gets = re.findall(r'hx-get="([^"]+)"', crumbs)
    assert [_query(g)["path"] for g in gets] == ["", "D:/", "D:/Music"]
    assert '<span aria-current="page">Albums</span>' in crumbs and "This computer" in crumbs


def test_folders_navigate_keeping_the_target_and_toggle():
    html = _browser(show_hidden=True)
    entries = re.findall(r"<button[^>]*data-gth-folder-entry>", html, re.S)
    assert len(entries) == 2
    assert _query(_get(entries[0])) == {"path": "D:/Music/Albums/2024 <live>", "hidden": "1",
                                        "target": "gth-field-library"}
    assert 'hx-target="closest [data-gth-folder-picker-body]" hx-swap="innerHTML"' in entries[0]
    assert "2024 &lt;live&gt;" in html
    assert '<span class="badge text-bg-light border ms-auto">hidden</span>' in html


def test_up_and_the_hidden_switch():
    html = _browser()
    up = re.search(r"<button[^>]*gth-folder-up[^>]*>", html, re.S).group(0)
    assert _query(_get(up))["path"] == "D:/Music"
    switch = re.search(r'<input class="form-check-input"[^>]*>', html, re.S).group(0)
    assert "checked" not in switch and 'hx-trigger="change"' in switch
    assert _query(_get(switch))["hidden"] == "1"
    on = re.search(r'<input class="form-check-input"[^>]*>', _browser(show_hidden=True),
                   re.S).group(0)
    assert " checked" in on and _query(_get(on))["hidden"] == ""


def test_choose_this_folder():
    html = _browser()
    assert re.search(r'data-gth-folder-choose="D:/Music/Albums">Choose this folder', html)
    assert '<code class="small text-truncate me-auto gth-folder-current"' in html


def test_the_roots():
    roots = {"path": None, "parent": None, "at_roots": True, "breadcrumbs": [],
             "entries": [{"name": "C:/", "path": "C:/", "hidden": False},
                         {"name": "D:/", "path": "D:/", "hidden": False}],
             "hidden_count": 0, "truncated": False, "error": None, "error_message": None}
    html = _browser(roots)
    assert "gth-folder-up" not in html and 'aria-label="Drives"' in html and "bi-hdd" in html
    assert ('<span aria-current="page"><i class="bi bi-pc-display me-1" aria-hidden="true">'
            "</i>This computer</span>") in html
    assert re.search(r'data-gth-folder-choose="" disabled>', html)


def test_an_error_shows_its_message_and_cant_be_chosen():
    listing = LISTING | {"entries": [], "error": "permission_denied",
                         "error_message": "You don't have permission to open this folder."}
    html = _browser(listing)
    assert "gth-toast-warning" in html and "You don&#39;t have permission" in html
    assert "No folders here." not in html
    assert re.search(r'data-gth-folder-choose="D:/Music/Albums" disabled>', html)


def test_empty_hidden_and_truncated_notes():
    empty = _browser(LISTING | {"entries": [], "hidden_count": 2})
    assert "No folders here." in empty and "2 hidden folders not shown." in empty
    shown = _browser(LISTING | {"hidden_count": 2}, show_hidden=True)
    assert "hidden folders not shown" not in shown
    assert "Showing the first 2 folders." in _browser(LISTING | {"truncated": True})


def test_browser_is_well_formed():
    html5lib.HTMLParser(strict=True).parseFragment(_browser())
