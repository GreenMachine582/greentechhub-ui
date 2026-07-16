import os
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

import greentechhub_ui
from greentechhub_ui.theme import brand_context

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _env() -> Environment:
    return Environment(
        loader=ChoiceLoader(
            [
                FileSystemLoader(greentechhub_ui.templates_path),
                FileSystemLoader(greentechhub_ui.components_path),
            ]
        )
    )


def _render(source: str, **context) -> str:
    return _env().from_string(source).render(**context)


def assert_snapshot(rendered: str, name: str):
    path = SNAPSHOT_DIR / f"{name}.html"
    if os.environ.get("GTH_UPDATE_SNAPSHOTS"):
        path.write_text(rendered, encoding="utf-8")
        return
    expected = path.read_text(encoding="utf-8")
    assert rendered == expected, (
        f"{name} snapshot mismatch — run with GTH_UPDATE_SNAPSHOTS=1 to update"
    )


def test_card():
    rendered = _render(
        """
        {% from "card.html" import gth_card %}
        {% call gth_card(title="Deal breakdown", footer="Updated 2h ago") %}
        <p>Score: 87</p>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "card")


def test_stat_card():
    rendered = _render(
        """{% from "stat_card.html" import gth_stat_card %}
        {{ gth_stat_card("30-day avg", "$12.34", delta="-1.20", delta_tone="good") }}"""
    )
    assert_snapshot(rendered, "stat_card")


def test_stat_card_with_value_tone_and_safe_html():
    rendered = _render(
        """{% from "stat_card.html" import gth_stat_card %}
        {{ gth_stat_card("All-time", "$8.99",
            delta='low / <span class="text-danger">$15.00</span> high',
            delta_tone="neutral", value_tone="good") }}"""
    )
    assert_snapshot(rendered, "stat_card_value_tone")


def test_stat_card_with_icon():
    rendered = _render(
        """{% from "stat_card.html" import gth_stat_card %}
        {{ gth_stat_card("Current", "$45.00", icon="cart") }}"""
    )
    assert_snapshot(rendered, "stat_card_with_icon")


def test_navbar_with_icons():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(nav_items, brand) }}""",
        nav_items=[
            {"label": "Deals", "url": "/", "icon": "cart"},
            {"label": "Watchlist", "url": "/watchlist", "icon": "star"},
        ],
        brand=brand_context(service_name="Playground"),
    )
    assert_snapshot(rendered, "navbar_with_icons")


def test_theme_toggle():
    rendered = _render(
        """{% from "theme_toggle.html" import gth_theme_toggle %}
        {{ gth_theme_toggle() }}"""
    )
    assert_snapshot(rendered, "theme_toggle")


def test_navbar_with_theme_toggle():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(nav_items, brand, show_theme_toggle=True) }}""",
        nav_items=[{"label": "Deals", "url": "/"}],
        brand=brand_context(service_name="Playground"),
    )
    assert_snapshot(rendered, "navbar_with_theme_toggle")


def test_table_with_rows():
    rendered = _render(
        """
        {% from "table.html" import gth_table, gth_table_body %}
        {% call gth_table(headers=["Score", "Product"], tbody_id="deals-tbody") %}
        {% call(deal) gth_table_body(rows=deals,
            empty_message="No deals match your filters.", colspan=2) %}
        <tr><td>{{ deal.score }}</td><td>{{ deal.name }}</td></tr>
        {% endcall %}
        {% endcall %}
        """,
        deals=[{"score": 87, "name": "Some Whisky 700mL"}, {"score": 72, "name": "Some Rum 700mL"}],
    )
    assert_snapshot(rendered, "table_with_rows")


def test_table_empty():
    rendered = _render(
        """
        {% from "table.html" import gth_table, gth_table_body %}
        {% call gth_table(headers=["Score", "Product"], tbody_id="deals-tbody") %}
        {% call(deal) gth_table_body(rows=deals,
            empty_message="No deals match your filters.", colspan=2) %}
        <tr><td>{{ deal.score }}</td><td>{{ deal.name }}</td></tr>
        {% endcall %}
        {% endcall %}
        """,
        deals=[],
    )
    assert_snapshot(rendered, "table_empty")


def test_empty_state():
    rendered = _render(
        """{% from "empty_state.html" import gth_empty_state %}
        {{ gth_empty_state("No scrape runs recorded yet.") }}"""
    )
    assert_snapshot(rendered, "empty_state")


def test_empty_state_with_action():
    rendered = _render(
        """
        {% from "empty_state.html" import gth_empty_state %}
        {% call gth_empty_state(message="No deals above score 65 right now.") %}
        <button class="btn btn-sm btn-outline-secondary">Scrape now</button>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "empty_state_with_action")


def test_pagination_with_next():
    rendered = _render(
        """{% from "pagination.html" import gth_pagination %}
        {{ gth_pagination(next_url="/watchlist/list?offset=20") }}"""
    )
    assert_snapshot(rendered, "pagination_with_next")


def test_pagination_no_next():
    rendered = _render(
        """{% from "pagination.html" import gth_pagination %}
        {{ gth_pagination(next_url=None) }}"""
    )
    assert_snapshot(rendered, "pagination_no_next")


def test_form_no_error():
    rendered = _render(
        """
        {% from "form.html" import gth_form, gth_form_field %}
        {% call gth_form(action="/criteria") %}
        {{ gth_form_field("min_deal_score", "Min deal score (0-100)", value=65.0, type="number") }}
        <button type="submit" class="btn btn-primary">Save</button>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "form_no_error")


def test_form_with_banner_error():
    rendered = _render(
        """
        {% from "form.html" import gth_form, gth_form_field %}
        {% call gth_form(action="/criteria", error="Some values couldn't be saved.",
            error_heading="Invalid values") %}
        {{ gth_form_field("min_deal_score", "Min deal score (0-100)", value=65.0, type="number") }}
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "form_with_banner_error")


def test_form_field_with_help():
    rendered = _render(
        """{% from "form.html" import gth_form_field %}
        {{ gth_form_field("min_saving_aud", "Min saving (AUD)", value=2.0, type="number",
            help_text="Absolute dollar saving per unit.") }}"""
    )
    assert_snapshot(rendered, "form_field_with_help")


def test_form_field_with_errors():
    rendered = _render(
        """{% from "form.html" import gth_form_field %}
        {{ gth_form_field("min_saving_aud", "Min saving (AUD)", value=-2.0, type="number",
            errors=["Input should be greater than or equal to 0"]) }}"""
    )
    assert_snapshot(rendered, "form_field_with_errors")


def test_toast_flashes_empty():
    rendered = _render(
        """{% from "toast.html" import gth_toast_flashes %}
        {{ gth_toast_flashes([]) }}"""
    )
    assert_snapshot(rendered, "toast_flashes_empty")


def test_toast_flashes_with_items():
    rendered = _render(
        """{% from "toast.html" import gth_toast_flashes %}
        {{ gth_toast_flashes(flashes) }}""",
        flashes=[
            {"message": "Saved successfully", "kind": "success"},
            {"message": "Heads up, something needs attention", "kind": "warning"},
        ],
    )
    assert_snapshot(rendered, "toast_flashes_with_items")
