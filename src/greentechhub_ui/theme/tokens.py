"""Brand tokens — source of truth for theme.css's CSS custom properties.

Colors sourced from the real green-tech-hub.com brand palette
(GreenMachine582/GreenTechHub, addons/base/static/base/scss/abstracts/_variables.scss)
— resolves the color half of the "Logo/brand asset source of truth" open
decision in ../../TODO.md. The logo image itself is vendored at
static/logo/logo.png (see static/VENDORED.md); GreenTechHub reuses that same
file as its favicon too, so there's no separate light/dark/icon variant here.
"""

BRAND_NAME = "GreenTechHub"
LOGO_ASSET_PATH = "logo/logo.png"

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
    gth_navbar's show_theme_toggle).
    """
    logo_url = f"{static_url_prefix}/{LOGO_ASSET_PATH}" if show_logo else None
    return {
        "name": BRAND_NAME,
        "logo_url": logo_url,
        "favicon_url": logo_url,
        "service_name": service_name,
    }
