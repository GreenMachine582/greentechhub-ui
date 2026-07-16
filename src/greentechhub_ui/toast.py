import json


def toast(message: str, kind: str = "success") -> str:
    """Build an HX-Trigger header value that fires the client-side showToast event."""
    return json.dumps({"showToast": {"message": message, "kind": kind}})
