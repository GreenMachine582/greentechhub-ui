import subprocess
import sys
from pathlib import Path

from jinja2 import DictLoader, Environment

import greentechhub_ui
from greentechhub_ui import htmx, install, render_macro, shell_globals, static_dirs, template_dirs


def test_template_and_static_dirs_exist():
    assert all(d.is_dir() for d in template_dirs())
    assert (template_dirs()[0] / "app.html").is_file()
    assert all(d.is_dir() for d in static_dirs().values())


def test_static_dirs_prefixes_match_shell_globals():
    g = shell_globals(service_name="S", nav_items=[])
    prefixes = list(static_dirs())
    assert g["htmx_js_url"].startswith(prefixes[0] + "/")
    assert g["theme_css_url"].startswith(prefixes[1] + "/")
    custom = static_dirs("/a", "/t")
    assert set(custom) == {"/a", "/t"}


def test_install_puts_app_templates_first_and_is_idempotent():
    env = Environment(loader=DictLoader({"badge.html": "APP OVERRIDE"}))
    install(env)
    install(env)  # no second loader layer
    assert env.get_template("badge.html").render() == "APP OVERRIDE"  # app wins
    assert env.get_template("card.html")  # gth-ui components reachable
    assert len(env.loader.loaders) == 1 + len(template_dirs())


def test_install_with_shell_kwargs_sets_globals_and_bare_env():
    env = install(Environment(), service_name="Svc", nav_items=[{"label": "A", "url": "/a"}])
    assert env.globals["brand"]["service_name"] == "Svc"
    assert env.get_template("app.html")  # a loader-less env gets gth-ui's alone


def test_render_macro_sees_env_globals():
    env = install(Environment(autoescape=True), service_name="Svc",
                  nav_items=[{"label": "Data", "children": [{"label": "T", "url": "/t"}]}])
    badge = render_macro(env, "badge.html", "gth_badge", "3", "warn")
    assert "text-warning-emphasis" in badge and ">3</span>" in badge
    palette = render_macro(env, "command_palette.html", "gth_command_palette",
                           env.globals["nav_items"])
    assert r"Data \u203a T" in palette  # used the nav_flatten global


def test_htmx_header_helpers_plain_and_case_insensitive():
    class CI(dict):
        def get(self, k, default=None):
            return {key.lower(): v for key, v in self.items()}.get(k.lower(), default)

    for headers in ({"HX-Request": "true", "HX-Target": "t"},
                    {"hx-request": "true", "hx-target": "t"},
                    CI({"Hx-Request": "true", "hX-tArGeT": "t"})):
        assert htmx.is_htmx(headers) and htmx.wants_fragment(headers)
        assert htmx.hx_target(headers) == "t"
    restore = {"HX-Request": "true", "HX-History-Restore-Request": "true"}
    assert htmx.is_htmx(restore) and not htmx.wants_fragment(restore)
    assert not htmx.is_htmx({}) and htmx.hx_target({}) is None


def test_trigger_builds_bare_and_detail_events():
    import json

    assert json.loads(htmx.trigger("a", "b")) == {"a": True, "b": True}
    assert json.loads(htmx.trigger("a", changed={"id": 7})) == {"a": True, "changed": {"id": 7}}


def test_table_state_is_own_swap():
    state = greentechhub_ui.TableState.from_query({}, id="parts", base_url="/p")
    assert state.is_own_swap({"HX-Target": "parts"})
    assert not state.is_own_swap({"HX-Target": "panel-body"}) and not state.is_own_swap({})


def test_importing_greentechhub_ui_needs_no_web_framework():
    """gth-ui is shared by FastAPI and Django consumers: its runtime deps are
    jinja2 alone. Import it with fastapi/starlette/django made unimportable."""
    code = ("import sys\n"
            "for m in ('fastapi', 'starlette', 'django'): sys.modules[m] = None\n"
            "import greentechhub_ui, greentechhub_ui.htmx, greentechhub_ui.setup\n"
            "print('ok')\n")
    src = Path(greentechhub_ui.__file__).parent.parent
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={"PYTHONPATH": str(src), "SYSTEMROOT": __import__("os").environ.get(
                             "SYSTEMROOT", "")})
    assert out.returncode == 0 and out.stdout.strip() == "ok", out.stderr


def test_page_base_template_header_crumbs_and_actions():
    env = install(Environment(loader=DictLoader({
        "p.html": '{% extends "page.html" %}'
                  '{% block header_actions %}<button id="act">New</button>{% endblock %}'
                  '{% block page %}<p id="body">Body</p>{% endblock %}',
        "bare.html": '{% extends "page.html" %}{% block page %}x{% endblock %}',
    })), service_name="S", nav_items=[{"label": "Data", "url": "/data",
                                        "children": [{"label": "T", "url": "/data/t"}]}])
    ctx = {"current_user": None, "flashes": [], "url_for": lambda *a, **k: "/"}
    html = env.get_template("p.html").render(page_title="Tables", current_path="/data/t", **ctx)
    assert '<button id="act">New</button>' in html and '<p id="body">Body</p>' in html
    assert '<a href="/data">Data</a>' in html  # trail derived from the nav
    # No current_path (or no nav helpers): just the title, no breadcrumbs.
    bare = env.get_template("bare.html").render(page_title="Plain", **ctx)
    assert "Plain" in bare and 'aria-label="breadcrumb"' not in bare
