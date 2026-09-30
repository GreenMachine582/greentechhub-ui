from datetime import date, datetime
from decimal import Decimal

import pytest

from greentechhub_ui.formatting import format_date, money, number


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
