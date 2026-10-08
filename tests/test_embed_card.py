"""gth_embed_card: an iframe card driven by embed-card.js, and its placeholder."""

from test_macros_snapshot import _render, assert_snapshot

IMPORT = """{% from "embed_card.html" import gth_embed_card %}"""


def test_embed_card():
    rendered = _render(IMPORT + """{{ gth_embed_card(
        "https://grafana.lan/d-solo/abc?panelId=2", "Portfolio value", height=240, timeout=5) }}""")
    assert_snapshot(rendered, "embed_card")
    assert 'data-gth-embed-src="https://grafana.lan/d-solo/abc?panelId=2"' in rendered
    assert 'data-gth-embed-theme-param="theme"' in rendered
    assert 'data-gth-embed-timeout="5000"' in rendered
    assert 'style="height: 240px"' in rendered
    # The script's frame starts hidden with no src; <noscript> loads src as is.
    frame = '<iframe class="gth-embed-card-frame" title="Portfolio value"'
    assert frame + " hidden></iframe>" in rendered
    assert ("<noscript>" + frame + ' src="https://grafana.lan/d-solo/abc?panelId=2" '
            'loading="lazy"></iframe></noscript>') in rendered
    assert '<div class="gth-embed-card-error text-secondary" role="alert" hidden>' in rendered
    assert 'target="_blank" rel="noopener noreferrer"' in rendered


def test_embed_card_escapes_even_without_autoescape():
    rendered = _render(IMPORT + """{{ gth_embed_card(src, title) }}""",
                       src='/x?a=1&b="2"', title="<P&L>")
    assert 'data-gth-embed-src="/x?a=1&amp;b=&#34;2&#34;"' in rendered
    assert 'src="/x?a=1&amp;b=&#34;2&#34;"' in rendered
    assert '"2"' not in rendered and "<P&L>" not in rendered
    assert 'title="&lt;P&amp;L&gt;"' in rendered


def test_embed_card_without_theme_param():
    rendered = _render(IMPORT + """{{ gth_embed_card("/p", "Panel", theme_param=None,
        card_class="h-100", open_label="View") }}""")
    assert "data-gth-embed-theme-param" not in rendered
    assert 'class="card gth-embed-card h-100"' in rendered
    assert ">View <i class=" in rendered


def test_embed_card_placeholder_without_src():
    for src in ("none", '""'):
        rendered = _render(IMPORT + "{{ gth_embed_card(" + src + ", 'Dividends panel', "
                           "empty_message='Grafana isn\\'t set up yet.') }}")
        assert "<iframe" not in rendered and "data-gth-embed" not in rendered
        assert "Grafana isn&#39;t set up yet." in rendered
        assert "new tab" not in rendered
    empty = _render(IMPORT + "{{ gth_embed_card(none, 'Dividends panel') }}")
    assert_snapshot(empty, "embed_card_empty")
