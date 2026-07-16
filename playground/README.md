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

- **Table** — search the task list; try a query with no matches (e.g. `zzz`) to see the row-level empty state.
- **Pagination** — click "Load more" on the widget list until it runs out (each click appends a new group, matching the real HTMX `hx-swap="outerHTML"` pattern this mirrors).
- **Form** — submit the budget field with a value in range (0–1000) to see the success toast fire, then with one out of range (e.g. `-5`) to see the inline validation error.
- **Toast** — click "Trigger a toast" for the standalone `HX-Trigger` demo.
- **Dark mode** — click the sun/moon toggle in the navbar; refresh the page to confirm the choice persists.

## Running the automated checks

```
pytest tests/test_playground_smoke.py
```

These test at the Jinja-render level (template compiles, expected markup present), not via a real HTTP client — `starlette.testclient` in this environment requires `httpx2`, and installing it hit a blocked sandbox permission check when the playground was built (see `TODO.md`). Live route behavior (status codes, `HX-Trigger` headers, HTMX partial swaps) is verified by running the app and testing it directly, same as above.
