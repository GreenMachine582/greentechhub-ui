"""money / number / date — the display formatting every service was writing
as its own Jinja filters (upstreamed from PyFinBot's money/qty).

install() registers them as filters — {{ price|money }}, {{ units|number }},
{{ added|date }} — without replacing a filter the app already has. They're
plain functions too, e.g. for a CSV export:

    from greentechhub_ui.formatting import money

Every one returns "" for None or "", and the value as a string when it can't
be parsed, rather than raising and breaking the page. Floats go through
str() first, so 0.1 stays 0.1 instead of Decimal(0.1)'s binary expansion.
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def _decimal(value) -> Decimal | None:
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return d if d.is_finite() else None


def _quantize(d: Decimal, places: int) -> Decimal:
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def money(value, symbol: str = "$", places: int = 2) -> str:
    """1234.5 → "$1,234.50"; -1234.5 → "-$1,234.50" (sign before the
    symbol); rounded half-up, and never "-$0.00". symbol="" for none."""
    if value is None or value == "":
        return ""
    d = _decimal(value)
    if d is None:
        return str(value)
    d = _quantize(d, places)
    sign = "-" if d < 0 else ""  # a rounded-away negative is zero, unsigned
    return f"{sign}{symbol}{abs(d):,.{places}f}"


def number(value, places: int | None = None) -> str:
    """Full stored precision with trailing zeros dropped and thousands
    separators: Decimal("100.500") → "100.5", 100 → "100" (never "1E+2"),
    1234567.891 → "1,234,567.891". places=n gives n fixed decimals instead."""
    if value is None or value == "":
        return ""
    d = _decimal(value)
    if d is None:
        return str(value)
    if places is not None:
        d = _quantize(d, places)
        return f"{d + 0:,.{places}f}"  # + 0 turns -0.00 into 0.00
    d = d.normalize()
    return f"{d + 0:,f}"


def format_date(value, fmt: str | None = None) -> str:
    """A date, datetime or ISO string as "5 Feb 2025", or strftime(fmt)."""
    if value is None or value == "":
        return ""
    d = value
    if isinstance(value, str):
        try:
            d = datetime.fromisoformat(value.strip())
        except ValueError:
            return value
    if not isinstance(d, date):
        return str(value)
    if fmt:
        return d.strftime(fmt)
    # Not "%-d": Windows' strftime doesn't support it.
    return f"{d.day} {d:%b} {d.year}"


FILTERS = {"money": money, "number": number, "date": format_date}
