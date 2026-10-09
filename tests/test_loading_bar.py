"""gth_loading_bar: the htmx loading bar app.html renders when
loading_bar_js_url is set."""

from test_app_shell_renders import _context, _env
from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "loading_bar.html" import gth_loading_bar %}"""


def test_loading_bar():
    rendered = _render(IMPORT + "{{ gth_loading_bar() }}")
    assert_snapshot(rendered, "loading_bar")
    assert 'data-gth-loading-bar data-delay="300" aria-hidden="true"' in rendered


def test_loading_bar_delay_is_an_int():
    assert 'data-delay="0"' in _render(IMPORT + "{{ gth_loading_bar(delay='x' ~ '') }}")
    assert 'data-delay="150"' in _render(IMPORT + "{{ gth_loading_bar(delay=150.7) }}")


def test_app_shell_renders_it_only_when_configured():
    def shell(**kw):
        return _env().get_template("app.html").render(**_context(**kw))

    assert "gth-loading-bar" not in shell()
    html = shell(loading_bar_js_url="/a/js/loading-bar.js")
    assert 'data-gth-loading-bar data-delay="300"' in html
    assert '<script src="/a/js/loading-bar.js"></script>' in html
    # First thing in <body>, so it sits above the navbar and any banner.
    assert html.index("data-gth-loading-bar") < html.index("<nav")
    assert 'data-delay="800"' in shell(loading_bar_js_url="/a/js/l.js", loading_bar_delay=800)
