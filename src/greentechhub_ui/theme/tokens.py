"""Brand tokens — source of truth for theme.css's CSS custom properties.

Colors sourced from the real green-tech-hub.com brand palette
(GreenMachine582/GreenTechHub, addons/base/static/base/scss/abstracts/_variables.scss)
— resolves the color half of the "Logo/brand asset source of truth" open
decision in ../../TODO.md. Logo image assets aren't vendored yet.
"""

BRAND_NAME = "GreenTechHub"
LOGO_URL = None  # logo image assets not vendored yet — see TODO.md

COLOR_PRIMARY = "#1FBE1E"
COLOR_PRIMARY_DARK = "#169617"
COLOR_PRIMARY_LIGHT = "#A6EBA6"


def brand_context(service_name: str | None = None) -> dict:
    """The `brand` context entry required by docs/contract.md."""
    return {
        "name": BRAND_NAME,
        "logo_url": LOGO_URL,
        "service_name": service_name,
    }
