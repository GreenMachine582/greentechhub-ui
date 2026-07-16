# 🌱 greentechhub-ui

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Status: Planning](https://img.shields.io/badge/Status-Planning-yellow.svg)](TODO.md)
[![Jinja2](https://img.shields.io/badge/Jinja2-B41717.svg?logo=jinja&logoColor=white)](https://jinja.palletsprojects.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Django](https://img.shields.io/badge/Django-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![HTMX](https://img.shields.io/badge/HTMX-3D72D7.svg?logo=htmx&logoColor=white)](https://htmx.org/)
[![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0.svg?logo=alpinedotjs&logoColor=white)](https://alpinejs.dev/)

> Shared UI framework for the GreenTechHub ecosystem. Provides reusable Jinja2 templates, components, theming, navigation, and static assets for FastAPI and Django applications, delivering a consistent, branded user experience while reducing duplicated frontend code across services.

## 🎯 Objective

A shared, installable package (`greentechhub-ui`) providing the frontend every GreenTechHub-ecosystem service currently reinvents: base layout, Jinja2 component macros, static assets, and a shared theme — so every service looks and behaves like part of one product instead of a pile of unrelated internal tools. Consumers depend on `greentechhub-ui`'s components and contract, not on the specific frontend libraries behind them.

## 💡 Why this now

- **BottleBot** already ships its own `templates/` + `static/style.css` + Bootstrap 5 + HTMX dashboard — its own navbar, its own card styling, its own overrides.
- **PyFinBot**'s web brief was about to build a second, independent copy of the same navbar/card/modal/toast pattern.
- **GreenTechHub** itself — the actual brand/hub site at green-tech-hub.com — runs **Django**, with its own templates, and is the one place a visitor would expect the "house style" to be authoritative.

Without a shared package, every new service (Market Watch, an eventual IAM/App Store) restarts this from zero, and nothing enforces that they end up looking related.

## 🧩 Scope

| Area | Contents |
|---|---|
| Templates | Base app shell (`app.html`), auth pages (`auth/login.html`), dashboard shell (`dashboard.html`) — extendable, not prescriptive about page content |
| Components (macros) | `gth-page-header`, `gth-card`, `gth-stat-card`, `gth-table`, `gth-form`, `gth-modal`, `gth-confirm-delete`, `gth-danger-modal`, `gth-toast`, `gth-pagination`, `gth-breadcrumbs`, `gth-empty-state`, `gth-sidebar`, `gth-navbar` |
| Static assets | Bundled internally — see [docs/theming.md](docs/theming.md) |
| Theme | CSS custom properties for color/spacing/typography, light + dark mode, brand tokens from green-tech-hub.com's visual identity |
| Navigation | A small Python helper (`navigation.py`) that renders a consistent nav/sidebar from a per-service list of `{label, url, icon, required_scope}` entries |
| Template context contract | The interface every consuming app must supply — see [docs/contract.md](docs/contract.md), the centrepiece design decision of this package |
| Extension points | Documented hooks for consumers to add without forking — see [docs/extensibility.md](docs/extensibility.md) |

Bootstrap 5, HTMX, and Alpine.js power the components internally but are **not public API** — consumers only ever call `gth-*` macros. See [docs/architecture.md](docs/architecture.md) for why that boundary matters.

## 📚 Docs

| Doc | Covers |
|---|---|
| [docs/contract.md](docs/contract.md) | 🔌 The framework-agnostic template context contract (read this first) |
| [docs/architecture.md](docs/architecture.md) | 🏗️ Public API boundary, package layout, FastAPI/Django integration, internal conventions |
| [docs/components.md](docs/components.md) | 🧱 Full `gth-*` component/macro catalogue |
| [docs/theming.md](docs/theming.md) | 🎨 Theme tokens, dark mode, static asset hosting |
| [docs/accessibility.md](docs/accessibility.md) | ♿ Keyboard nav, ARIA, contrast, focus management |
| [docs/testing.md](docs/testing.md) | 🧪 `/playground` demo app + testing strategy |
| [docs/versioning.md](docs/versioning.md) | 🏷️ Semver policy & distribution |
| [docs/extensibility.md](docs/extensibility.md) | 🧩 Extension points/hooks for consumers |
| [docs/migration.md](docs/migration.md) | 🔄 Migration path for BottleBot, PyFinBot, GreenTechHub |

## 🗺️ Status & Roadmap

This package is in the **planning phase** — no code has shipped yet. The phased rollout (v0.1 → v1.0) and open decisions are tracked as a living checklist in [TODO.md](TODO.md).

## 📄 License

[MIT](LICENSE) © 2026 Matthew Johnson
