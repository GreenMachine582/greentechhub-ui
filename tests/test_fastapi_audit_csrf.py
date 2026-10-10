"""The audit page and the CSRF shell against greentechhub-fastapi itself
(v0.16), not stand-in dicts: AuditViews renders audit_page.html with its
real context, and register_csrf + ui_context put the request's token on
<body> and in the logout form — the same token as the gth_csrf cookie."""

import asyncio
import json
import re
from datetime import UTC, datetime, timedelta
from html import unescape

import httpx
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from greentechhub_core.audit import InMemoryAuditStore, new_entry
from greentechhub_core.config import GTHBaseSettings
from greentechhub_core.identity import DevelopmentIdentityProvider, Identity
from greentechhub_core.permissions import Permission, Role
from greentechhub_fastapi import register_audit, register_auth, register_csrf, register_permissions
from greentechhub_fastapi.audit import AuditViews
from greentechhub_fastapi.auth.csrf import CSRF_COOKIE_NAME
from greentechhub_fastapi.templating import ui_context
from jinja2 import Environment

import greentechhub_ui

SECRET = "test-secret"


class _Settings(GTHBaseSettings):
    ROLE_BOOTSTRAP: str = "root=auditor"


def _templates() -> Jinja2Templates:
    env = greentechhub_ui.install(Environment(autoescape=True), service_name="Test", nav_items=[])
    return Jinja2Templates(env=env, context_processors=[ui_context])


def _app() -> FastAPI:
    settings = _Settings(secret_key=SECRET)
    templates = _templates()
    app = FastAPI()
    register_auth(app, settings)
    register_csrf(app)
    register_permissions(app, settings, roles=[Role(name="auditor",
                                                    permissions={Permission("audit.view")})])
    store = InMemoryAuditStore()
    start = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    store.record_sync(new_entry("auth.signed_in", actor="root", target=("user", "root"),
                                summary="root signed in", now=start))
    store.record_sync(new_entry("auth.sign_in_failed", summary="Failed sign-in as bob",
                                now=start + timedelta(hours=1)))
    register_audit(app, settings, store=store,
                   views=AuditViews(templates=templates, permission="audit.view"))

    @app.get("/home")
    async def home(request: Request):
        return templates.TemplateResponse(request, "page.html", {
            "page_title": "Home", "current_user": {"username": "root", "email": None},
            "logout_url": "/logout"})

    return app


def _get(app, path):
    async def go():
        identity = Identity(subject="root", username="root", email=None, groups=[], claims={})
        cookies = {"gth_session": DevelopmentIdentityProvider(secret_key=SECRET).issue(identity)}
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                     cookies=cookies) as client:
            return await client.get(path, headers={"Accept": "text/html"})

    return asyncio.run(go())


def test_audit_views_renders_the_audit_page():
    response = _get(_app(), "/admin/audit?action=auth.")
    assert response.status_code == 200
    html = response.text
    assert re.findall(r'<code class="gth-audit-action">([^<]+)<', html) == [
        "auth.sign_in_failed", "auth.signed_in"]
    assert '<time datetime="2026-10-01T10:00:00+00:00">' in html
    assert '<span class="text-secondary">System</span>' in html
    assert 'name="action"\n        value="auth."' in html


def test_register_csrf_puts_the_cookies_token_on_body_and_logout():
    response = _get(_app(), "/home")
    token = response.cookies[CSRF_COOKIE_NAME]
    header = re.search(r"<body hx-headers='([^']*)'>", response.text).group(1)
    assert json.loads(unescape(header)) == {"X-CSRF-Token": token}
    assert f'<input type="hidden" name="csrf_token" value="{token}">' in response.text
