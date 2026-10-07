"""gth_filter_bar and gth_download_button: a filter row for a pane under a
plain gth_table, and the download link gth_data_table's export also uses."""

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "table.html" import gth_filter_bar, gth_download_button %}
{% from "select.html" import gth_select %}"""


def test_download_button():
    rendered = _render(IMPORT + """{{ gth_download_button("/reports/gains.csv?fy=2025") }}""")
    assert ('class="btn btn-outline-secondary gth-download" href="/reports/gains.csv?fy=2025"'
            " download>") in rendered
    assert '<i class="bi bi-download" aria-hidden="true"></i> CSV' in rendered
    labelled = _render(IMPORT + """{{ gth_download_button("/x.csv?a=1&b=2", "Export") }}""")
    assert 'href="/x.csv?a=1&amp;b=2"' in labelled and "</i> Export" in labelled


def test_filter_bar_with_fields_and_export():
    rendered = _render(IMPORT + """
        {% call gth_filter_bar("/reports/gains", "closest .tab-pane",
                               export_url="/reports/gains.csv?fy=2025") %}
          {{ gth_select("fy", "Financial year", [2024, 2025], value=2025, id="gains-fy",
                        field_class="mb-0") }}
        {% endcall %}""")
    assert_snapshot(rendered, "filter_bar")
    assert ('hx-get="/reports/gains" hx-target="closest .tab-pane" hx-trigger="change"'
            in rendered)
    assert rendered.index('id="gains-fy"') < rendered.index("gth-download")
    assert 'class="btn btn-outline-secondary ms-auto gth-download"' in rendered


def test_filter_bar_without_export():
    rendered = _render(IMPORT + """
        {% call gth_filter_bar("/r", "#pane", trigger="change delay:200ms") %}
          <input name="q">
        {% endcall %}""")
    assert "gth-download" not in rendered
    assert 'hx-target="#pane" hx-trigger="change delay:200ms"' in rendered
    assert '<input name="q">' in rendered
