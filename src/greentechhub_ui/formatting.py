"""money / number / date / tone / fy — the display formatting every service was writing
as its own Jinja filters (upstreamed from PyFinBot's money/qty).

install() registers them as filters — {{ price|money }}, {{ units|number }},
{{ added|date }} — without replacing a filter the app already has. They're
plain functions too, e.g. for a CSV export:

    from greentechhub_ui.formatting import money

Every one returns "" for None or "", and the value as a string when it can't
be parsed, rather than raising and breaking the page. Floats go through
str() first, so 0.1 stays 0.1 instead of Decimal(0.1)'s binary expansion.

The filters follow the viewer's preferences (v0.12), from the template's
optional `user_settings` (greentechhub-fastapi's settings_context supplies
it): date and datetime read greentechhub-core's locale.date_format /
locale.timezone / locale.time_format, money and number read
locale.number_format. Without it, or with explicit arguments, they render
exactly as before — and so do the plain functions, e.g. for CSV.
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


# greentechhub-core's locale.number_format codes → (thousands, decimal)
# separators. The space form uses a non-breaking space so a number never wraps.
NUMBER_FORMATS = {"comma_dot": (",", "."), "dot_comma": (".", ","), "space_comma": ("\u00a0", ",")}


def _separate(text: str, number_format: str | None) -> str:
    """Python's "1,234.56" with the separators of `number_format`; an unknown
    or missing format keeps comma_dot."""
    thousands, decimal = NUMBER_FORMATS.get(number_format or "", (",", "."))
    if (thousands, decimal) == (",", "."):
        return text
    return "".join(thousands if c == "," else decimal if c == "." else c for c in text)


def money(value, symbol: str = "$", places: int = 2, *, number_format: str | None = None) -> str:
    """1234.5 → "$1,234.50"; -1234.5 → "-$1,234.50" (sign before the
    symbol); rounded half-up, and never "-$0.00". symbol="" for none.
    number_format: core's locale.number_format code — comma_dot (the default),
    dot_comma ("$1.234,50") or space_comma ("$1 234,50")."""
    if value is None or value == "":
        return ""
    d = _decimal(value)
    if d is None:
        return str(value)
    d = _quantize(d, places)
    sign = "-" if d < 0 else ""  # a rounded-away negative is zero, unsigned
    return f"{sign}{symbol}{_separate(f'{abs(d):,.{places}f}', number_format)}"


def number(value, places: int | None = None, *, number_format: str | None = None) -> str:
    """Full stored precision with trailing zeros dropped and thousands
    separators: Decimal("100.500") → "100.5", 100 → "100" (never "1E+2"),
    1234567.891 → "1,234,567.891". places=n gives n fixed decimals instead.
    number_format as for money."""
    if value is None or value == "":
        return ""
    d = _decimal(value)
    if d is None:
        return str(value)
    if places is not None:
        d = _quantize(d, places)
        return _separate(f"{d + 0:,.{places}f}", number_format)  # + 0 turns -0.00 into 0.00
    d = d.normalize()
    return _separate(f"{d + 0:,f}", number_format)


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


@pass_context
def money_filter(context, value, symbol: str = "$", places: int = 2, **options) -> str:
    """{{ value|money }}: money, defaulting number_format to the viewer's
    locale.number_format from `user_settings`."""
    options.setdefault("number_format", _preferences(context).get("locale.number_format"))
    return money(value, symbol, places, **options)


@pass_context
def number_filter(context, value, places: int | None = None, **options) -> str:
    """{{ value|number }}: number, defaulting number_format as money_filter does."""
    options.setdefault("number_format", _preferences(context).get("locale.number_format"))
    return number(value, places, **options)


def tone(value, places: int | None = None) -> str:
    """The text colour class for a signed amount: "text-success" above zero,
    "text-danger" below, "" at zero or for anything unparseable (v0.16).
    places: judge the value as rounded to that many decimals, so -0.004
    shown as "$0.00" isn't red."""
    d = _decimal(value) if value is not None and value != "" else None
    if d is None:
        return ""
    if places is not None:
        d = _quantize(d, places)
    return "text-success" if d > 0 else "text-danger" if d < 0 else ""


def fiscal_year_label(fy, start_month: int = 7) -> str:
    """FY 2024 → "2024–25" (an en dash and the two-digit end year; "1999–00"
    across a century), or "2024" when start_month=1, the calendar year:
    greentechhub-core's dates.fiscal_year_label, which this package doesn't
    import at runtime (a test keeps the two in step). "" for None or "", and
    the value as a string when it isn't a year (v0.16)."""
    if fy is None or fy == "":
        return ""
    try:
        year = int(fy)
    except (TypeError, ValueError):
        return str(fy)
    if start_month == 1:
        return str(year)
    return f"{year}–{(year + 1) % 100:02d}"


FILTERS = {"money": money_filter, "number": number_filter, "date": date_filter,
           "datetime": datetime_filter, "tone": tone, "fy": fiscal_year_label}
