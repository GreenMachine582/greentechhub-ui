[← Back to README](../README.md)

# ♿ Accessibility

First-class requirement, not an afterthought.

- **Keyboard navigation**: all interactive components (`gth-table` sort headers, `gth-modal`, `gth-pagination`) usable without a mouse; tab order verified as part of component review, not left implicit.
- **ARIA labels**: `gth-modal`, `gth-toast`, and `gth-table`'s sortable headers carry appropriate `aria-*` attributes (`role="dialog"`, `aria-live` for toasts, `aria-sort` for table headers) from the start, not retrofitted.
- **Color contrast**: theme tokens (see [docs/theming.md](theming.md)) checked against WCAG AA at definition time — a brand color that fails contrast gets a documented accessible variant, not a one-off override per page.
- **Focus management for HTMX-loaded modals**: when `gth-modal` content is swapped in via HTMX, focus moves into the modal and is trapped there until dismissed, then returns to the triggering element — this is the one HTMX+accessibility interaction that's easy to get wrong silently, so it's called out explicitly rather than left to "Bootstrap probably handles it."
