[← Back to README](../README.md)

# 🧪 Testing & Developer Experience

## `/playground`

A minimal FastAPI demo app (`playground/`) ships in the same repo, rendering every shipped component with representative fixture data (no real database) — a filterable table, pagination, both toast delivery modes, a form with validation errors, dark mode toggled. No `gth-modal`/`gth-confirm-delete` demo yet — they haven't shipped. This is:

- **Living documentation** — the first place a contributor checks "what does `gth-table` actually look like" instead of reading macro source.
- **The Playwright smoke-test target** (below, not yet built) — tests will run against `playground/`, not against a mocked-up FastAPI app rebuilt per test.

See [playground/README.md](../playground/README.md) for concrete setup/run instructions and what to click through.

## Testing strategy

| Layer | Approach |
|---|---|
| Macro snapshot tests | Render each `gth-*` macro with representative inputs, assert output HTML against a stored snapshot — catches accidental markup changes (which would be a breaking change per [docs/versioning.md](versioning.md)) |
| HTML validation | Run rendered output through an HTML validator (e.g. `html5lib` or the W3C validator API) as part of CI — catches malformed markup the snapshot tests wouldn't flag |
| Playwright smoke tests | Run against `/playground`: open each modal, submit a form, trigger a toast, tab through a table with the keyboard, toggle dark mode — a small, fast suite, not full E2E coverage of consumer apps |
| Contract tests | Verify the [template context contract](contract.md) — a fixture supplying a minimal valid context renders without error, catching accidental new required context keys (which would be a breaking change) |

CI (GitHub Actions): lint (ruff for Python, an HTML/Jinja linter for templates) + the test layers above, same pattern as `greentechhub-core` and the services that consume it.
