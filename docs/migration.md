[← Back to README](../README.md)

# 🔄 Migration Path for Existing Services

- **BottleBot**: has a real, working UI to retrofit — highest-value proof of concept. Start with low-risk swaps (drop its custom `static/style.css` overrides in favor of the shared theme, replace its hand-rolled navbar with `gth-navbar`), then move component-by-component.
- **PyFinBot**: greenfield — builds directly on `gth-table`, `gth-form`, `gth-modal`, `gth-toast` from the start.
- **GreenTechHub**: lowest priority to migrate (Django, already has working templates, customer-facing rather than internal) — but worth wiring the Jinja2 backend early just to validate the [template context contract](contract.md) actually holds, even before porting its real pages. A natural first step for GreenTechHub specifically: adopt just `theme/` (see [docs/architecture.md](architecture.md#package-layout) and [docs/theming.md](theming.md)) for brand consistency before touching its component markup at all — exactly the use case the theme/components split open decision is about (see [TODO.md](../TODO.md)).

Progress against this migration is tracked per service in [TODO.md](../TODO.md#-migration-tracking).
