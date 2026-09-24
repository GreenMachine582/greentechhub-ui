"""Package directories and the default URL prefixes they're served under —
one source of truth for greentechhub_ui.static_dirs() and shell_globals()."""

from pathlib import Path

_package_dir = Path(__file__).parent

templates_path = _package_dir / "templates"
components_path = _package_dir / "components"
static_path = _package_dir / "static"
theme_path = _package_dir / "theme"

ASSETS_PREFIX = "/gth-assets"  # serves static_path (vendored Bootstrap/htmx/icons, gth JS)
THEME_PREFIX = "/gth-static"  # serves theme_path (theme.css)
