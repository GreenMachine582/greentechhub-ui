"""Framework-neutral wiring helpers — what every consumer (FastAPI's
Jinja2Templates, Django's Jinja2 backend, a bare jinja2.Environment) was
hand-writing: the template loader chain, the two static directories, and
rendering one macro for an htmx endpoint. Only jinja2 and the stdlib here;
the framework-specific halves (mounting, responses) live in the adapters
(greentechhub_fastapi.templating / .htmx, and gth-django's equivalents).
"""

from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from greentechhub_ui._paths import (
    ASSETS_PREFIX,
    THEME_PREFIX,
    components_path,
    static_path,
    templates_path,
    theme_path,
)
from greentechhub_ui.shell import shell_globals

_INSTALLED = "_greentechhub_ui_installed"


def template_dirs() -> list[Path]:
    """Where app.html and the gth_* component macros live — e.g. Django's
    TEMPLATES[...]["DIRS"] for its Jinja2 backend, after the project's own."""
    return [templates_path, components_path]


def static_dirs(
    assets_prefix: str = ASSETS_PREFIX, theme_prefix: str = THEME_PREFIX
) -> dict[str, Path]:
    """URL prefix → directory to serve there. Pass the same prefixes to
    shell_globals() (or leave both at their defaults) so the asset URLs it
    renders match. FastAPI: greentechhub_fastapi.templating.mount_static_dirs
    (app, static_dirs()). Django: STATICFILES_DIRS = [(prefix.strip("/"),
    path) for prefix, path in static_dirs().items()] — prefixed entries."""
    return {assets_prefix: static_path, theme_prefix: theme_path}


def install(env: Environment, **shell_kwargs: Any) -> Environment:
    """Make gth-ui's templates loadable from `env` — after the env's own
    loader, so an app template of the same name wins — and, given
    shell_globals() keyword arguments (service_name, nav_items, layout, …),
    install those globals too. Safe to call twice (the loader is added once).
    Returns env, for Django's `environment` callable:

        def environment(**options):
            return greentechhub_ui.install(Environment(**options), service_name="…", nav_items=[…])
    """
    if not getattr(env, _INSTALLED, False):
        ui_loaders = [FileSystemLoader(str(path)) for path in template_dirs()]
        env.loader = ChoiceLoader([env.loader, *ui_loaders] if env.loader else ui_loaders)
        setattr(env, _INSTALLED, True)
    if shell_kwargs:
        env.globals.update(shell_globals(**shell_kwargs))
    return env


def render_macro(env: Environment, template: str, macro: str, *args: Any, **kwargs: Any) -> str:
    """Render one macro to a string, e.g. an htmx endpoint returning a live
    nav badge: render_macro(env, "badge.html", "gth_badge", "3", "warn").
    Goes through the template's module, so env globals (nav_flatten, …) are
    in scope as they are for a full page. Macros that need a {% call %} body
    can't be rendered this way — use a small template for those."""
    return getattr(env.get_template(template).module, macro)(*args, **kwargs)
