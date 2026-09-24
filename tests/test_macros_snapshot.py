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


def test_badges():
    rendered = _render(
        """{% from "badge.html" import gth_badge %}
        {{ gth_badge("OK", "good", icon="check-circle") }}{{ gth_badge("Brand", "brand") }}
        {{ gth_badge("Sq", "unknown-tone", pill=False) }}"""
    )
    assert_snapshot(rendered, "badges")


def test_tabs_static_and_lazy():
    rendered = _render(
        """{% from "tabs.html" import gth_tabs %}
        {% call(key) gth_tabs("t", [{"key": "a", "label": "A", "icon": "info-circle"},
            {"key": "b", "label": "B", "url": "/tab/b?x=1&y=2"}]) %}Pane {{ key }}{% endcall %}"""
    )
    assert_snapshot(rendered, "tabs")


def test_tabs_active_lazy_tab_loads_on_page_load():
    rendered = _render(
        """{% from "tabs.html" import gth_tabs %}
        {{ gth_tabs("t", [{"key": "a", "label": "A"}, {"key": "b", "label": "B", "url": "/b"}],
            active="b") }}"""
    )
    assert 'hx-trigger="load"' in rendered
    assert 'aria-selected="true"' in rendered.split('id="t-tab-b"')[1].split(">")[0]


def test_chips():
    rendered = _render(
        """{% from "chips.html" import gth_chips %}
        {{ gth_chips("tags", [{"value": 1, "label": "One"},
                              {"value": 2, "label": "Two", "icon": "x"}],
            values=["2"], label="Tags") }}"""
    )
    assert_snapshot(rendered, "chips")
    inputs = rendered.split("<input")[1:]
    assert " checked" not in inputs[0] and " checked" in inputs[1]


def test_switch():
    rendered = _render(
        """{% from "chips.html" import gth_switch %}
        {{ gth_switch("alerts", "Alerts", checked=True, help_text="Emails.",
            input_attrs={"hx-post": "/prefs?a=1&b=2"}) }}"""
    )
    assert_snapshot(rendered, "switch")


def test_multiselect_with_values_and_errors():
    rendered = _render(
        """{% from "multiselect.html" import gth_multiselect %}
        {{ gth_multiselect("stocks", "Stocks", url="/stocks/options?x=1&y=2",
            values=[{"value": 7, "label": "BHP"}, {"value": "a&b", "label": "<A&B>"}],
            max_items=3, errors=["Pick one."], help_text="Up to 3.") }}"""
    )
    assert_snapshot(rendered, "multiselect")
    assert rendered.count('type="hidden" name="stocks"') == 2
    assert "<span>&lt;A&amp;B&gt;</span>" in rendered  # escaped even with autoescape off
    assert 'value="a&amp;b"' in rendered


def test_multiselect_without_url_is_a_tags_input():
    rendered = _render(
        """{% from "multiselect.html" import gth_multiselect %}
        {{ gth_multiselect("tags", "Tags") }}"""
    )
    assert_snapshot(rendered, "multiselect_tags")
    assert "data-gth-combobox-create" in rendered
    assert "data-gth-combobox-url" not in rendered and 'role="combobox"' not in rendered


def test_form_attrs_and_input_attrs_are_escaped_without_autoescape():
    rendered = _render(
        """{% from "form.html" import gth_form, gth_form_field %}
        {% call gth_form("/x", form_attrs={"hx-post": "/x?a=1&b=2"}) %}
        {{ gth_form_field("n", "N", input_attrs={"data-x": 'say "hi"'}) }}
        {% endcall %}"""
    )
    assert 'hx-post="/x?a=1&amp;b=2"' in rendered
    assert 'data-x="say &#34;hi&#34;"' in rendered


def test_record_picker_empty():
    rendered = _render(
        """{% from "record_picker.html" import gth_record_picker %}
        {{ gth_record_picker("part", "Part", "/parts/picker?x=1&y=2") }}"""
    )
    assert_snapshot(rendered, "record_picker_empty")


def test_record_picker_with_value_and_errors():
    rendered = _render(
        """{% from "record_picker.html" import gth_record_picker %}
        {{ gth_record_picker("part", "Part", "/parts/picker", value=17, value_label="Kilo <17>",
            errors=["Pick a part."], help_text="Search 120 parts.", panel_width="50rem") }}"""
    )
    assert_snapshot(rendered, "record_picker_with_value_and_errors")
    assert "Kilo &lt;17&gt;" in rendered


def test_record_picker_row():
    rendered = _render(
        """{% from "record_picker.html" import gth_record_picker_row %}
        <table><tbody>{% call gth_record_picker_row(17, "Kilo & co") %}<td>Kilo</td>{% endcall %}
        </tbody></table>"""
    )
    assert_snapshot(rendered, "record_picker_row")


def test_multiselect_custom_max_message():
    rendered = _render(
        """{% from "multiselect.html" import gth_multiselect %}
        {{ gth_multiselect("w", "W", url="/w", max_items=2, max_message="Two & no more.") }}"""
    )
    assert 'data-gth-combobox-max-message="Two &amp; no more."' in rendered


def test_record_picker_opens_at_modal_size_without_toggle():
    rendered = _render(
        """{% from "record_picker.html" import gth_record_picker %}
        {{ gth_record_picker("part", "Part", "/p", size="modal", expandable=False) }}"""
    )
    assert_snapshot(rendered, "record_picker_modal_fixed")
    assert 'data-gth-record-picker-size="modal"' in rendered
    assert "data-gth-record-picker-size aria" not in rendered  # no toggle button
    assert "data-gth-record-picker-close" in rendered


_SIDEBAR_NAV = [
    {"label": "Home", "url": "/", "icon": "house"},
    {"label": "Data", "icon": "database", "children": [
        {"label": "Tables", "url": "/tables", "badge": {"label": "3", "tone": "warn"}},
        {"label": "Archive", "children": [{"label": "2024", "url": "/archive/2024"}]},
    ]},
    {"label": "Reports", "url": "/reports",
     "children": [{"label": "Monthly", "url": "/reports/m"}]},
]


def test_sidebar_marks_active_trail():
    from greentechhub_ui.navigation import mark_active

    rendered = _render(
        """{% from "sidebar.html" import gth_sidebar, gth_sidebar_rail_toggle %}
        {{ gth_sidebar(items) }}{{ gth_sidebar_rail_toggle() }}""",
        items=mark_active(_SIDEBAR_NAV, "/archive/2024"),
    )
    assert_snapshot(rendered, "sidebar")
    assert rendered.count('aria-current="page"') == 1
    data_toggle = rendered.split('data-gth-sidebar-group="Data"')[0].rsplit("<button", 1)[1]
    assert 'aria-expanded="true"' in data_toggle
    # Reports isn't on the trail, so its list starts hidden, and its own url
    # becomes an "Overview" first child.
    assert 'hidden data-gth-sidebar-children\n        aria-label="Reports"' in rendered
    assert "Overview" in rendered


def test_sidebar_without_mark_active_renders_plain():
    rendered = _render(
        """{% from "sidebar.html" import gth_sidebar %}
        {{ gth_sidebar(items, show_filter=False) }}""",
        items=_SIDEBAR_NAV,
    )
    assert "aria-current" not in rendered and "data-gth-sidebar-filter" not in rendered


def test_navbar_sidebar_mode():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(items, brand, sidebar=True, show_search=True, show_theme_toggle=True) }}""",
        items=_SIDEBAR_NAV, brand=brand_context(service_name="Playground"),
    )
    assert_snapshot(rendered, "navbar_sidebar_mode")
    assert "Tables" not in rendered  # the items live in the sidebar
    assert 'data-bs-target="#gth-sidebar"' in rendered and "data-gth-command-open" in rendered


def test_navbar_dropdown_for_nested_items():
    rendered = _render(
        """{% from "navbar.html" import gth_navbar %}
        {{ gth_navbar(items, brand, "/archive/2024") }}""",
        items=_SIDEBAR_NAV, brand=brand_context(service_name="Playground"),
    )
    assert_snapshot(rendered, "navbar_dropdown")
    assert rendered.count('class="nav-item dropdown"') == 2
    assert 'class="dropdown-item active" href="/archive/2024"' in rendered


def test_nav_badge_static_live_and_none():
    rendered = _render(
        """{% from "badge.html" import gth_nav_badge %}
        [{{ gth_nav_badge({"label": "x"}) }}]
        {{ gth_nav_badge({"badge": {"label": "3", "tone": "warn"}}) }}
        {{ gth_nav_badge({"badge_url": "/b?a=1&c=2", "badge_event": "healthChanged"}) }}"""
    )
    assert "[]" in rendered
    assert "text-warning-emphasis" in rendered and ">3</span>" in rendered
    assert 'hx-get="/b?a=1&amp;c=2"' in rendered
    assert 'hx-trigger="load, healthChanged from:body"' in rendered


def test_command_palette_markup():
    from greentechhub_ui.navigation import flatten

    env = _env()
    env.globals["nav_flatten"] = flatten  # an env global, as shell_globals installs it
    rendered = env.from_string(
        """{% from "command_palette.html" import gth_command_palette, gth_command_item %}
        {{ gth_command_palette(items, search_url="/search?x=1") }}
        {{ gth_command_item("Bolt <M6>", "/p?id=1&x=2", "cpu", "Sensor") }}"""
    ).render(items=_SIDEBAR_NAV)
    assert_snapshot(rendered, "command_palette")
    # Embedded JSON is script-safe, and entries carry their group path.
    assert r"Data \u203a Tables" in rendered  # tojson escapes non-ASCII
    assert "Bolt &lt;M6&gt;" in rendered and 'href="/p?id=1&amp;x=2"' in rendered


def test_command_palette_without_nav_flatten_is_empty_list():
    rendered = _render(
        """{% from "command_palette.html" import gth_command_palette %}
        {{ gth_command_palette(items) }}""",
        items=_SIDEBAR_NAV,
    )
    assert "data-gth-command-data>[]</script>" in rendered
    assert "data-gth-command-remote" not in rendered


_TREE = [
    {"id": "c:1", "label": "Sensors", "icon": "collection", "badge": {"label": "2"},
     "expanded": True,
     "children": [
         {"id": "p:1", "label": "Probe <A>", "url": "/d?id=p:1&x=1", "selected": True},
         {"id": "a:1", "label": "Assembly", "has_children": True},
     ]},
    {"id": "c:2", "label": "Motors", "children": [{"id": "p:2", "label": "Stepper"}]},
]


def test_tree_single_with_lazy_and_detail():
    rendered = _render(
        """{% from "tree.html" import gth_tree %}
        {{ gth_tree("t", nodes, "Catalogue", select="single", name="node",
            lazy_url="/nodes?tree=t", detail_target="#detail") }}""",
        nodes=_TREE,
    )
    assert_snapshot(rendered, "tree_single")
    # a:1 is at level 2, so its lazy children are level 3.
    assert 'hx-get="/nodes?tree=t&amp;parent=a%3A1&amp;level=3"' in rendered
    assert 'hx-target="this"' in rendered
    assert "Probe &lt;A&gt;" in rendered
    assert rendered.count('tabindex="0"') == 1


def test_tree_multi_marks_checked_and_multiselectable():
    nodes = [{**_TREE[1], "checked": True, "children": [{"id": "p:2", "label": "Stepper",
                                                          "checked": True}]}]
    rendered = _render(
        """{% from "tree.html" import gth_tree %}
        {{ gth_tree("m", nodes, "Pick", select="multi", name="nodes") }}""",
        nodes=nodes,
    )
    assert_snapshot(rendered, "tree_multi")
    assert 'aria-multiselectable="true"' in rendered
    assert rendered.count('aria-checked="true"') == 2
    assert "aria-selected" not in rendered


def test_tree_nodes_partial_levels():
    rendered = _render(
        """{% from "tree.html" import gth_tree_nodes %}
        <ul role="group">{{ gth_tree_nodes(nodes, 3, "t", "multi") }}</ul>""",
        nodes=[{"id": "p:9", "label": "Leaf"}, {"id": "p:10", "label": "Leaf 2"}],
    )
    assert rendered.count('aria-level="3"') == 2
    assert 'aria-setsize="2" aria-posinset="2"' in rendered
    assert 'tabindex="0"' not in rendered  # only the tree's first top-level node


def test_self_loading_elements_pin_their_own_hx_target():
    """htmx inherits hx-target: inside e.g. a gth_form with hx-target="this",
    an element that loads itself must say where its response goes, or it
    lands in the form (found with gth_tree's lazy groups)."""
    rendered = _render(
        """{% from "badge.html" import gth_nav_badge %}
        {% from "table.html" import gth_table_load_more %}
        {% from "tabs.html" import gth_tabs %}
        {% from "tree.html" import gth_tree %}
        {{ gth_nav_badge({"badge_url": "/b"}) }}
        <table><tbody>{{ gth_table_load_more("/rows?page=2", infinite=True) }}</tbody></table>
        {{ gth_tabs("t", [{"key": "a", "label": "A", "url": "/a"},
                          {"key": "b", "label": "B", "url": "/b"}]) }}
        {{ gth_tree("tr", [{"id": 1, "label": "x", "has_children": True}], "T", lazy_url="/n") }}"""
    )
    import re as _re

    for tag in _re.findall(r"<[a-z]+[^>]*\bhx-get=[^>]*>", rendered):
        if "gth-pagination-more" in tag:  # its button already targets "closest tr"
            continue
        assert 'hx-target="' in tag, tag
