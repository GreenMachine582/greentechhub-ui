import json
from collections.abc import Iterable


def toast(message: str, kind: str = "success", *, events: Iterable[str] = ()) -> str:
    """Build an HX-Trigger header value that fires the client-side showToast event.

    `events` adds further HX-Trigger events to the same header (e.g.
    "closeModal", or a consumer's own "stocksChanged" that a table listens
    for with `hx-trigger="stocksChanged from:body"`). A response carries a
    single HX-Trigger header, so they have to be merged into one JSON object
    rather than set separately.
    """
    payload: dict[str, object] = {"showToast": {"message": message, "kind": kind}}
    payload.update({event: True for event in events})
    return json.dumps(payload)
