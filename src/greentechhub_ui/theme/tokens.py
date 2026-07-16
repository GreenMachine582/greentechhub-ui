"""Brand tokens — source of truth for theme.css's CSS custom properties.

No canonical green-tech-hub.com brand asset source exists yet (tracked as an
open decision in ../../TODO.md), so these are a placeholder green palette.
"""

BRAND_NAME = "GreenTechHub"
LOGO_URL = None  # placeholder until a canonical brand asset source is picked

COLOR_PRIMARY = "#2e7d32"
COLOR_PRIMARY_DARK = "#1b5e20"
COLOR_PRIMARY_LIGHT = "#66bb6a"


def brand_context(service_name: str | None = None) -> dict:
    """The `brand` context entry required by docs/contract.md."""
    return {
        "name": BRAND_NAME,
        "logo_url": LOGO_URL,
        "service_name": service_name,
    }
