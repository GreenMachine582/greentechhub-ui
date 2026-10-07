"""gth_stat_grid: gth_stat_cards in a responsive row/col grid."""

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "stat_card.html" import gth_stat_grid %}"""


def test_stat_grid():
    rendered = _render(IMPORT + """{{ gth_stat_grid([
        {"label": "Net gain/loss", "value": "$1,200.00", "value_tone": "good"},
        {"label": "Stocks sold", "value": 3, "delta": "+1", "delta_tone": "good",
         "icon": "graph-up"},
    ], cols=3) }}""")
    assert_snapshot(rendered, "stat_grid")
    assert '<div class="row g-3 gth-stat-grid mb-3">' in rendered
    assert rendered.count('<div class="col-6 col-md-4">') == 2
    assert "gth-stat-card-value text-success" in rendered
    assert "bi-graph-up" in rendered


def test_stat_grid_columns():
    def cols(**kw):
        source = """{{ gth_stat_grid([{"label": "A", "value": 1}], **kw) }}"""
        return _render(IMPORT + source, kw=kw)

    assert 'class="col-6 col-md-3"' in cols()
    assert 'class="col-6 col-md-6"' in cols(cols=2)
    assert 'class="col-6 col-md-3"' in cols(cols=5)  # unsupported: the default
    assert '<div class="row g-3 gth-stat-grid">' in cols(grid_class="")


def test_stat_grid_empty():
    assert "col-6" not in _render(IMPORT + "{{ gth_stat_grid([]) }}")
