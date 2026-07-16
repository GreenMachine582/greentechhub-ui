[← Back to README](../README.md)

# 🧩 Extension Points

Documented hooks so consumers can extend without forking or copying templates:

| Hook | Use case |
|---|---|
| `nav_items` context entry (custom items) | A service adds its own sidebar/navbar links alongside the shared ones — no template edit needed, just appending to the list it already supplies per the [context contract](contract.md) |
| `extra_head` context entry | Per-page `<head>` additions (a service-specific meta tag, a chart library's CSS) rendered into `app.html`'s head block without editing the shared template |
| `extra_css` / `extra_js` slots | A consumer injects one additional stylesheet/script (e.g. a page needing a charting library) without vendoring it into `greentechhub-ui` itself |
| Custom Jinja blocks (`{% block content %}`, `{% block sidebar_extra %}`, etc.) | Standard Jinja inheritance — `app.html` and `dashboard.html` expose named blocks a consumer's own templates can override selectively |
| `navigation.py` scope filtering | A consumer supplies `required_scope` per nav item; `greentechhub-core`'s permission check decides visibility — no UI-side branching needed |

The goal: a service should be able to add one custom widget or nav item without ever copy-pasting a shared template into its own repo.
