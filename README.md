# 🌱 greentechhub-ui

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-blue.svg)](TODO.md)
[![Jinja2](https://img.shields.io/badge/Jinja2-B41717.svg?logo=jinja&logoColor=white)](https://jinja.palletsprojects.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Django](https://img.shields.io/badge/Django-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![HTMX](https://img.shields.io/badge/HTMX-3D72D7.svg?logo=htmx&logoColor=white)](https://htmx.org/)

## 🎯 Objective

A shared, installable package (`greentechhub-ui`) providing the frontend every GreenTechHub-ecosystem service currently reinvents: base layout, Jinja2 component macros, static assets, and a shared theme — so every service looks and behaves like part of one product instead of a pile of unrelated internal tools. Consumers depend on `greentechhub-ui`'s components and contract, not on the specific frontend libraries behind them. It ships templates, macros, and assets only — no database, no server, nothing to deploy on its own; it's installed into a consuming service's app.

## 🧩 Scope

| Area | Contents |
|---|---|
| Templates | Base app shell (`app.html`) — extendable, not prescriptive about page content |
| Components (macros) | Layout: `gth-page-header`, `gth-card`, `gth-stat-card`, `gth-empty-state`, `gth-skeleton`, `gth-badge`, `gth-tabs`. Data: `gth-table`, `gth-pagination`, `gth-data-table` (+ `TableState`), `gth-tree`. Forms: `gth-form`, `gth-combobox`, `gth-multiselect`, `gth-record-picker`, `gth-segmented`, `gth-chips`, `gth-switch`, `gth-busy-button`. Feedback/overlays: `gth-toast`, `gth-modal`, `gth-confirm-delete`. Navigation: `gth-navbar`, `gth-sidebar`, `gth-command-palette` — see [docs/components.md](docs/components.md) |
| Static assets | Bundled internally — see [docs/theming.md](docs/theming.md) |
| Theme | CSS custom properties for color/spacing/typography, light + dark mode, brand tokens from green-tech-hub.com's visual identity |
| Navigation | A small Python helper (`navigation.py`) that renders a consistent navbar or sidebar from a per-service (optionally nested) list of `{label, url, icon, required_scope, children, badge…}` entries, and derives active state, breadcrumbs and the command palette's index from it |
| Template context contract | The interface every consuming app must supply — see [docs/contract.md](docs/contract.md), the centrepiece design decision of this package |
| Extension points | Documented hooks for consumers to add without forking — see [docs/extensibility.md](docs/extensibility.md) |

Bootstrap 5 and HTMX power the components internally but are **not public API** — consumers only ever call `gth-*` macros. See [docs/architecture.md](docs/architecture.md) for why that boundary matters.

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

## 🗺️ Status & Roadmap

v0.1–v0.4 are largely shipped — theme, navigation, core content/form/toast components, dark mode, a `/playground` demo app, and Playwright tests running in CI, with BottleBot's retrofit underway. The phased rollout (v0.1 → v1.0) is tracked as a living checklist in [TODO.md](TODO.md).

## 📄 License

[MIT](LICENSE) © 2026 Matthew Johnson
