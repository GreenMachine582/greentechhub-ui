"""Brand tokens — source of truth for theme.css's CSS custom properties.

Colors sourced from the real green-tech-hub.com brand palette
(GreenMachine582/GreenTechHub, addons/base/static/base/scss/abstracts/_variables.scss)
— resolves the color half of the "Logo/brand asset source of truth" open
decision in ../../TODO.md. The logo images are original artwork at
static/logo/ (see static/VENDORED.md) designed for greentechhub-ui's own
brand identity — they intentionally diverge from GreenTechHub production's
current logo file, not a copy of it. Two variants: logo.png is tuned for
gth-navbar's hardcoded dark background; logo-light.png has a much stronger
outline for the unpredictable (often light) background of a browser's
favicon chrome, so brand_context() uses it for favicon_url specifically.
"""

BRAND_NAME = "GreenTechHub"
LOGO_ASSET_PATH = "logo/logo.png"
LOGO_LIGHT_ASSET_PATH = "logo/logo-light.png"

COLOR_PRIMARY = "#1FBE1E"
COLOR_PRIMARY_DARK = "#169617"
COLOR_PRIMARY_LIGHT = "#A6EBA6"


def brand_context(
    service_name: str | None = None,
    show_logo: bool = False,
    static_url_prefix: str = "/static",
) -> dict:
    """The `brand` context entry required by docs/contract.md.

    `show_logo` defaults to False so adopting this doesn't change any
    existing consumer's rendered output until they opt in (same pattern as
    gth_navbar's show_theme_toggle). logo_url (navbar) and favicon_url
    (browser chrome) intentionally point at different assets — see the
    module docstring.
    """
    if show_logo:
        logo_url = f"{static_url_prefix}/{LOGO_ASSET_PATH}"
        favicon_url = f"{static_url_prefix}/{LOGO_LIGHT_ASSET_PATH}"
    else:
        logo_url = None
        favicon_url = None
    return {
        "name": BRAND_NAME,
        "logo_url": logo_url,
        "favicon_url": favicon_url,
        "service_name": service_name,
    }
