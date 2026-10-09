"""The CSP-ready shell (v0.17): with csp_nonce every <script> app.html
renders carries it, the pre-paint and htmx setup run from static files when
their URLs are set (inline otherwise), and htmx gets the nonce and stops
injecting its indicator <style>."""

import re

import html5lib
from jinja2 import Environment
from test_app_shell_renders import _context, _env

import greentechhub_ui
from greentechhub_ui import shell_globals

NONCE = "r4nd0m-n0nce"
ALL_URLS = {k: v for k, v in shell_globals(service_name="Svc", nav_items=[]).items()
            if k.endswith("_js_url")}


def _shell(**kw) -> str:
    return _env().get_template("app.html").render(**_context(**kw))


def _scripts(html: str) -> list[str]:
    return re.findall(r"<script\b[^>]*>", html)


def test_every_script_carries_the_nonce():
    for layout in ("navbar", "sidebar"):
        html = _shell(csp_nonce=NONCE, layout=layout, show_command_palette=True,
                      extra_js=["/x.js"], **ALL_URLS)
        html5lib.HTMLParser(strict=True).parse(html)
        tags = _scripts(html)
        assert len(tags) > 15
        for tag in tags:
            assert f'nonce="{NONCE}"' in tag or 'type="application/json"' in tag, tag


def test_inline_fallbacks_carry_the_nonce_too():
    html = _shell(csp_nonce=NONCE, layout="sidebar", alert_banner_js_url="/a/js/ab.js")
    inline = [t for t in _scripts(html) if "src=" not in t]
    assert len(inline) == 4  # theme, sidebar rail, banners, 422 handler
    assert all(t == f'<script nonce="{NONCE}">' for t in inline)


def test_nonce_is_escaped():
    html = _shell(csp_nonce='x"><script>alert(1)</script>')
    assert '<script>alert(1)' not in html
    assert 'nonce="x&#34;&gt;&lt;script&gt;' in html


def test_no_nonce_changes_nothing():
    html = _shell(**ALL_URLS)
    assert "nonce=" not in html and "htmx-config" not in html
    assert '<script src="/gth-assets/js/htmx-setup.js"></script>' in html


def test_htmx_config_meta_under_a_nonce():
    html = _shell(csp_nonce=NONCE)
    meta = re.search(r'<meta name="htmx-config" content=\'([^\']*)\'>', html).group(1)
    assert meta == '{"includeIndicatorStyles": false, "inlineScriptNonce": "r4nd0m-n0nce"}'
    assert html.index("htmx-config") < html.index("htmx.min.js")  # read when htmx loads


def test_prepaint_runs_from_its_static_file_when_set():
    html = _shell(prepaint_js_url="/a/js/prepaint.js", layout="sidebar",
                  alert_banner_js_url="/a/js/ab.js",
                  user_settings={"ui.sidebar_default": "rail"})
    assert '<script src="/a/js/prepaint.js" data-sidebar="rail" data-banners></script>' in html
    assert "gth-sidebar-mode" not in html and "gth-banner:" not in html  # no inline copy
    # Only what applies: no sidebar outside layout="sidebar", no banners without their script.
    html = _shell(prepaint_js_url="/a/js/prepaint.js", alert_banner_js_url="/a/js/ab.js")
    assert '<script src="/a/js/prepaint.js" data-banners></script>' in html
    assert "prepaint.js" not in _shell(prepaint_js_url="/a/js/prepaint.js")


def test_htmx_setup_replaces_the_inline_422_handler():
    assert "evt.detail.xhr.status === 422" in _shell()
    html = _shell(htmx_setup_js_url="/a/js/htmx-setup.js")
    assert "evt.detail.xhr.status === 422" not in html
    assert html.index("htmx.min.js") < html.index("/a/js/htmx-setup.js")


def test_the_static_scripts_exist_and_match_the_inline_fallbacks():
    js = greentechhub_ui.static_path
    prepaint = (js / "js" / "prepaint.js").read_text(encoding="utf-8")
    setup = (js / "js" / "htmx-setup.js").read_text(encoding="utf-8")
    html = _shell(layout="sidebar", alert_banner_js_url="/a/js/ab.js")
    for shared in ('localStorage.getItem("gth-sidebar-mode")',
                   'stored === "rail" || (stored !== "full" && preferred === "rail")',
                   'key.indexOf("gth-banner:") === 0', ':not([data-gth-banner-current])'):
        assert shared in prepaint and shared in html, shared
    assert "evt.detail.xhr.status === 422" in setup
    filter_check = 'e.type === "change" && e.target && e.target.type === "search"'
    assert filter_check in setup and filter_check in _shell()


def test_no_component_needs_htmx_eval():
    """hx-trigger filters ([...]), hx-on, hx-vars and js: values make htmx
    eval, which the recommended CSP blocks."""
    import pathlib
    import re as _re
    root = pathlib.Path(greentechhub_ui.components_path)
    templates = pathlib.Path(greentechhub_ui.templates_path)
    for path in [*root.glob("*.html"), *templates.glob("*.html")]:
        text = path.read_text(encoding="utf-8")
        assert not _re.search(r'hx-trigger="[^"]*\[', text), path.name
        assert "hx-on" not in text and "hx-vars" not in text and '"js:' not in text, path.name


def test_django_builtin_csp_nonce_reaches_every_script():
    """Django 6's ContentSecurityPolicyMiddleware + the csp context processor
    hand templates the same `csp_nonce` name — a lazy object that's falsy until
    read (and only a read puts it in the header). app.html must read it."""
    import pytest
    pytest.importorskip("django")
    from django.conf import settings
    from django.http import HttpResponse
    from django.middleware.csp import ContentSecurityPolicyMiddleware
    from django.template.backends.jinja2 import Jinja2
    from django.test import RequestFactory
    from django.utils.csp import CSP

    if not settings.configured:
        settings.configure(TEMPLATES=[{
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "DIRS": [str(greentechhub_ui.templates_path), str(greentechhub_ui.components_path)],
            "APP_DIRS": False, "OPTIONS": {}}])
        import django
        django.setup()
    engine = Jinja2({"NAME": "gth-csp", "DIRS": [], "APP_DIRS": False, "OPTIONS": {
        "environment": "test_csp_shell._django_environment",
        "context_processors": ["django.template.context_processors.csp"]}})

    def view(request):
        return HttpResponse(engine.get_template("app.html").render({}, request))

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "SECURE_CSP", {"script-src": [CSP.SELF, CSP.NONCE]}, raising=False)
        response = ContentSecurityPolicyMiddleware(view)(RequestFactory().get("/"))
    nonce = re.search(r"'nonce-([^']+)'", response["Content-Security-Policy"]).group(1)
    html = response.content.decode()
    tags = _scripts(html)
    assert tags and all(f'nonce="{nonce}"' in t for t in tags)
    assert f'"inlineScriptNonce": "{nonce}"' in html


def _django_environment(**options):
    return greentechhub_ui.install(Environment(**options), service_name="Svc", nav_items=[])
