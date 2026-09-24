import json
from collections.abc import Iterable, Mapping

DEFAULT_DURATION_MS = 5000
VARIANTS = ("surface", "solid")


def toast(
    message: str,
    kind: str = "success",
    *,
    title: str | None = None,
    icon: str | None = None,
    action: Mapping[str, str] | None = None,
    duration: int = DEFAULT_DURATION_MS,
    variant: str = "surface",
    html: bool = False,
    events: Iterable[str] = (),
) -> str:
    """Build an HX-Trigger header value that fires the client-side showToast event.

    kind: "success" | "info" | "warning" | "danger" | "neutral" (aliases
    "warn", "error"). title: an optional bold first line. icon: a
    bootstrap-icons name (each kind has a default). action: {"label", "url"}
    renders a link. duration: ms before it hides itself; 0 = stays until
    closed. variant: "surface" (theme background, kind-coloured accent —
    the default) or "solid" (kind-coloured fill).

    html=True renders `message` as HTML instead of text. Only for markup the
    server itself produced and escaped (e.g. a template render) — NEVER for
    anything containing user input; the default text rendering is what keeps
    toast(f"Saved {name}") safe.

    `events` adds further HX-Trigger events to the same header (e.g.
    "closeModal", or a consumer's own "stocksChanged" that a table listens
    for with `hx-trigger="stocksChanged from:body"`). A response carries a
    single HX-Trigger header, so they have to be merged into one JSON object
    rather than set separately.

    Options left at their defaults are omitted from the payload, so a plain
    toast("Saved") is exactly {"showToast": {"message", "kind"}}.
    """
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}, got {variant!r}")
    if duration < 0:
        raise ValueError("duration must be >= 0 (0 = stays until closed)")
    detail: dict[str, object] = {"message": message, "kind": kind}
    if title:
        detail["title"] = title
    if icon:
        detail["icon"] = icon
    if action:
        detail["action"] = {"label": action["label"], "url": action["url"]}
    if duration != DEFAULT_DURATION_MS:
        detail["duration"] = duration
    if variant != "surface":
        detail["variant"] = variant
    if html:
        detail["html"] = True
    payload: dict[str, object] = {"showToast": detail}
    payload.update({event: True for event in events})
    return json.dumps(payload)
