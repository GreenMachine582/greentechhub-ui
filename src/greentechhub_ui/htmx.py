"""htmx request/response helpers that don't need a web framework: they take
any headers Mapping — Starlette's and Django's request.headers are both
case-insensitive; a plain dict is looked up by the canonical name and its
lower-case form. The response side (a 204 carrying HX-Trigger) is the
adapter's job: greentechhub_fastapi.htmx.hx_response(trigger(...)).
"""

import json
from collections.abc import Mapping
from typing import Any


def _header(headers: Mapping[str, str], name: str) -> str | None:
    value = headers.get(name)
    return value if value is not None else headers.get(name.lower())


def is_htmx(headers: Mapping[str, str]) -> bool:
    """The request came from htmx (HX-Request: true)."""
    return _header(headers, "HX-Request") == "true"


def wants_fragment(headers: Mapping[str, str]) -> bool:
    """Render the partial, not the page: an htmx request that isn't htmx's
    history-restore request (which needs a whole page for its cache miss)."""
    return is_htmx(headers) and _header(headers, "HX-History-Restore-Request") != "true"


def hx_target(headers: Mapping[str, str]) -> str | None:
    """The id of the element the response will be swapped into, if any."""
    return _header(headers, "HX-Target")


def trigger(*events: str, **detail_events: Any) -> str:
    """An HX-Trigger header value firing bare events and/or events with a
    detail payload: trigger("watchlistChanged") or trigger(stockChanged={"id": 7}).
    For a toast (optionally plus events) use greentechhub_ui.toast()."""
    payload: dict[str, Any] = {event: True for event in events}
    payload.update(detail_events)
    return json.dumps(payload)
