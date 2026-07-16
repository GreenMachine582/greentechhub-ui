from pathlib import Path

import html5lib
import pytest
from test_app_shell_renders import _context, _env

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
FRAGMENT_PARSER = html5lib.HTMLParser(strict=True)


@pytest.mark.parametrize(
    "snapshot_name",
    [
        "card",
        "stat_card",
        "stat_card_value_tone",
        "table_with_rows",
        "table_empty",
        "empty_state",
        "empty_state_with_action",
        "pagination_with_next",
        "pagination_no_next",
    ],
)
def test_macro_output_is_well_formed(snapshot_name):
    html = (SNAPSHOT_DIR / f"{snapshot_name}.html").read_text(encoding="utf-8")
    FRAGMENT_PARSER.parseFragment(html)


def test_app_shell_is_well_formed_document():
    html = _env().get_template("app.html").render(**_context())
    html5lib.HTMLParser(strict=True).parse(html)
