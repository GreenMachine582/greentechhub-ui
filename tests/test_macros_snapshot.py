import os
from pathlib import Path

from greentechhub_core.types import FlashMessage
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


def test_page_header_bare():
    rendered = _render(
        """{% from "page_header.html" import gth_page_header %}
        {{ gth_page_header("Deals") }}"""
    )
    assert_snapshot(rendered, "page_header_bare")


def test_page_header_with_breadcrumbs():
    rendered = _render(
        """{% from "page_header.html" import gth_page_header %}
        {{ gth_page_header("Deal Breakdown", subtitle="Reviewing terms before you commit",
            breadcrumbs=[{"label": "Deals", "url": "/"}, {"label": "Deal Breakdown"}]) }}"""
    )
    assert_snapshot(rendered, "page_header_with_breadcrumbs")


def test_page_header_with_action():
    rendered = _render(
        """
        {% from "page_header.html" import gth_page_header %}
        {% call gth_page_header("Deals", breadcrumbs=[{"label": "Deals"}]) %}
        <button class="btn btn-sm btn-primary">New deal</button>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "page_header_with_action")


def test_modal_bare():
    rendered = _render(
        """
        {% from "modal.html" import gth_modal %}
        {% call gth_modal("demo-modal", title="Demo Modal") %}
        <p>Body content.</p>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "modal_bare")


def test_modal_with_size_and_static_backdrop():
    rendered = _render(
        """
        {% from "modal.html" import gth_modal %}
        {% call gth_modal("big-modal", title="Big Modal", size="lg", static_backdrop=True) %}
        <p>Body content.</p>
        {% endcall %}
        """
    )
    assert_snapshot(rendered, "modal_with_size_and_static_backdrop")


def test_confirm_delete():
    rendered = _render(
        """{% from "confirm_delete.html" import gth_confirm_delete %}
        {{ gth_confirm_delete("confirm-1", target_url="/items/1", item_label="Widget #1",
            hx_target="#list") }}"""
    )
    assert_snapshot(rendered, "confirm_delete")


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


def test_navbar_with_logo():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(nav_items, brand) }}""",
        nav_items=[{"label": "Deals", "url": "/"}],
        brand=brand_context(service_name="Playground", show_logo=True),
    )
    assert_snapshot(rendered, "navbar_with_logo")


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


def test_toast_flashes_with_flash_message_objects_matches_dict_rendering():
    """gth_toast_flashes uses f.kind/f.message (Jinja attribute lookup), so a
    real greentechhub_core.types.FlashMessage renders identically to the
    equivalent {message, kind} dict, with no conversion. Asserts against the
    *same* recorded snapshot as test_toast_flashes_with_items (not a new
    one) to prove that equivalence directly.
    """
    rendered = _render(
        """{% from "toast.html" import gth_toast_flashes %}
        {{ gth_toast_flashes(flashes) }}""",
        flashes=[
            FlashMessage(message="Saved successfully", kind="success"),
            FlashMessage(message="Heads up, something needs attention", kind="warning"),
        ],
    )
    assert_snapshot(rendered, "toast_flashes_with_items")


def test_busy_button():
    rendered = _render(
        """{% from "busy_button.html" import gth_busy_button %}
        {{ gth_busy_button("Sync ASX", "Syncing ASX…", {"hx-post": "/sync/ASX", "hx-swap": "none"},
            icon="arrow-repeat", start_toast="ASX sync started") }}"""
    )
    assert_snapshot(rendered, "busy_button")


def test_combobox_empty():
    rendered = _render(
        """{% from "combobox.html" import gth_combobox %}
        {{ gth_combobox("stock_id", "Stock", "/stocks/options") }}"""
    )
    assert_snapshot(rendered, "combobox_empty")


def test_combobox_with_value_and_errors():
    rendered = _render(
        """{% from "combobox.html" import gth_combobox %}
        {{ gth_combobox("stock_id", "Stock", "/stocks/options", value=7,
            value_label="BHP · ASX", errors=["Choose a stock."],
            help_text="Pick from the list.") }}"""
    )
    assert_snapshot(rendered, "combobox_with_value_and_errors")


def test_combobox_options():
    rendered = _render(
        """{% from "combobox.html" import gth_combobox_option, gth_combobox_empty %}
        {{ gth_combobox_option(7, "BHP · ASX") }}
        {% call gth_combobox_option(8, "CBA · ASX") %}<b>CBA</b> · ASX{% endcall %}
        {{ gth_combobox_empty("No matching stocks") }}"""
    )
    assert_snapshot(rendered, "combobox_options")


def test_segmented():
    rendered = _render(
        """{% from "segmented.html" import gth_segmented %}
        {{ gth_segmented("type", [
            {"value": "Buy", "label": "Buy", "style": "btn-outline-primary", "icon": "plus-circle"},
            {"value": "Sell", "label": "Sell", "style": "btn-outline-warning"},
        ], value="Sell", label="Type") }}"""
    )
    assert_snapshot(rendered, "segmented")


def test_segmented_defaults_to_first_option():
    rendered = _render(
        """{% from "segmented.html" import gth_segmented %}
        {{ gth_segmented("size", [{"value": "s", "label": "S"}, {"value": "m", "label": "M"}]) }}"""
    )
    radios = [line for line in rendered.split("<input")[1:]]
    assert len(radios) == 2
    assert 'value="s"' in radios[0] and " checked" in radios[0]
    assert " checked" not in radios[1]


def test_table_load_more_with_next():
    rendered = _render(
        """{% from "table.html" import gth_table, gth_table_load_more %}
        {% call gth_table(headers=["Name"], tbody_id="rows") %}
        <tr><td>Row 1</td></tr>
        {{ gth_table_load_more("/rows?page=2&size=50", total=120) }}
        {% endcall %}"""
    )
    assert_snapshot(rendered, "table_load_more_with_next")


def test_table_load_more_no_next_renders_nothing():
    rendered = _render(
        """{% from "table.html" import gth_table_load_more %}
        {{ gth_table_load_more(None) }}"""
    )
    assert rendered.strip() == ""


def test_busy_button_escapes_attrs_without_autoescape():
    rendered = _render(
        """{% from "busy_button.html" import gth_busy_button %}
        {{ gth_busy_button("Go", "Going", {"hx-get": "/rows?a=1&b=\\"2\\""},
            start_toast="Tom & Jerry") }}"""
    )
    assert 'hx-get="/rows?a=1&amp;b=&#34;2&#34;"' in rendered
    assert 'data-gth-start-toast="Tom &amp; Jerry"' in rendered


def test_segmented_respects_falsy_value():
    rendered = _render(
        """{% from "segmented.html" import gth_segmented %}
        {{ gth_segmented("n", [{"value": 1, "label": "One"}, {"value": 0, "label": "Zero"}],
            value=0) }}"""
    )
    radios = rendered.split("<input")[1:]
    assert " checked" not in radios[0]
    assert 'value="0"' in radios[1] and " checked" in radios[1]


def test_combobox_option_has_no_value_derived_id():
    rendered = _render(
        """{% from "combobox.html" import gth_combobox_option %}
        {{ gth_combobox_option("a b", "A B") }}"""
    )
    assert " id=" not in rendered


def test_navbar_pinned_dark():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(nav_items, brand, navbar_theme="dark") }}""",
        nav_items=[{"label": "Deals", "url": "/"}],
        brand=brand_context(service_name="Playground"),
    )
    assert_snapshot(rendered, "navbar_pinned_dark")


def test_navbar_single_logo_without_logo_light_url():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}{{ gth_navbar([], brand) }}""",
        brand={"name": "GTH", "logo_url": "/l.png", "service_name": None},
    )
    assert rendered.count("<img") == 1
    assert "gth-logo-on-" not in rendered


_DATA_TABLE = """{% from "table.html" import gth_data_table %}
{% call(r) gth_data_table(state, [{"label": "Name", "sort_key": "name"}, "Qty"], rows) %}
<tr><td>{{ r.name }}</td><td>{{ r.qty }}</td></tr>
{% endcall %}"""
_ROWS = [{"name": "Bolt", "qty": 3}, {"name": "Nut", "qty": 9}]


def _table_state(query=None, **kwargs):
    from greentechhub_ui import TableState

    kwargs.setdefault("sortable", ("name",))
    state = TableState.from_query(query or {}, id="parts", base_url="/parts", page_size=2, **kwargs)
    return state.with_result(total=kwargs.pop("total", 9))


def test_data_table_pages():
    state = _table_state({"page": "3", "sort": "name", "dir": "desc", "q": "b&c"},
                         mode="pages", page_sizes=(2, 10), push_url=True)
    assert_snapshot(_render(_DATA_TABLE, state=state, rows=_ROWS), "data_table_pages")


def test_data_table_load_more():
    state = _table_state(mode="load_more")
    assert_snapshot(_render(_DATA_TABLE, state=state, rows=_ROWS), "data_table_load_more")


def test_data_table_infinite_in_scroll_box():
    state = _table_state(mode="infinite", max_height="20rem")
    assert_snapshot(_render(_DATA_TABLE, state=state, rows=_ROWS), "data_table_infinite")


def test_data_table_rows_only_append():
    state = _table_state({"page": "2", "partial": "rows"}, mode="infinite")
    rendered = _render(_DATA_TABLE, state=state, rows=_ROWS)
    assert 'id="parts"' not in rendered and "<thead>" not in rendered
    assert rendered.count("<tr") == 3  # two rows + the next trailing row
    assert 'hx-get="/parts?page=3&amp;partial=rows"' in rendered


def test_data_table_none_mode_has_no_navigation():
    state = _table_state(mode="none")
    rendered = _render(_DATA_TABLE, state=state, rows=_ROWS)
    assert "gth-table-load-more" not in rendered and "pagination" not in rendered


def test_data_table_empty():
    state = _table_state(mode="pages", total=0)
    rendered = _render(_DATA_TABLE, state=state, rows=[])
    assert "gth-empty-state" in rendered and "pagination" not in rendered


def test_table_filter():
    rendered = _render(
        """{% from "table.html" import gth_table_filter %}
        {% call gth_table_filter(state) %}<select name="category"></select>{% endcall %}""",
        state=_table_state({"q": 'a"b', "page": "2"}, mode="pages",
                           filter_params=("q", "category")),
    )
    assert_snapshot(rendered, "table_filter")


def test_skeleton():
    rendered = _render(
        """{% from "skeleton.html" import gth_skeleton, gth_skeleton_rows %}
        {{ gth_skeleton(2) }}<table><tbody>{{ gth_skeleton_rows(2, colspan=3) }}</tbody></table>"""
    )
    assert_snapshot(rendered, "skeleton")
