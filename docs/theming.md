[← Back to README](../README.md)

# 🎨 Theming & Static Assets

## Theming

- CSS custom properties (`--gth-color-primary`, `--gth-space-*`, `--gth-font-*`), defined in `theme/tokens.py` and layered on top of the vendored CSS framework's variables — override, don't fork it.
- Dark mode via a `data-theme` attribute toggled by a small Alpine.js component, persisted in `localStorage` — an internal implementation detail (see [docs/architecture.md](architecture.md#public-api-vs-implementation-details)), not something consumers write themselves.
- Brand tokens (colors, logo, favicon) sourced once from green-tech-hub.com's identity and reused everywhere, rather than each service picking its own accent color.
- Because `theme/` has no dependency on `components/` (see [docs/architecture.md](architecture.md#package-layout)), a service that only wants brand-consistent colors/typography without the full component library is already structurally possible — tracked as an open decision in [TODO.md](../TODO.md).

## Static asset hosting

- **Bundled per service (recommended to start)**: each FastAPI service mounts `greentechhub_ui.static` at `/static`; Django does the equivalent via `STATICFILES_DIRS`. Simple, no extra infra.
- **Shared static host** (`static.green-tech-hub.com`, fronted by Caddy): one copy, browser-cacheable across services. Worth it once there are enough services that duplication/versioning drift becomes a real annoyance — not needed for the first two consumers.

Either way, consumers never reference individual vendored files (`htmx.min.js`, `bootstrap.min.css`) by name — `app.html` resolves them internally, which is what keeps the "swap without breaking consumers" property true regardless of hosting choice.
