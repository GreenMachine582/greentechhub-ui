[← Back to README](../README.md)

# 🧩 Extension Points

Documented hooks so consumers can extend without forking or copying templates:

| Hook | Use case |
|---|---|
| `nav_items` context entry (custom items) | A service adds its own sidebar/navbar links alongside the shared ones — build the list via `greentechhub_ui.navigation.build_nav_items(custom_items=[...])` (see [docs/components.md](components.md#shipped-signatures-v04)) rather than assembling it by hand, so built-in items and per-request permission filtering apply automatically |
| `extra_head` context entry | Per-page `<head>` additions (a service-specific meta tag, a chart library's CSS) rendered into `app.html`'s head block without editing the shared template |
| `extra_css` / `extra_js` slots | A consumer injects one additional stylesheet/script (e.g. a page needing a charting library) without vendoring it into `greentechhub-ui` itself |
| Custom Jinja blocks (`{% block content %}`, `{% block sidebar_extra %}`, etc.) | Standard Jinja inheritance — `app.html` exposes named blocks a consumer's own templates can override selectively. `sidebar_extra` (layout="sidebar" only) fills the sidebar's footer, beside the rail toggle — e.g. a version string. The user menu lives in the navbar (`current_user`), so this slot stays the service's |
| Nested `nav_items` (v0.8) | Items with `children` become sidebar groups (and navbar dropdowns); `badge` / `badge_url` + `badge_event` add counts a response can refresh via `toast(..., events=[...])`; `match="exact"` stops prefix matching. Breadcrumbs (`nav_breadcrumbs`) and the command palette's index (`nav_flatten`) derive from the same list, so one nav definition drives all three |
| `navigation.py` permission filtering | A consumer sets `required_permission` (or the older `required_scope`) per nav item and passes the viewer's `granted` permissions (greentechhub-core's `RoleResolver`) as context; `app.html` hides what they can't use — no UI-side branching needed |

The goal: a service should be able to add one custom widget or nav item without ever copy-pasting a shared template into its own repo.
