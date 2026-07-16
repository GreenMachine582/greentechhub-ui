from pathlib import Path

from . import theme

_package_dir = Path(__file__).parent

templates_path = _package_dir / "templates"
components_path = _package_dir / "components"
static_path = _package_dir / "static"
theme_path = _package_dir / "theme"

__all__ = ["templates_path", "components_path", "static_path", "theme_path", "theme"]
