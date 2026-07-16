[← Back to README](../README.md)

# 🏷️ Versioning & Distribution

- Own GitHub repo (`GreenMachine582/greentechhub-ui`), semver git tags, `pip`/`uv` git-dependency installs — no private index needed at this scale.
- **Explicit semver policy** (this is what makes the package feel like a framework rather than a shared template folder):
  - **Non-breaking (minor/patch)**: adding new CSS custom properties/tokens; adding new optional Jinja blocks to `app.html`/`dashboard.html`; adding new `gth-*` macros; adding new optional parameters to an existing macro (with defaults preserving current behavior).
  - **Breaking (major)**: changing an existing macro's required parameters or output structure/semantics; removing or renaming a CSS custom property a theme override might reference; changing the [template context contract](contract.md) to require a new key.
- Because this package ships **rendered markup and assets**, not just code, tag every release where component markup or the theme changes — a service silently picking up new markup on a routine upgrade is exactly the kind of surprise version pinning exists to prevent.
