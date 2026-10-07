"""The tone and fy filters and gth_amount (v0.16): a signed amount coloured
by its sign, and a fiscal year label kept in step with greentechhub-core's."""

from decimal import Decimal

import pytest
from greentechhub_core.dates import fiscal_year_label as core_label
from jinja2 import Environment, FileSystemLoader

import greentechhub_ui
from greentechhub_ui.formatting import fiscal_year_label, tone


@pytest.mark.parametrize(("value", "places", "expected"), [
    (12.5, None, "text-success"),
    (Decimal("-0.01"), None, "text-danger"),
    ("-3", None, "text-danger"),
    (0, None, ""),
    (-0.004, None, "text-danger"),
    (-0.004, 2, ""),  # shown as $0.00, so not red
    (None, None, ""),
    ("", None, ""),
    ("n/a", None, ""),
])
def test_tone(value, places, expected):
    assert tone(value, places) == expected


@pytest.mark.parametrize(("value", "expected"), [
    (2024, "2024–25"), ("2024", "2024–25"), (1999, "1999–00"), (None, ""), ("", ""), ("all", "all"),
])
def test_fiscal_year_label(value, expected):
    assert fiscal_year_label(value) == expected


@pytest.mark.parametrize("start_month", [1, 4, 7, 10])
def test_fy_matches_core(start_month):
    for year in (1999, 2000, 2024, 2099):
        assert fiscal_year_label(year, start_month) == core_label(year, start_month)


def _env():
    env = Environment(loader=FileSystemLoader(greentechhub_ui.template_dirs()))
    return greentechhub_ui.install(env, service_name="T", nav_items=[])


def test_filters_are_installed():
    out = _env().from_string("{{ 2024|fy }} {{ -5|tone }}").render()
    assert out == "2024–25 text-danger"


def test_gth_amount():
    env = _env()
    source = '{% from "amount.html" import gth_amount %}{{ gth_amount(v, **kw) }}'

    def render(v, **kw):
        return env.from_string(source).render(v=v, kw=kw).strip()

    assert render(Decimal("1234.5")) == '<span class="gth-amount text-success">$1,234.50</span>'
    assert render(-12) == '<span class="gth-amount text-danger">-$12.00</span>'
    assert render(-0.004) == '<span class="gth-amount">$0.00</span>'
    assert render(None) == '<span class="gth-amount"></span>'
    assert (render(Decimal("-1.500"), kind="number", amount_class="fw-semibold")
            == '<span class="gth-amount text-danger fw-semibold">-1.5</span>')
