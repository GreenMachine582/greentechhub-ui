# Vendored third-party assets

Every file below is vendored verbatim (unmodified, minified upstream build) so `app.html` and the icon font work
without depending on a public CDN staying up — see [docs/theming.md](../../../docs/theming.md) and
[docs/architecture.md](../../../docs/architecture.md). `app.html` never references these files by a hardcoded
path; it resolves them through the `*_url` globals documented in [docs/contract.md](../../../docs/contract.md),
so bumping a version here is a file-replacement + hash update, not a template change.

To update one: fetch the new version from its source URL, confirm the SHA256, replace the file in place, and
update its row below.

| File | Source | Version | SHA256 | Size |
|---|---|---|---|---|
| `css/bootstrap.min.css` | https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css | 5.3.3 | `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8` | 232,803 bytes |
| `js/bootstrap.bundle.min.js` | https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js | 5.3.3 | `0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c` | 80,721 bytes |
| `js/htmx.min.js` | https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js | 1.9.10 | `b3bdcf5c741897a53648b1207fff0469a0d61901429ba1f6e88f98ebd84e669e` | 47,755 bytes |
| `icons/bootstrap-icons.min.css` | https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css | 1.13.1 | `a5d6387a32ca3baec4d02336b5b3edab50c9dd518355576a011ea3dd9c1d884e` | 87,008 bytes |
| `icons/fonts/bootstrap-icons.woff2` | https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/fonts/bootstrap-icons.woff2 | 1.13.1 | `6c75710364a1ca5604267716f6d28997b26319fdb078cf11e0b42ab66ff2ea61` | 134,044 bytes |
| `logo/logo.png` | https://github.com/GreenMachine582/GreenTechHub/blob/cbc14090bd18878e646e09e7cc8dbe222fc3b2b1/addons/base/static/img/logo.png | commit `cbc1409` | `9c3b4d3749cfae4c1e1ac758dfecdabb1acf3a1d6f08b56e550955ce88cc83fe` | 3,799 bytes |

Not a third-party package like the rows above — `logo/logo.png` is vendored straight from the `GreenTechHub`
repo itself (our own production Django app), so "Version" is a commit SHA rather than a semver. GreenTechHub
reuses this exact file for its navbar logo, its `<link rel="icon">` favicon, and its `og:image` tag — there is
no separate dark-mode variant or standalone favicon file upstream to vendor, so `brand_context()`'s `logo_url`
and `favicon_url` both resolve to this one file (see `docs/theming.md`).

Not vendored: Alpine.js — nothing shipped uses it (dark mode is plain vanilla JS; `gth-modal` doesn't exist yet).
Revisit once a real component needs it — see `docs/architecture.md`'s internal interaction conventions.
