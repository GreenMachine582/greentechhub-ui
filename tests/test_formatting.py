from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from jinja2 import Environment

import greentechhub_ui
from greentechhub_ui.formatting import format_date, format_datetime, money, number


@pytest.mark.parametrize(("value", "expected"), [
    (1234.5, "$1,234.50"),
    (Decimal("1234.5"), "$1,234.50"),
    (7, "$7.00"),
    ("12", "$12.00"),
    (-1234.5, "-$1,234.50"),  # the sign goes before the symbol
    (2.675, "$2.68"),  # half-up, and no float noise (2.675 is 2.67499… as a float)
    (-0.004, "$0.00"),  # rounds to zero: no "-$0.00"
    (None, ""),
    ("", ""),
    ("abc", "abc"),  # unparseable: shown as-is, never raises
])
def test_money(value, expected):
    assert money(value) == expected


def test_money_symbol_and_places():
    assert money(1234.5, "") == "1,234.50"
    assert money(1234.5, "€") == "€1,234.50"
    assert money(1234.5, places=0) == "$1,235"
    assert money(-5, "A$") == "-A$5.00"


@pytest.mark.parametrize(("value", "expected"), [
    (100, "100"),  # not "1E+2"
    (Decimal("100.500"), "100.5"),
    (1234567.891, "1,234,567.891"),
    (0.1, "0.1"),  # no binary expansion
    (Decimal("0E-8"), "0"),
    (-0.0, "0"),
    (1e-7, "0.0000001"),
    ("2.50", "2.5"),
    (None, ""),
    ("n/a", "n/a"),
    (Decimal("NaN"), "NaN"),
])
def test_number(value, expected):
    assert number(value) == expected


def test_number_fixed_places():
    assert number(1234.5, places=2) == "1,234.50"
    assert number(2.5, places=0) == "3"
    assert number(-0.001, places=2) == "0.00"


@pytest.mark.parametrize(("value", "expected"), [
    (date(2025, 2, 5), "5 Feb 2025"),
    (datetime(2025, 12, 25, 10, 30), "25 Dec 2025"),
    ("2025-02-05", "5 Feb 2025"),
    ("2025-02-05T10:00:00", "5 Feb 2025"),
    (None, ""),
    ("", ""),
    ("soon", "soon"),
    (42, "42"),
])
def test_format_date(value, expected):
    assert format_date(value) == expected


def test_format_date_custom_format():
    assert format_date(date(2025, 2, 5), "%Y-%m-%d") == "2025-02-05"
    assert format_date("2025-02-05T10:30:00", "%d/%m/%Y %H:%M") == "05/02/2025 10:30"


# ── v0.12: locale.date_format / locale.timezone / locale.time_format ──────

LATE_UTC = datetime(2025, 2, 5, 23, 30, tzinfo=UTC)  # 10:30 next morning in Sydney


@pytest.mark.parametrize(("code", "expected"), [
    ("iso", "2025-02-05"), ("dmy", "05/02/2025"), ("mdy", "02/05/2025"), ("long", "5 Feb 2025"),
    (None, "5 Feb 2025"), ("unknown", "5 Feb 2025"),
])
def test_format_date_codes(code, expected):
    assert format_date(date(2025, 2, 5), date_format=code) == expected


def test_format_date_converts_an_aware_datetime_to_the_viewers_day():
    assert format_date(LATE_UTC) == "5 Feb 2025"
    assert format_date(LATE_UTC, tz="Australia/Sydney") == "6 Feb 2025"
    iso = LATE_UTC.isoformat()
    assert format_date(iso, tz="Australia/Sydney", date_format="iso") == "2025-02-06"


def test_naive_values_and_unknown_zones_are_left_alone():
    naive = datetime(2025, 2, 5, 23, 30)
    assert format_date(naive, tz="Australia/Sydney") == "5 Feb 2025"
    assert format_date(LATE_UTC, tz="Not/AZone") == "5 Feb 2025"


def test_fmt_wins_over_the_options():
    assert format_date(LATE_UTC, "%Y", date_format="dmy", tz="Australia/Sydney") == "2025"


@pytest.mark.parametrize(("value", "kwargs", "expected"), [
    (datetime(2025, 2, 5, 13, 45), {}, "5 Feb 2025 13:45"),
    (datetime(2025, 2, 5, 13, 45), {"time_format": "12h"}, "5 Feb 2025 1:45 pm"),
    (datetime(2025, 2, 5, 0, 5), {"time_format": "12h"}, "5 Feb 2025 12:05 am"),
    (datetime(2025, 2, 5, 12, 0), {"time_format": "12h"}, "5 Feb 2025 12:00 pm"),
    (datetime(2025, 2, 5, 9, 0), {"date_format": "iso"}, "2025-02-05 09:00"),
    (LATE_UTC, {"tz": "Australia/Sydney", "date_format": "dmy"}, "06/02/2025 10:30"),
    (date(2025, 2, 5), {"time_format": "12h"}, "5 Feb 2025"),
    (None, {}, ""), ("", {}, ""), ("not a date", {}, "not a date"), (42, {}, "42"),
])
def test_format_datetime(value, kwargs, expected):
    assert format_datetime(value, **kwargs) == expected


def _render(source, **context):
    env = Environment()
    greentechhub_ui.install(env, service_name="T", nav_items=[])
    return env.from_string(source).render(**context)


def test_date_filter_reads_user_settings():
    prefs = {"locale.date_format": "dmy", "locale.timezone": "Australia/Sydney"}
    assert _render("{{ v|date }}", v=LATE_UTC) == "5 Feb 2025"
    assert _render("{{ v|date }}", v=LATE_UTC, user_settings=prefs) == "06/02/2025"
    assert _render('{{ v|date("%Y") }}', v=LATE_UTC, user_settings=prefs) == "2025"
    explicit = _render('{{ v|date(date_format="iso") }}', v=LATE_UTC, user_settings=prefs)
    assert explicit == "2025-02-06"


def test_datetime_filter_reads_user_settings():
    prefs = {"locale.date_format": "iso", "locale.timezone": "Australia/Sydney",
             "locale.time_format": "12h"}
    assert _render("{{ v|datetime }}", v=LATE_UTC) == "5 Feb 2025 23:30"
    assert _render("{{ v|datetime }}", v=LATE_UTC, user_settings=prefs) == "2025-02-06 10:30 am"


def test_filters_ignore_a_non_mapping_user_settings():
    assert _render("{{ v|date }}", v=LATE_UTC, user_settings="nope") == "5 Feb 2025"


# ── v0.12: locale.number_format ───────────────────────────────────────────

NBSP = "\u00a0"


@pytest.mark.parametrize(("code", "expected"), [
    ("comma_dot", "1,234,567.891"), ("dot_comma", "1.234.567,891"),
    ("space_comma", f"1{NBSP}234{NBSP}567,891"), (None, "1,234,567.891"),
    ("unknown", "1,234,567.891"),
])
def test_number_formats(code, expected):
    assert number(1234567.891, number_format=code) == expected


def test_number_format_with_places_negatives_and_small_values():
    assert number(-1234.5, 2, number_format="dot_comma") == "-1.234,50"
    assert number(999, number_format="dot_comma") == "999"
    assert number(0.5, number_format="space_comma") == "0,5"


def test_money_formats_keep_the_sign_and_symbol_outside_the_digits():
    assert money(-1234.5, number_format="dot_comma") == "-$1.234,50"
    assert money(1234.5, "", number_format="space_comma") == f"1{NBSP}234,50"
    assert money(1234.5, "€", places=0, number_format="dot_comma") == "€1.235"
    assert money(1234.5) == "$1,234.50"  # defaults unchanged, e.g. for CSV


def test_empty_and_garbage_are_unchanged_by_the_format():
    assert number(None, number_format="dot_comma") == ""
    assert money("", number_format="dot_comma") == ""
    assert number("n/a", number_format="dot_comma") == "n/a"


def test_money_and_number_filters_read_user_settings():
    prefs = {"locale.number_format": "dot_comma"}
    assert _render("{{ v|money }}", v=1234.5) == "$1,234.50"
    assert _render("{{ v|money }}", v=1234.5, user_settings=prefs) == "$1.234,50"
    assert _render('{{ v|money("€", places=0) }}', v=1234.5, user_settings=prefs) == "€1.235"
    assert _render("{{ v|number(2) }}", v=1234.5, user_settings=prefs) == "1.234,50"
    explicit = _render('{{ v|number(number_format="comma_dot") }}', v=1234.5,
                       user_settings=prefs)
    assert explicit == "1,234.5"
    assert _render("{{ v|number }}", v=1234.5, user_settings="nope") == "1,234.5"
