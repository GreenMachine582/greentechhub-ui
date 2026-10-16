"""formatting.pluralise: a count with the right form of a noun, as a Python
function (toasts built in route code) and as install()'s |pluralise filter."""

from decimal import Decimal

import pytest
from jinja2 import Environment

import greentechhub_ui
from greentechhub_ui import pluralise


@pytest.mark.parametrize("count,expected", [
    (1, "1 transaction"), (0, "0 transactions"), (3, "3 transactions"), (-1, "-1 transaction"),
    (1234, "1,234 transactions"), ("2", "2 transactions"), (Decimal("1.0"), "1 transaction"),
])
def test_counts(count, expected):
    assert pluralise(count, "transaction") == expected


def test_an_irregular_plural():
    assert pluralise(1, "entry", "entries") == "1 entry"
    assert pluralise(2, "entry", "entries") == "2 entries"


def test_the_noun_alone():
    assert pluralise(1, "stock", show_count=False) == "stock"
    assert pluralise(5, "entry", "entries", show_count=False) == "entries"


@pytest.mark.parametrize("count", [None, ""])
def test_empty_in_empty_out(count):
    assert pluralise(count, "transaction") == ""


@pytest.mark.parametrize("count,expected", [(1.5, "1.5 units"), ("lots", "lots units")])
def test_a_count_that_isnt_whole_is_shown_as_is_with_the_plural(count, expected):
    assert pluralise(count, "unit") == expected


def test_install_registers_the_filter():
    env = greentechhub_ui.install(Environment())
    template = env.from_string(
        '{{ n|pluralise("entry", "entries") }}|{{ n|pluralise("row", show_count=False) }}')
    assert template.render(n=1) == "1 entry|row"
    assert template.render(n=4) == "4 entries|rows"
