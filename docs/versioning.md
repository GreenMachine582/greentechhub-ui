[← Back to README](../README.md)

# 🏷️ Versioning & Distribution

- Own GitHub repo (`GreenMachine582/greentechhub-ui`), semver git tags, `pip`/`uv` git-dependency installs — no private index needed at this scale.
- **Explicit semver policy** (this is what makes the package feel like a framework rather than a shared template folder):
  - **Non-breaking (minor/patch)**: adding new CSS custom properties/tokens; adding new optional Jinja blocks to `app.html`/`dashboard.html`; adding new `gth-*` macros; adding new optional parameters to an existing macro (with defaults preserving current behavior).
  - **Breaking (major)**: changing an existing macro's required parameters or output structure/semantics; removing or renaming a CSS custom property a theme override might reference; changing the [template context contract](contract.md) to require a new key.
- Because this package ships **rendered markup and assets**, not just code, tag every release where component markup or the theme changes — a service silently picking up new markup on a routine upgrade is exactly the kind of surprise version pinning exists to prevent.
- **v0.7 visual change to note in the release**: `gth_navbar` now follows the color mode (light navbar in light mode) instead of always rendering `navbar-dark bg-dark` — a fix for the navbar ignoring light mode, but a visible output change for every consumer. Opt out with `gth_navbar(..., navbar_theme="dark")` / the `navbar_theme` global / `shell_globals(navbar_theme="dark")`. Dark-mode secondary buttons also got lighter (a contrast fix). Everything else in v0.7 is additive (new macros, new optional params, new optional globals).
- **v0.8 visual changes to note in the release**: toasts move from solid `text-bg-*` fills to the "surface"
  look (pass `variant="solid"` to `toast()` / a flash for the old style), and the navbar logo doubles to 48px
  (override `--gth-logo-height`; the navbar height follows). `layout="sidebar"`, the sidebar, palette, tree,
  back-to-top and nav badges are all opt-in or additive.
- A milestone in [TODO.md](../TODO.md) isn't ticked off until its version tag actually exists, matching `pyproject.toml`.
