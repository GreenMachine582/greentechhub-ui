[← Back to README](../README.md)

# 🧱 Component Catalogue

All macros are prefixed `gth-` and are the only public surface consumers should touch — see [docs/architecture.md](architecture.md#public-api-vs-implementation-details) for why.

| Macro | Purpose |
|---|---|
| `gth-page-header` | Title + breadcrumb + action-button slot, top of every page |
| `gth-card` | Standard bordered content container |
| `gth-stat-card` | Dashboard KPI tile (label, value, delta, icon) |
| `gth-table` | Sortable/filterable table shell — headers wired for HTMX-driven sort/filter requests, empty-state fallback built in |
| `gth-form` | Form wrapper with consistent label/validation-error layout |
| `gth-modal` | Generic modal, HTMX-loadable content slot, focus-trapped (see [docs/accessibility.md](accessibility.md)) |
| `gth-confirm-delete` / `gth-danger-modal` | Pre-built destructive-action confirmation modal |
| `gth-toast` | Renders `flashes` from the [template context contract](contract.md) as accessible toast notifications |
| `gth-pagination` | Renders page controls from `greentechhub-core`'s pagination envelope |
| `gth-breadcrumbs` | From `nav_items` + current route |
| `gth-empty-state` | "Nothing here yet" placeholder for empty tables/lists |
| `gth-sidebar` / `gth-navbar` | Renders `nav_items` (built-in + consumer-registered, see [docs/extensibility.md](extensibility.md)), scope-filtered against `current_user` |
