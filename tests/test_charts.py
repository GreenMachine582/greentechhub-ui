"""charts.html: gth_sparkline, gth_bar_chart and gth_line_chart (server-rendered
SVG, no JS), and gth_stat_card's chart slot."""

import re
from decimal import Decimal

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "charts.html" import gth_sparkline, gth_bar_chart, gth_line_chart %}"""


def _chart(source: str, **context) -> str:
    return _render(IMPORT + source, **context)


def _attr(html: str, element: str, attr: str) -> list[str]:
    return re.findall(rf'<{element}\b[^>]*\b{attr}="([^"]*)"', html)


# --- gth_sparkline -----------------------------------------------------------

def test_sparkline():
    rendered = _chart("""{{ gth_sparkline([10, 12, 9, 15, 14], label="Cost base", prefix="$") }}""")
    assert_snapshot(rendered, "sparkline")
    assert 'role="img"' in rendered
    assert 'aria-label="Cost base: from $10 to $14, low $9, high $15"' in rendered
    assert 'class="gth-sparkline gth-chart-primary"' in rendered


def test_sparkline_points_span_the_box():
    rendered = _chart("""{{ gth_sparkline([1, 3, 2], width=100, height=20, fill=False) }}""")
    (points,) = _attr(rendered, "polyline", "points")
    xs = [float(p.split(",")[0]) for p in points.split()]
    ys = [float(p.split(",")[1]) for p in points.split()]
    assert xs == [2.0, 50.0, 98.0]
    assert ys[1] == 2.0 and ys[0] == 18.0  # the high at the top, the low at the bottom
    assert "<polygon" not in rendered


def test_sparkline_trend_tone():
    assert "gth-chart-good" in _chart("""{{ gth_sparkline([3, 1, 4], tone="trend") }}""")
    assert "gth-chart-bad" in _chart("""{{ gth_sparkline([3, 5, 2], tone="trend") }}""")


def test_sparkline_one_value_and_none():
    one = _chart("""{{ gth_sparkline([Decimal("7.5")], places=1) }}""", Decimal=Decimal)
    assert '<circle class="gth-chart-dot"' in one and 'aria-label="7.5"' in one
    flat = _chart("""{{ gth_sparkline([4, 4]) }}""")
    assert _attr(flat, "polyline", "points") == ["2.00,14.00 94.00,14.00"]
    empty = _chart("""{{ gth_sparkline([], label="Dividends") }}""")
    assert 'aria-label="Dividends: no data"' in empty and "<polyline" not in empty


# --- gth_bar_chart ------------------------------------------------------------

def test_bar_chart_signed():
    rendered = _chart("""{{ gth_bar_chart(
        [("2023–24", 1200), ("2024–25", -300), {"label": "2025–26", "value": "800"}],
        "Gains by FY", tone="signed", prefix="$") }}""")
    assert_snapshot(rendered, "bar_chart_signed")
    assert [c.split()[-1] for c in _attr(rendered, "rect", "class")] == [
        "gth-chart-good", "gth-chart-bad", "gth-chart-good"]
    # 1,200 above zero and 300 below: zero sits at 80% of the height.
    assert _attr(rendered, "line", "y1") == ["80.00%"]
    assert _attr(rendered, "rect", "height")[1] == "20.00%"
    assert "<title>2024–25: -$300</title>" in rendered
    assert '<span style="top: 80.00%">$0</span>' in rendered
    assert '<th scope="row">2024–25</th><td>-$300</td>' in rendered  # the hidden data table


def test_bar_chart_all_positive_starts_at_zero():
    rendered = _chart("""{{ gth_bar_chart([("a", 5), ("b", 10)], "Units") }}""")
    assert _attr(rendered, "rect", "y") == ["50.00%", "0.00%"]
    assert _attr(rendered, "rect", "height") == ["50.00%", "100.00%"]
    assert 'top: 100%">0</span>' in rendered
    assert rendered.count("gth-chart-primary") == 2


def test_bar_chart_thins_x_labels():
    items = [(f"M{i}", i) for i in range(24)]
    rendered = _chart("""{{ gth_bar_chart(items, "Monthly", max_x_labels=6) }}""",
                      items=items)
    x_axis = rendered.split('class="gth-chart-x"')[1].split("</div>")[0]
    shown = re.findall(r"<span>([^<]+)</span>", x_axis)
    assert shown == ["M0", "M4", "M8", "M12", "M16", "M23"]  # not M20, which would crowd M23
    assert rendered.count("<title>") == 24


def test_bar_chart_options_and_empty():
    hidden = _chart("""{{ gth_bar_chart([("a", 1)], "Secret", show_label=False,
        columns=("FY", "Gain"), chart_class="my-chart", places=2, suffix="%") }}""")
    assert '<figcaption class="gth-chart-caption visually-hidden">Secret</figcaption>' in hidden
    assert '<th scope="col">FY</th><th scope="col">Gain</th>' in hidden
    assert 'class="gth-chart gth-bar-chart my-chart"' in hidden
    assert "<td>1.00%</td>" in hidden
    empty = _chart("""{{ gth_bar_chart([], "Nothing") }}""")
    assert "No data." in empty and "<svg" not in empty


# --- gth_line_chart -----------------------------------------------------------

def test_line_chart():
    rendered = _chart("""{{ gth_line_chart([("Jul", 0), ("Aug", 50), ("Sep", 100)], "Cost base",
        prefix="$") }}""")
    assert_snapshot(rendered, "line_chart")
    assert _attr(rendered, "polyline", "points") == ["0.00,100.00 50.00,50.00 100.00,0.00"]
    assert _attr(rendered, "polygon", "points") == [
        "0,100 0.00,100.00 50.00,50.00 100.00,0.00 100,100"]
    assert 'preserveAspectRatio="none"' in rendered


def test_line_chart_fit_to_data():
    zeroed = _chart("""{{ gth_line_chart([("a", 90), ("b", 100)], "Price") }}""")
    assert _attr(zeroed, "polyline", "points") == ["0.00,10.00 100.00,0.00"]
    fitted = _chart(
        """{{ gth_line_chart([("a", 90), ("b", 100)], "Price", zero=False, fill=False) }}""")
    assert _attr(fitted, "polyline", "points") == ["0.00,100.00 100.00,0.00"]
    assert "<polygon" not in fitted
    assert 'top: 100%">90</span>' in fitted


def test_line_chart_crossing_zero_draws_the_baseline():
    rendered = _chart("""{{ gth_line_chart([("a", -10), ("b", 30)], "Net") }}""")
    assert _attr(rendered, "line", "y1") == ["75.00"]


def test_line_chart_x_labels_sit_at_their_points():
    items = [(m, i) for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May"])]
    rendered = _chart("""{{ gth_line_chart(items, "Monthly", max_x_labels=3) }}""", items=items)
    x_axis = rendered.split('class="gth-chart-x"')[1].split("</div>")[0]
    assert re.findall(r'left: ([\d.]+)%">(\w+)<', x_axis) == [
        ("0.00", "Jan"), ("50.00", "Mar"), ("100.00", "May")]


def test_line_chart_one_point_and_empty():
    one = _chart("""{{ gth_line_chart([("Now", 5)], "One") }}""")
    assert _attr(one, "polyline", "points") == ["0,0.00 100,0.00"]
    assert "No data." in _chart("""{{ gth_line_chart([], "None") }}""")


# --- gth_stat_card's chart slot -------------------------------------------------

def test_stat_card_with_a_sparkline():
    rendered = _render("""{% from "stat_card.html" import gth_stat_card %}""" + IMPORT + """
        {{ gth_stat_card("Cost base", "$1,400",
            chart=gth_sparkline([10, 14], label="Cost base", prefix="$")) }}""")
    assert_snapshot(rendered, "stat_card_with_chart")
    assert '<div class="gth-stat-card-chart"><svg class="gth-sparkline' in rendered


def test_stat_card_without_a_chart_is_unchanged():
    rendered = _render(
        """{% from "stat_card.html" import gth_stat_card %}{{ gth_stat_card("A", 1) }}""")
    assert "gth-stat-card-chart" not in rendered
    assert rendered.rstrip().endswith(
        '<div class="metric-value gth-stat-card-value">1</div>\n  \n</div>')
