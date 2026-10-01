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
chrome, so gth_navbar uses it in light mode (logo_light_url). favicon.png is
logo-light.png's mark on a dark rounded-square tile, 64x64
(scripts/make_favicon.py): the mark is portrait, so even cropped tight it
looked narrow in a tab; the tile fills the square on any tab strip.
"""

BRAND_NAME = "GreenTechHub"
LOGO_ASSET_PATH = "logo/logo.png"
LOGO_LIGHT_ASSET_PATH = "logo/logo-light.png"
FAVICON_ASSET_PATH = "logo/favicon.png"

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
    gth_navbar's show_theme_toggle). logo_url (dark navbar), logo_light_url
    (light navbar) and favicon_url (the tab icon, the light variant's mark on
    a dark rounded-square tile) point at three assets — see the module
    docstring.
    """
    if show_logo:
        logo_url = f"{static_url_prefix}/{LOGO_ASSET_PATH}"
        logo_light_url = f"{static_url_prefix}/{LOGO_LIGHT_ASSET_PATH}"
        favicon_url = f"{static_url_prefix}/{FAVICON_ASSET_PATH}"
    else:
        logo_url = logo_light_url = favicon_url = None
    return {
        "name": BRAND_NAME,
        "logo_url": logo_url,
        # gth_navbar follows the color mode: on a light navbar it shows this
        # stronger-outlined variant instead of logo_url.
        "logo_light_url": logo_light_url,
        "favicon_url": favicon_url,
        "service_name": service_name,
    }
