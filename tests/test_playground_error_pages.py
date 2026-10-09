"""The playground's error-page wiring (the docs/components.md › Error pages
recipe): a browser's page request gets 403.html / 404.html / 500.html with
the right status; JSON and htmx requests keep the defaults."""

import httpx
from test_playground_routes import _run

from playground.app import app

PAGE = {"accept": "text/html,application/xhtml+xml"}


async def _get(path, **headers):
    # raise_app_exceptions=False: the 500 handler's response, as a server sends it
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, headers=headers)


def test_page_requests_get_the_error_pages():
    for path, code, title in [("/no-such-page", 404, "Page not found"),
                              ("/demo/error-page/403", 403, "Access denied"),
                              ("/demo/error-page/500", 500, "Something went wrong")]:
        response = _run(_get(path, **PAGE))
        assert response.status_code == code, path
        assert response.headers["content-type"].startswith("text/html")
        assert f'<h1 class="gth-page-header-title">{title}</h1>' in response.text
        assert 'class="gth-sidebar' in response.text  # the playground's own shell


def test_500_shows_the_request_id_and_a_retry():
    response = _run(_get("/demo/error-page/500", **PAGE, **{"x-request-id": "abc-123"}))
    assert '<code class="user-select-all">abc-123</code>' in response.text
    assert 'href="/demo/error-page/500">Try again</a>' in response.text


def test_json_and_htmx_requests_keep_the_defaults():
    response = _run(_get("/no-such-page"))
    assert response.status_code == 404 and response.json() == {"detail": "Not Found"}
    response = _run(_get("/no-such-page", **PAGE, **{"hx-request": "true"}))
    assert response.status_code == 404 and response.json() == {"detail": "Not Found"}
    response = _run(_get("/demo/error-page/500"))
    assert response.status_code == 500 and response.text == "Internal Server Error"


def test_no_two_playground_routes_share_a_method_and_path():
    """A second route on the same path is silently shadowed by the first (the
    error-page demo once hid /demo/error/{status}, the error-toast demo)."""
    import re

    seen = {}
    for route in app.routes:
        if not hasattr(route, "path"):  # an included router: its routes are listed too
            continue
        # /demo/error/{code} and /demo/error/{status} are the same path.
        path = re.sub(r"\{[^}]*\}", "{}", route.path)
        for method in getattr(route, "methods", None) or ():
            assert (method, path) not in seen, (
                f"{method} {route.path} is shadowed by {seen.get((method, path))}")
            seen[(method, path)] = route.path
