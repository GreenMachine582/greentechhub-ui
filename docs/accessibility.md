[← Back to README](../README.md)

# ♿ Accessibility

First-class requirement, not an afterthought.

- **Keyboard navigation**: all interactive components (`gth-table` sort headers, `gth-modal`, `gth-pagination`) usable without a mouse; tab order verified as part of component review, not left implicit.
- **ARIA labels**: `gth-modal` sets `aria-labelledby` (pointing at its own title element) statically in the macro; `aria-modal` and `aria-hidden` are toggled at runtime by Bootstrap's own Modal JS (`static/js/bootstrap.bundle.min.js`) when it's shown/hidden, not hand-managed here. `gth-toast` carries `aria-live`/`aria-atomic`, `gth-table`'s sortable headers use `aria-sort` — all from the start, not retrofitted.
- **Color contrast**: theme tokens (see [docs/theming.md](theming.md)) checked against WCAG AA at definition time — a brand color that fails contrast gets a documented accessible variant, not a one-off override per page.
- **Focus management for modals**: opening `gth-modal` moves focus into it and traps it there until dismissed, then returns it to the triggering element — this comes directly from Bootstrap's native Modal JS (no `gth-*` JS involved), verified for real with a Playwright test (open → focus lands inside → Tab cycles → Esc closes → focus returns to trigger) rather than left to "Bootstrap probably handles it."
