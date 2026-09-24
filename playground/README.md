# Playground

A minimal FastAPI app exercising every shipped `gth-*` component with fixture data — see [docs/testing.md](../docs/testing.md) for why it exists.

## Setup

From the repo root, in a venv:

```
pip install -e ".[dev,playground]"
```

## Run

```
python playground/app.py
```

(`uv run playground/app.py` works equivalently if you use `uv`.)

Open **http://127.0.0.1:8500/**.

## What to try

The playground itself runs in `app.html`'s `layout="sidebar"`: one page per category (Layout, Data, Forms,
Feedback, Overlays, Navigation, Extensibility), each demo an anchor the sidebar links to. Press
<kbd>Ctrl</kbd>+<kbd>K</kbd> (<kbd>⌘K</kbd>) to jump to any of them, collapse the sidebar to an icon rail with the
button at its bottom, or narrow the window below 992px for the drawer.

- **Table** (Data) — search the task list; try a query with no matches (e.g. `zzz`) to see the row-level empty state.
- **Pagination** (Data) — click "Load more" on the widget list until it runs out (each click appends a new group, matching the real HTMX `hx-swap="outerHTML"` pattern this mirrors).
- **Form** (Forms) — submit the budget field with a value in range (0–1000) to see the success toast fire, then with one out of range (e.g. `-5`) to see the inline validation error.
- **Toast** (Feedback) — click "Trigger a toast" for the standalone `HX-Trigger` demo.
- **Tables** (`/tables`) — the same `gth_data_table` in each `TableState` mode (pages, load more, infinite, infinite inside a scroll box, none): sort by a header, search, filter by category, change page size; in pages mode the URL follows along (`push_url`), so reload/back work.
- **Tree** (`/tree`) — keyboard-drive the parts tree (arrows, Home/End, letters), expand an assembly to lazy-load its parts, pick one for the detail pane, and tick categories/assemblies/parts in the tri-state form.
- **Sidebar demo** (`/layouts/sidebar`) — a standalone `layout="sidebar"` page with deeper nesting, badges (one live: resolve issues to watch it count down) and a server-searched command palette.
- **Dark mode** — click the sun/moon toggle in the navbar; refresh the page to confirm the choice persists.

## Running the automated checks

```
pytest tests/test_playground_smoke.py tests/test_playground_routes.py
```

`test_playground_smoke.py` tests at the Jinja-render level (template compiles, expected markup present) —
fast, and catches macro drift. `test_playground_routes.py` runs the same app through a real ASGI HTTP
client (`httpx` + `ASGITransport`), covering status codes, `HX-Trigger` headers, and HTMX partial-swap
response bodies (see [docs/testing.md](../docs/testing.md)).
