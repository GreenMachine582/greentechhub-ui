from pathlib import Path

import html5lib
import pytest
from test_app_shell_renders import _context, _env

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
FRAGMENT_PARSER = html5lib.HTMLParser(strict=True)


@pytest.mark.parametrize(
    "snapshot_name",
    [
        "modal_bare",
        "modal_with_size_and_static_backdrop",
        "confirm_delete",
        "page_header_bare",
        "page_header_with_breadcrumbs",
        "page_header_with_action",
        "card",
        "stat_card",
        "stat_card_value_tone",
        "stat_card_with_icon",
        "navbar_with_icons",
        "theme_toggle",
        "navbar_with_theme_toggle",
        "table_with_rows",
        "table_empty",
        "empty_state",
        "empty_state_with_action",
        "pagination_with_next",
        "pagination_no_next",
        "form_no_error",
        "form_with_banner_error",
        "form_field_with_help",
        "form_field_with_errors",
        "form_field_affixes",
        "form_field_counter",
        "form_field_textarea",
        "toast_flashes_empty",
        "toast_flashes_with_items",
        "toast_flashes_rich",
        "alert",
        "back_to_top",
        "busy_button",
        "busy_button_submit",
        "combobox_empty",
        "combobox_with_value_and_errors",
        "combobox_options",
        "segmented",
        "segmented_with_help_and_errors",
        "select",
        "select_with_placeholder_and_errors",
        "select_hide_label",
        "select_id",
        "result_panel",
        "result_panel_error",
        "segmented_id",
        "switch_id",
        "form_field_id",
        "switch_with_off_value_and_errors",
        "settings_section_with_form",
        "settings_section_without_action",
        "setting_field_secret_unset",
        "setting_field_secret_set",
        "settings_section_with_secret",
        "table_load_more_with_next",
        "data_table_pages",
        "data_table_load_more",
        "data_table_infinite",
        "table_filter",
        "skeleton",
        "badges",
        "tabs",
        "chips",
        "switch",
        "multiselect",
        "multiselect_tags",
        "record_picker_empty",
        "record_picker_with_value_and_errors",
        "record_picker_row",
        "record_picker_modal_fixed",
        "record_picker_full_page",
        "record_pick_banner",
        "record_pick_button",
        "action_menu",
        "action_menu_no_label",
        "action_menu_inline_2",
        "action_menu_all_inline",
        "description_list",
        "description_list_pairs_two_columns",
        "progress",
        "progress_indeterminate",
        "progress_meter_bad",
        "progress_polling",
        "alert_banner",
        "alert_banner_bad_static",
        "sidebar",
        "navbar_sidebar_mode",
        "navbar_dropdown",
        "navbar_with_user_menu",
        "navbar_sidebar_mode_with_user_menu",
        "settings_section_template",
        "roles_section_template",
        "segmented_track",
        "command_palette",
        "tree_single",
        "tree_multi",
        "date_range",
        "date_range_with_values_and_errors",
        "date_range_presets_subset",
        "file_drop",
        "file_drop_accept_and_size",
        "file_drop_with_errors",
        "data_table_bulk",
        "data_table_view_options",
        "data_table_export",
        "data_table_row_actions",
    ],
)
def test_macro_output_is_well_formed(snapshot_name):
    html = (SNAPSHOT_DIR / f"{snapshot_name}.html").read_text(encoding="utf-8")
    FRAGMENT_PARSER.parseFragment(html)


def test_app_shell_is_well_formed_document():
    html = _env().get_template("app.html").render(**_context())
    html5lib.HTMLParser(strict=True).parse(html)


def test_app_shell_sidebar_layout_is_well_formed_document():
    html = _env().get_template("app.html").render(**_context(
        layout="sidebar", sidebar_js_url="/a/js/sidebar.js",
        nav_items=[{"label": "Data", "children": [{"label": "Tables", "url": "/t"}]}],
    ))
    html5lib.HTMLParser(strict=True).parse(html)
