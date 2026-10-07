"""gth_result_panel and gth_live_region: an operation's result card (or its
error alert), and the region an htmx form swaps it into."""

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "result_panel.html" import gth_result_panel %}"""


def test_badges_problems_and_link():
    rendered = _render(IMPORT + """
        {{ gth_result_panel("Results — trades.csv",
            badges=[("12 rows", "neutral"), {"label": "10 imported", "tone": "good"}],
            problems=["Row 3: no date", "Row 7: unknown stock"],
            link=("/transactions", "View transactions")) }}""")
    assert_snapshot(rendered, "result_panel")
    assert '<div class="card-header gth-card-header">Results — trades.csv</div>' in rendered
    assert rendered.count('class="badge') == 2
    assert "<li>Row 3: no date</li>" in rendered
    assert ('<a href="/transactions" class="btn btn-outline-primary btn-sm">View transactions</a>'
            in rendered)
    assert "alert" not in rendered


def test_empty_parts_are_left_out():
    rendered = _render(IMPORT + """
        {{ gth_result_panel("Synced", link={"url": "/x", "label": "Open"}) }}""")
    assert "gth-result-badges" not in rendered
    assert "gth-result-problems" not in rendered and "<h6>" not in rendered
    assert '<a href="/x"' in rendered


def test_a_call_body_comes_after_the_problems():
    rendered = _render(IMPORT + """
        {% call gth_result_panel("Results", problems=["Two rows failed"]) %}
        <table id="row-errors"></table>
        {% endcall %}""")
    assert rendered.index("Two rows failed") < rendered.index('id="row-errors"')


def test_an_error_is_a_danger_alert_instead():
    rendered = _render(IMPORT + """
        {{ gth_result_panel("Email sync", badges=[("1 new", "good")], error="IMAP login failed",
            error_action={"label": "Open Settings", "url": "/settings#email"}) }}""")
    assert_snapshot(rendered, "result_panel_error")
    assert "gth-result-panel" not in rendered and "badge" not in rendered
    assert "IMAP login failed" in rendered and "Email sync" in rendered
    assert 'href="/settings#email"' in rendered
    titled = _render(IMPORT + """{{ gth_result_panel("Results", error="Bad file",
        error_title="Couldn't import trades.csv") }}""")
    assert "Couldn&#39;t import trades.csv" in titled or "Couldn't import trades.csv" in titled


def test_live_region():
    rendered = _render("""{% from "result_panel.html" import gth_live_region %}
        {{ gth_live_region("import-result") }}""")
    assert rendered.strip() == '<div id="import-result" aria-live="polite"></div>'
