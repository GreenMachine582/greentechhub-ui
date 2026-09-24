[← Back to README](../README.md)

# ♿ Accessibility

First-class requirement, not an afterthought.

- **Keyboard navigation**: all interactive components (`gth-data-table` sort headers and pager, `gth-modal`, `gth-pagination`) usable without a mouse; tab order verified as part of component review, not left implicit.
- **ARIA labels**: `gth-modal` sets `aria-labelledby` (pointing at its own title element) statically in the macro; `aria-modal` and `aria-hidden` are toggled at runtime by Bootstrap's own Modal JS (`static/js/bootstrap.bundle.min.js`) when it's shown/hidden, not hand-managed here. `gth-toast` carries `aria-live`/`aria-atomic`, `gth-data-table`'s sortable headers use `aria-sort` — all from the start, not retrofitted.
- **Navigation vs. data trees (v0.8)** — two different ARIA patterns on purpose. `gth-sidebar` is a `<nav>` of
  lists with disclosure buttons (`aria-expanded`/`aria-controls`) — the APG navigation pattern; Tab moves through
  it like any links. `gth-tree` is the APG *tree view* (`role="tree"`/`treeitem`/`group`, roving tabindex, arrow
  keys), for data only; using it for site navigation would hide the links from screen readers' link lists.
  - `gth-sidebar`: the current page carries `aria-current="page"`. In the icon rail, labels stay in the
    accessibility tree (visually hidden) and show as tooltips on hover/focus; badges shrink to dots, so their text
    stays readable only in full mode and in the flyouts. Rail flyouts close with Esc (focus returns to the group
    button). Below 992px the drawer is Bootstrap's offcanvas: focus moves in, Esc closes, focus returns.
  - `gth-command-palette`: a modal `<dialog>` (the page behind is inert) holding a combobox + listbox with
    `aria-activedescendant`; Esc closes and returns focus to whatever opened it. The shortcut is advertised with
    `aria-keyshortcuts`.
  - `gth-tree`: ↑/↓ move, → expands (then enters the first child), ← collapses (then goes to the parent),
    Home/End, Enter activates, Space selects or checks, typing a letter jumps to the next matching node.
    Selection is `aria-selected` (single) or tri-state `aria-checked` including `mixed` (multi, with
    `aria-multiselectable`); the checkbox is drawn in CSS, its state is only ever the ARIA attribute. Lazy groups
    show a "Loading…" item to assistive tech.
- **Keyboard models for the v0.7 widgets** (each covered by a Playwright test):
  - `gth-data-table`: sort headers are `<button>`s inside `<th aria-sort>`; the pager is a `<nav aria-label>` of real links with `aria-current="page"`; infinite scroll keeps a "Load more" button reachable by Tab (`visually-hidden-focusable`) for keyboard and screen-reader users, who never trigger the scroll-into-view load.
  - `gth-tabs`: Bootstrap's own tab JS gives `role="tab"`/`tabpanel`, `aria-selected` and ←/→ between tabs; lazy panes show an `aria-hidden` skeleton until loaded.
  - `gth-combobox`/`gth-multiselect`: `role="combobox"` + `aria-activedescendant` (panel-scoped option ids); ↑/↓, Enter picks (never submits), Esc closes the panel (not an enclosing modal). Multiselect: Backspace on the empty input removes the last chip, every chip has a labelled remove button (removing one moves focus to the next chip rather than reopening the list), adds/removals go to a polite live region, and hitting `max_items` is both announced and shown as a toast. Unpicked typed text is cleared on blur so it can't pass for a selection. Tags mode highlights nothing until ↑/↓, so Enter creates what was typed.
  - `gth-record-picker`: the trigger is a `<button aria-haspopup="dialog" aria-expanded>`; the panel is `role="dialog"` with the field's label. Opening focuses its search box; ↓ enters the rows (focusable `<tr>`s), ↑/↓/Home/End move, Enter/Space picks, Esc closes the panel only and returns focus to the trigger. While inside a modal the panel lives in the `.modal` element so Bootstrap's focus trap doesn't pull focus back out. The header has a labelled ✕ and an Expand/Shrink toggle (`aria-pressed`); at modal size the panel is `aria-modal="true"`, Tab/Shift+Tab wrap inside it, and closing by any route (backdrop, ✕, Esc, a pick) returns focus to the trigger. An open picker takes Esc before an enclosing modal, even before its content has loaded.
  - `gth-chips`/`gth-badge`: state and meaning never rest on color alone — a check icon marks selected chips, badge labels carry the status.
- **Toasts (v0.8)**: warning/danger are `role="alert"` + `aria-live="assertive"`, success/info/neutral
  `role="status"` + `polite`; every toast is `aria-atomic`. The kind is carried by the icon *and* the text,
  never colour alone. The close button keeps contrast on every kind in both colour modes (the solid
  warning/info fills get Bootstrap's dark close, which dark mode would otherwise invert to white). An
  auto-hiding toast pauses while hovered or focused, so there's time to read or reach its action link;
  `duration=0` keeps it until closed.
- **Back to top (v0.8)**: a labelled button (`aria-label`), hidden until needed; activating it moves focus to
  `<main>` so keyboard and screen-reader users land at the top of the content, not on a button that then
  disappears.
- **Color contrast**: theme tokens (see [docs/theming.md](theming.md)) checked against WCAG AA at definition time — a brand color that fails contrast gets a documented accessible variant, not a one-off override per page.
- **Focus management for modals**: opening `gth-modal` moves focus into it and traps it there until dismissed, then returns it to the triggering element — this comes directly from Bootstrap's native Modal JS (no `gth-*` JS involved), verified for real with a Playwright test (open → focus lands inside → Tab cycles → Esc closes → focus returns to trigger) rather than left to "Bootstrap probably handles it."
