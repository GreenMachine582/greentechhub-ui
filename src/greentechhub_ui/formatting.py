"""money / number / date — the display formatting every service was writing
as its own Jinja filters (upstreamed from PyFinBot's money/qty).

install() registers them as filters — {{ price|money }}, {{ units|number }},
{{ added|date }} — without replacing a filter the app already has. They're
plain functions too, e.g. for a CSV export:

    from greentechhub_ui.formatting import money

Every one returns "" for None or "", and the value as a string when it can't
be parsed, rather than raising and breaking the page. Floats go through
str() first, so 0.1 stays 0.1 instead of Decimal(0.1)'s binary expansion.

date and datetime follow the viewer's preferences (v0.12): the filters read
greentechhub-core's locale.date_format / locale.timezone / locale.time_format
from the template's optional `user_settings` (greentechhub-fastapi's
settings_context supplies it). Without it, or with an explicit fmt, they
render exactly as before.
"""

from collections.abc import Mapping
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jinja2 import pass_context


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


# greentechhub-core's locale.date_format codes. Not "%-d": Windows' strftime
# doesn't support it, so "long" is assembled by hand.
DATE_FORMATS = {"iso": "%Y-%m-%d", "dmy": "%d/%m/%Y", "mdy": "%m/%d/%Y"}


def _parse(value) -> date | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError:
            return None
    return value if isinstance(value, date) else None


def _in_zone(d: date, tz: str | None) -> date:
    """An aware datetime converted to `tz`; anything else (a naive datetime, a
    plain date, an unknown zone or a host without tzdata) unchanged."""
    if not tz or not isinstance(d, datetime) or d.tzinfo is None:
        return d
    try:
        return d.astimezone(ZoneInfo(tz))
    except (ZoneInfoNotFoundError, ValueError):
        return d


def _date_part(d: date, date_format: str | None) -> str:
    pattern = DATE_FORMATS.get(date_format or "")
    return d.strftime(pattern) if pattern else f"{d.day} {d:%b} {d.year}"


def _time_part(d: datetime, time_format: str | None) -> str:
    if time_format == "12h":
        hour = d.hour % 12 or 12
        return f"{hour}:{d:%M} {'am' if d.hour < 12 else 'pm'}"
    return f"{d:%H:%M}"


def format_date(value, fmt: str | None = None, *, date_format: str | None = None,
                tz: str | None = None) -> str:
    """A date, datetime or ISO string as "5 Feb 2025", or strftime(fmt).

    date_format: core's locale.date_format code — iso (2025-02-05), dmy
    (05/02/2025), mdy (02/05/2025) or long (5 Feb 2025, the default).
    tz: an IANA zone an aware datetime is converted to first, so a late-night
    UTC timestamp lands on the viewer's day. fmt wins over date_format."""
    if value is None or value == "":
        return ""
    d = _parse(value)
    if d is None:
        return value if isinstance(value, str) else str(value)
    d = _in_zone(d, tz)
    if fmt:
        return d.strftime(fmt)
    return _date_part(d, date_format)


def format_datetime(value, fmt: str | None = None, *, date_format: str | None = None,
                    time_format: str | None = None, tz: str | None = None) -> str:
    """format_date plus the time: "5 Feb 2025 13:45" by default, or with
    time_format="12h" "5 Feb 2025 1:45 pm". A plain date has no time to show,
    so it renders as format_date would."""
    if value is None or value == "":
        return ""
    d = _parse(value)
    if d is None:
        return value if isinstance(value, str) else str(value)
    d = _in_zone(d, tz)
    if fmt:
        return d.strftime(fmt)
    if not isinstance(d, datetime):
        return _date_part(d, date_format)
    return f"{_date_part(d, date_format)} {_time_part(d, time_format)}"


def _preferences(context) -> Mapping:
    settings = context.get("user_settings")
    return settings if isinstance(settings, Mapping) else {}


@pass_context
def date_filter(context, value, fmt: str | None = None, **options) -> str:
    """{{ value|date }}: format_date, defaulting date_format and tz to the
    viewer's locale.date_format / locale.timezone from `user_settings`."""
    prefs = _preferences(context)
    options.setdefault("date_format", prefs.get("locale.date_format"))
    options.setdefault("tz", prefs.get("locale.timezone"))
    return format_date(value, fmt, **options)


@pass_context
def datetime_filter(context, value, fmt: str | None = None, **options) -> str:
    """{{ value|datetime }}: format_datetime, defaulting date_format,
    time_format and tz from `user_settings`."""
    prefs = _preferences(context)
    options.setdefault("date_format", prefs.get("locale.date_format"))
    options.setdefault("time_format", prefs.get("locale.time_format"))
    options.setdefault("tz", prefs.get("locale.timezone"))
    return format_datetime(value, fmt, **options)


FILTERS = {"money": money, "number": number, "date": date_filter,
           "datetime": datetime_filter}
