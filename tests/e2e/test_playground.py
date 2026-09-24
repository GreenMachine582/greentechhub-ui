"""Playwright smoke tests against the real /playground app (docs/testing.md).

Skips cleanly (not fails) if playwright isn't installed — see conftest.py's
`pytest.importorskip`.
"""

import re
from urllib.parse import urlparse

from playwright.sync_api import expect

# Every playground page (the category pages the sidebar links to, plus the
# data-table / tree / standalone sidebar demos).
PAGES = ["/", "/layout", "/data", "/forms", "/feedback", "/overlays", "/navigation",
         "/extensibility", "/tables", "/tree", "/layouts/sidebar"]

# Dynamically-triggered toasts land in #gth-toast-container. The static
# gth_toast_flashes demo section on the page also renders `.toast.show`
# elements (unconditionally, inline) — this selector must not match those.
DYNAMIC_TOAST = "#gth-toast-container .toast.show"


def test_dark_mode_toggle_persists(page, playground_url):
    page.goto(playground_url)
    html = page.locator("html")
    assert html.get_attribute("data-bs-theme") == "dark"

    page.click(".gth-theme-toggle")
    assert html.get_attribute("data-bs-theme") == "light"

    page.reload()
    assert html.get_attribute("data-bs-theme") == "light"


def test_form_validation_and_success_toast(page, playground_url):
    page.goto(f"{playground_url}/forms")

    page.fill("#gth-field-budget", "-5")
    page.click("#form-demo-container button[type=submit]")
    page.wait_for_selector("#gth-field-budget.is-invalid")
    assert "greater than or equal to 0" in page.inner_text("#form-demo-container")

    page.fill("#gth-field-budget", "250")
    page.click("#form-demo-container button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved budget")


def test_standalone_toast_trigger(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    page.click("text=Trigger a toast")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Demo toast triggered")


def test_table_filter_and_keyboard_focus(page, playground_url):
    page.goto(f"{playground_url}/data")
    assert "Design onboarding flow" in page.inner_text("#tasks-tbody")

    page.locator("#task-q-input").focus()
    page.keyboard.type("CI")

    tbody = page.locator("#tasks-tbody")
    expect(tbody).not_to_contain_text("Design onboarding flow")
    expect(tbody).to_contain_text("Fix flaky CI job")


def test_extra_css_and_js_and_head_slots_actually_work(page, playground_url):
    page.goto(f"{playground_url}/extensibility")

    # extra_css: a real applied stylesheet, not just markup presence — checks
    # the browser's computed style, proving the data: URI stylesheet loaded.
    css_demo = page.locator(".gth-extra-css-demo")
    assert css_demo.evaluate("el => getComputedStyle(el).color") == "rgb(255, 105, 180)"

    # extra_js: proves the injected script actually executed, not just that
    # a <script> tag with the right src is present in the markup.
    expect(page.locator("#gth-extra-js-demo")).to_have_text("extra_js worked!")

    # extra_head: a real DOM node, not just a text search on page source.
    assert page.locator('meta[name="gth-extra-head-demo"]').get_attribute("content") == "works"


def test_modal_traps_focus_and_escape_returns_it_to_trigger(page, playground_url):
    page.goto(f"{playground_url}/overlays")
    trigger = page.get_by_role("button", name="Open modal", exact=True)
    trigger.click()

    modal = page.locator("#demo-modal")
    expect(modal).to_be_visible()
    # Bootstrap's own Modal JS focuses the modal container itself on show —
    # the focus trap and aria-modal/aria-hidden toggling come from that same
    # native JS, not any gth-* code (see components/modal.html).
    expect(modal).to_be_focused()

    page.keyboard.press("Tab")
    expect(modal.locator(".btn-close")).to_be_focused()

    page.keyboard.press("Escape")
    expect(modal).to_be_hidden()
    expect(trigger).to_be_focused()


def test_confirm_delete_removes_watchlist_item(page, playground_url):
    page.goto(f"{playground_url}/overlays")
    watchlist = page.locator("#watchlist-demo-list")
    expect(watchlist).to_contain_text("Widget A")

    watchlist.get_by_role("button", name="Remove").first.click()
    confirm_modal = page.locator(".gth-modal.show")
    expect(confirm_modal).to_contain_text("Delete Widget A?")

    confirm_modal.get_by_role("button", name="Delete").click()
    expect(watchlist).not_to_contain_text("Widget A")


def test_page_makes_no_off_origin_requests(page, playground_url):
    """The concrete test that keeps app.html local-first: Bootstrap/HTMX/icons
    are vendored and served from the playground's own origin (see
    static/VENDORED.md), so a real page load should never reach a public CDN.
    """
    origin = urlparse(playground_url).netloc
    off_origin_urls = []

    def _record_off_origin(request):
        netloc = urlparse(request.url).netloc
        if netloc and netloc != origin:
            off_origin_urls.append(request.url)

    page.on("request", _record_off_origin)
    for path in PAGES:
        page.goto(f"{playground_url}{path}")
        page.wait_for_load_state("networkidle")

    assert off_origin_urls == []


# ── v0.7: modal host, combobox, segmented, busy button, table load-more ────

MODAL = "#gth-modal-host .modal.show"
COMBO_INPUT = "#gth-field-widget-search"
COMBO_VALUE = "#gth-modal-host input[name=widget]"
COMBO_RESULTS = "#gth-field-widget-results"


def _open_v07_modal(page, playground_url):
    page.goto(f"{playground_url}/overlays")
    page.click("text=Open server-rendered modal")
    expect(page.locator(MODAL)).to_be_visible()


def test_combobox_search_clear_restores_full_list(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click(COMBO_INPUT)
    expect(page.locator(COMBO_RESULTS)).to_be_visible()
    expect(page.locator(f"{COMBO_RESULTS} [data-value]")).to_have_count(10)

    page.fill(COMBO_INPUT, "#16")
    expect(page.locator(f"{COMBO_RESULTS} [data-value]")).to_have_count(1)
    page.click(f"{COMBO_RESULTS} [data-value]")
    expect(page.locator(COMBO_RESULTS)).to_be_hidden()
    assert page.input_value(COMBO_INPUT) == "Widget #16"
    assert page.input_value(COMBO_VALUE) == "16"

    # The reported bug: clearing the search must bring the whole list back
    # and drop the stale pick.
    page.fill(COMBO_INPUT, "")
    expect(page.locator(f"{COMBO_RESULTS} [data-value]")).to_have_count(10)
    assert page.input_value(COMBO_VALUE) == ""


def test_combobox_keyboard_pick_does_not_submit_and_esc_keeps_modal(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click(COMBO_INPUT)
    expect(page.locator(COMBO_RESULTS)).to_be_visible()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(page.locator(COMBO_RESULTS)).to_be_hidden()
    assert page.input_value(COMBO_INPUT) == "Widget #2"
    expect(page.locator(MODAL)).to_be_visible()  # Enter picked, didn't submit

    page.fill(COMBO_INPUT, "Wid")
    expect(page.locator(COMBO_RESULTS)).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator(COMBO_RESULTS)).to_be_hidden()
    expect(page.locator(MODAL)).to_be_visible()  # Esc closed the panel, not the modal


def test_modal_form_422_then_success_closes_modal(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.fill(COMBO_INPUT, "Wid")  # typed, never picked
    expect(page.locator(COMBO_RESULTS)).to_be_visible()
    page.keyboard.press("Escape")  # the open panel overlays the fields below it
    page.click("#gth-modal-host label:has-text('Large')")
    page.click("#gth-modal-host button[type=submit]")
    expect(page.locator("#gth-modal-host")).to_contain_text("Pick a widget from the list.")
    assert page.input_value(COMBO_INPUT) == "Wid"
    expect(page.locator("#gth-modal-host input[name=size][value=L]")).to_be_checked()

    page.click(COMBO_INPUT)
    page.click(f"{COMBO_RESULTS} [data-value='3']")
    page.click("#gth-modal-host button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved Widget #3 (L)")
    expect(page.locator(MODAL)).to_have_count(0)


def test_busy_button_shows_busy_state_then_resets(page, playground_url):
    page.goto(f"{playground_url}/forms")
    button = page.locator(".gth-busy-button")
    button.click()
    expect(page.locator(DYNAMIC_TOAST).first).to_contain_text("Slow job started")
    expect(button).to_be_disabled()
    expect(button.locator(".gth-busy-button-busy")).to_be_visible()
    expect(button.locator(".gth-busy-button-idle")).to_be_hidden()

    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Slow job finished", timeout=10000)
    # The reported bug: the busy label must not stick once the request ends.
    expect(button).to_be_enabled()
    expect(button.locator(".gth-busy-button-idle")).to_be_visible()
    expect(button.locator(".gth-busy-button-busy")).to_be_hidden()


def test_table_load_more_appends_rows_until_exhausted(page, playground_url):
    page.goto(f"{playground_url}/data")
    rows = page.locator("#widgets-tbody tr:not(.gth-table-load-more)")
    expect(rows).to_have_count(5)
    for expected in (10, 15, 16):
        page.click("#widgets-tbody .gth-table-load-more button")
        expect(rows).to_have_count(expected)
    expect(page.locator("#widgets-tbody .gth-table-load-more")).to_have_count(0)


def test_modal_host_reopen_does_not_leak_backdrops(page, playground_url):
    page.goto(f"{playground_url}/overlays")
    for _ in range(2):
        page.click("text=Open server-rendered modal")
        expect(page.locator(MODAL)).to_be_visible()
        page.click("#gth-modal-host button[data-bs-dismiss=modal] >> nth=0")
        expect(page.locator("#gth-modal-host .modal")).to_have_count(0)
    expect(page.locator(".modal-backdrop")).to_have_count(0)
    assert "modal-open" not in (page.locator("body").get_attribute("class") or "")

    # Swapping a modal in over an open one tears the old one down.
    page.click("text=Open server-rendered modal")
    expect(page.locator(MODAL)).to_be_visible()
    page.evaluate("htmx.ajax('GET', '/v07-demo/modal', {target: '#gth-modal-host'})")
    expect(page.locator("#gth-modal-host .modal")).to_have_count(1)
    expect(page.locator(MODAL)).to_be_visible()
    expect(page.locator(".modal-backdrop")).to_have_count(1)


def test_combobox_options_get_panel_scoped_ids(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click(COMBO_INPUT)
    first = page.locator(f"{COMBO_RESULTS} [data-value]").first
    expect(first).to_have_id("gth-field-widget-results-opt-0")
    page.keyboard.press("ArrowDown")
    active = page.get_attribute(COMBO_INPUT, "aria-activedescendant")
    assert active == "gth-field-widget-results-opt-1"


def test_navbar_follows_color_mode(page, playground_url):
    page.goto(playground_url)
    nav = page.locator("nav.gth-navbar")

    def bg():
        return nav.evaluate("el => getComputedStyle(el).backgroundColor")

    dark_bg = bg()
    expect(page.locator(".gth-logo-on-dark")).to_be_visible()
    expect(page.locator(".gth-logo-on-light")).to_be_hidden()

    page.click(".gth-theme-toggle")
    assert bg() != dark_bg
    expect(page.locator(".gth-logo-on-light")).to_be_visible()
    expect(page.locator(".gth-logo-on-dark")).to_be_hidden()
    brand = page.locator(".gth-navbar-brand").evaluate("el => getComputedStyle(el).color")
    assert brand == "rgb(18, 122, 19)"  # #127a13, 5.2:1 on the light navbar


def test_secondary_buttons_follow_color_mode(page, playground_url):
    page.goto(f"{playground_url}/forms")
    button = page.locator(".gth-busy-button")  # btn-outline-secondary
    # to_have_css retries: .btn transitions its color
    expect(button).to_have_css("color", "rgb(206, 212, 218)")  # #ced4da: 10.3:1 on dark
    page.click(".gth-theme-toggle")
    expect(button).to_have_css("color", "rgb(108, 117, 125)")  # Bootstrap's light value


# ── gth_data_table / TableState ──────────────────────────────────────────

RECORD_ROWS = "#records tbody tr[data-record-id]"


def _htmx_idle(page):
    """Wait out htmx's swap/settle (20ms by default): a control swapped in
    moments ago isn't wired up yet, and Playwright acts faster than that."""
    page.wait_for_function(
        "() => !document.querySelector('.htmx-request, .htmx-swapping, .htmx-settling')"
    )
    page.wait_for_timeout(50)


def test_data_table_pages_navigation_pushes_url(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    expect(page.locator(RECORD_ROWS)).to_have_count(10)
    page.click("#records .gth-table-pager >> text=3")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("21–30 of 120")
    assert "page=3" in page.url
    _htmx_idle(page)
    page.select_option("#records-size", "25")
    expect(page.locator(RECORD_ROWS)).to_have_count(25)
    expect(page.locator("#records .gth-table-summary")).to_contain_text("1–25 of 120")


def test_data_table_sort_toggles(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    price_header = page.locator("#records th:has-text('Price')")
    price_header.locator("button").click()
    expect(price_header).to_have_attribute("aria-sort", "ascending")
    first_asc = page.locator(RECORD_ROWS).first.inner_text()
    _htmx_idle(page)
    page.locator("#records th:has-text('Price') button").click()
    price_header = page.locator("#records th:has-text('Price')")
    expect(price_header).to_have_attribute("aria-sort", "descending")
    expect(page.locator(RECORD_ROWS).first).not_to_have_text(first_asc)


def test_data_table_filter_debounced_and_resets_page(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages&page=4")
    page.fill(".gth-table-filter input[type=search]", "kilo")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 20")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("1–10")
    page.click(".gth-table-filter label:has-text('Cable')")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 10")
    assert page.locator(".gth-table-filter input[type=search]").input_value() == "kilo"


def test_data_table_load_more(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=load_more")
    expect(page.locator(RECORD_ROWS)).to_have_count(10)
    _htmx_idle(page)
    page.click("#records .gth-table-load-more button")
    expect(page.locator(RECORD_ROWS)).to_have_count(20)


def test_data_table_infinite_scroll_until_exhausted(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=infinite")
    rows = page.locator(RECORD_ROWS)
    expect(rows).to_have_count(10)
    for _ in range(20):
        if rows.count() >= 120:
            break
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(150)
    expect(rows).to_have_count(120)
    expect(page.locator("#records .gth-table-infinite")).to_have_count(0)


def test_data_table_infinite_inside_scroll_box(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=infinite&scroll=1")
    rows = page.locator(RECORD_ROWS)
    expect(rows).to_have_count(10)
    box = page.locator("#records-scroll")
    box.evaluate("el => el.scrollTop = el.scrollHeight")
    expect(rows).to_have_count(20)
    # The header sticks to the top of the scroll box.
    th = page.locator("#records thead th").first
    assert th.evaluate("el => getComputedStyle(el).position") == "sticky"


# ── gth-badge / gth-tabs / gth-chips / gth-switch ─────────────────────────


def test_tabs_lazy_load_once_and_keyboard(page, playground_url):
    page.goto(f"{playground_url}/layout")
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/v07-demo/tab/" in r.url else None)
    activity = page.locator("#demo-tabs-pane-activity")
    expect(activity.locator(".gth-skeleton")).to_have_count(1)

    page.click("#demo-tabs-tab-activity")
    expect(page.locator("#demo-tabs-tab-activity")).to_have_attribute("aria-selected", "true")
    expect(activity.locator("[data-tab-loaded=activity]")).to_be_visible()

    # Arrow keys move between tabs (Bootstrap's own tab JS).
    page.keyboard.press("ArrowRight")
    expect(page.locator("#demo-tabs-tab-settings")).to_be_focused()
    expect(page.locator("#demo-tabs-pane-settings [data-tab-loaded=settings]")).to_be_visible()

    page.click("#demo-tabs-tab-activity")
    page.wait_for_timeout(500)
    assert sum("/tab/activity" in u for u in requests) == 1  # loaded once, not per show


def test_chips_and_switch_submit_like_checkboxes(page, playground_url):
    page.goto(f"{playground_url}/forms")
    result = page.locator("#chips-demo-result")
    page.click("#chips-demo label:has-text('Sensors')")
    expect(result).to_have_text("tags=sensor, tags=motor, alerts=on")
    page.click("#chips-demo label:has-text('Motors')")
    page.click("#gth-field-alerts")
    expect(result).to_have_text("tags=sensor")
    checked = page.locator("#chips-demo label:has-text('Sensors') .gth-chip-check")
    expect(checked).to_be_visible()
    unchecked = page.locator("#chips-demo label:has-text('Motors') .gth-chip-check")
    expect(unchecked).to_be_hidden()


# ── gth-multiselect ──────────────────────────────────────────────────────

MS_INPUT = "#gth-field-widgets-search"
MS_RESULTS = "#gth-field-widgets-results"
MS_CHIPS = "#multi-demo [data-gth-combobox-name=widgets] [data-gth-combobox-chip]"
TAG_INPUT = "#gth-field-tags-search"
TAG_CHIPS = "#multi-demo [data-gth-combobox-name=tags] [data-gth-combobox-chip]"


def test_multiselect_pick_hides_chosen_and_backspace_removes(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(MS_INPUT)
    expect(page.locator(f"{MS_RESULTS} [data-value]")).to_have_count(10)
    page.click(f"{MS_RESULTS} [data-value='1']")
    expect(page.locator(MS_CHIPS)).to_have_count(1)
    expect(page.locator(MS_INPUT)).to_be_focused()
    expect(page.locator(MS_RESULTS)).to_be_visible()  # stays open for the next pick
    expect(page.locator(f"{MS_RESULTS} [data-value='1']")).to_be_hidden()

    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(page.locator(MS_CHIPS)).to_have_count(2)
    # The refreshed list starts on #2 (#1 is hidden); ArrowDown moves to #3.
    assert page.locator(MS_CHIPS).nth(1).get_attribute("data-value") == "3"
    page.keyboard.press("Backspace")
    expect(page.locator(MS_CHIPS)).to_have_count(1)
    expect(page.locator("#multi-demo [data-gth-combobox-live]").first).to_have_text(
        "Removed Widget #3")


def test_multiselect_max_items_toasts_and_remove_stays_closed(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(MS_INPUT)
    for value in ("1", "2", "3", "4", "5"):
        page.click(f"{MS_RESULTS} [data-value='{value}']")
    expect(page.locator(MS_CHIPS)).to_have_count(5)
    page.click(f"{MS_RESULTS} [data-value='6']")  # one over max_items=5
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("You can choose up to 5 widgets.")
    expect(page.locator(MS_CHIPS)).to_have_count(5)

    # Removing a chip doesn't open the list; focus moves to the next chip.
    page.keyboard.press("Escape")
    expect(page.locator(MS_RESULTS)).to_be_hidden()
    page.click(f"{MS_CHIPS} >> nth=0 >> [data-gth-combobox-remove]")
    expect(page.locator(MS_CHIPS)).to_have_count(4)
    expect(page.locator(MS_RESULTS)).to_be_hidden()
    expect(page.locator(f"{MS_CHIPS} >> nth=0 >> [data-gth-combobox-remove]")).to_be_focused()

    # Removing the last chip hands focus back to the input — still closed.
    for _ in range(4):
        page.click(f"{MS_CHIPS} >> nth=0 >> [data-gth-combobox-remove]")
    expect(page.locator(MS_CHIPS)).to_have_count(0)
    expect(page.locator(MS_INPUT)).to_be_focused()
    expect(page.locator(MS_RESULTS)).to_be_hidden()

    # Clicking into the (already focused) input opens it.
    page.click(MS_INPUT)
    expect(page.locator(MS_RESULTS)).to_be_visible()


def test_multiselect_unpicked_text_is_cleared_on_blur(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.fill(MS_INPUT, "Wid")
    expect(page.locator(MS_RESULTS)).to_be_visible()
    page.click("h2:has-text('gth-multiselect')")  # outside
    expect(page.locator(MS_RESULTS)).to_be_hidden()
    assert page.input_value(MS_INPUT) == ""
    expect(page.locator(MS_CHIPS)).to_have_count(0)

    page.fill(TAG_INPUT, "half-typed")
    page.keyboard.press("Tab")
    assert page.input_value(TAG_INPUT) == ""
    expect(page.locator(TAG_CHIPS)).to_have_count(1)  # just the pre-filled "urgent"


def test_combobox_click_reopens_after_escape(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(MS_INPUT)
    expect(page.locator(MS_RESULTS)).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator(MS_RESULTS)).to_be_hidden()
    expect(page.locator(MS_INPUT)).to_be_focused()
    page.click(MS_INPUT)
    expect(page.locator(MS_RESULTS)).to_be_visible()


def test_tags_enter_comma_and_422_round_trip(page, playground_url):
    page.goto(f"{playground_url}/forms")
    expect(page.locator(TAG_CHIPS)).to_have_count(1)  # "urgent" pre-filled
    page.fill(TAG_INPUT, "blue")
    page.keyboard.press("Enter")
    page.type(TAG_INPUT, "red,")
    page.fill(TAG_INPUT, "urgent")  # duplicate: ignored, and cleared
    page.keyboard.press("Enter")
    expect(page.locator(TAG_CHIPS)).to_have_count(3)
    assert page.input_value(TAG_INPUT) == ""

    page.click("#multi-demo button[type=submit]")  # no widgets picked → 422
    expect(page.locator("#multi-demo")).to_contain_text("Pick at least one widget.")
    expect(page.locator(TAG_CHIPS)).to_have_count(3)  # tags echoed back

    page.click(MS_INPUT)
    page.click(f"{MS_RESULTS} [data-value='2']")
    page.keyboard.press("Escape")  # the panel stays open after a pick
    page.click("#multi-demo button[type=submit]")
    expect(page.locator("#multi-demo-saved")).to_have_text("Saved: widgets=2 tags=urgent,blue,red")


# ── gth-record-picker ────────────────────────────────────────────────────

PART_TRIGGER = "#gth-field-part-trigger"
PART_PANEL = "#gth-field-part-panel"


def test_record_picker_search_page_and_keyboard_pick(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    expect(panel).to_be_visible()
    # Moved out of the form: its filter <form> mustn't nest in #record-demo.
    assert panel.evaluate("el => el.parentElement === document.body")
    search = panel.locator("input[type=search]")
    expect(search).to_be_focused()
    expect(panel.locator("[data-gth-pick]")).to_have_count(10)

    # Page inside the panel, then search.
    _htmx_idle(page)
    panel.get_by_role("link", name="Page 2", exact=True).click()
    expect(panel.locator(".gth-table-summary")).to_contain_text("11–20 of 120")
    expect(panel.locator(".gth-table-filter")).to_have_count(1)  # swaps don't duplicate it
    search.fill("kilo part 010")
    expect(panel.locator("[data-gth-pick]")).to_have_count(1)
    _htmx_idle(page)

    search.focus()
    page.keyboard.press("ArrowDown")
    expect(panel.locator("[data-gth-pick]").first).to_be_focused()
    page.keyboard.press("Enter")
    expect(panel).to_be_hidden()
    expect(page.locator(PART_TRIGGER)).to_be_focused()
    expect(page.locator(PART_TRIGGER)).to_have_text("Kilo part 010")
    expect(page.locator("#record-demo-result")).to_have_text("part=10 (Kilo part 010)")

    # Reopening keeps the panel's state and marks the current pick.
    page.click(PART_TRIGGER)
    expect(panel.locator("[data-gth-pick][aria-current=true]")).to_have_count(1)
    page.mouse.click(5, 5)  # outside
    expect(panel).to_be_hidden()

    page.click("#record-demo [data-gth-record-picker-clear]")
    expect(page.locator(PART_TRIGGER)).to_have_text("Choose a part…")
    expect(page.locator("#record-demo-result")).to_have_text("Nothing picked.")


def test_record_picker_in_modal_esc_keeps_modal_and_422_keeps_pick(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click("#gth-field-record-trigger")
    panel = page.locator("#gth-field-record-panel")
    expect(panel).to_be_visible()
    # Inside the .modal, so Bootstrap's focus trap leaves the search box alone.
    assert panel.evaluate("el => el.parentElement.classList.contains('modal')")
    expect(panel.locator("input[type=search]")).to_be_focused()
    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(page.locator(MODAL)).to_be_visible()
    expect(page.locator("#gth-field-record-trigger")).to_be_focused()

    page.click("#gth-field-record-trigger")
    panel.locator("[data-gth-pick]").first.click()  # sorted by name: Alpha part 006
    expect(page.locator("#gth-field-record-trigger")).to_have_text("Alpha part 006")

    page.click("#gth-modal-host button[type=submit]")  # no widget → 422 re-render
    expect(page.locator("#gth-modal-host")).to_contain_text("Pick a widget from the list.")
    expect(page.locator("#gth-field-record-trigger")).to_have_text("Alpha part 006")
    # The re-rendered picker gets a fresh panel; the old portaled one is gone.
    page.click("#gth-field-record-trigger")
    expect(page.locator("#gth-field-record-panel")).to_have_count(1)
    expect(page.locator("#gth-field-record-panel [data-gth-pick]")).to_have_count(10)
    page.keyboard.press("Escape")

    page.click(COMBO_INPUT)
    page.click(f"{COMBO_RESULTS} [data-value='3']")
    page.click("#gth-modal-host button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved Widget #3 (S) for Alpha part 006")


def test_switch_focus_knob_is_brand_colored(page, playground_url):
    page.goto(f"{playground_url}/forms")
    switch = page.locator("#gth-field-alerts")
    switch.click()  # unchecks it and leaves it focused
    expect(switch).not_to_be_checked()
    expect(switch).to_be_focused()
    knob = switch.evaluate("el => getComputedStyle(el).getPropertyValue('--bs-form-switch-bg')")
    assert "1FBE1E" in knob and "86b7fe" not in knob


def test_infinite_scroll_box_does_not_grow_the_page(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/tables?mode=infinite&scroll=1")
    rows = page.locator(RECORD_ROWS)
    box = page.locator("#records-scroll")
    doc_height = page.evaluate("document.documentElement.scrollHeight")
    for expected in (20, 30, 40):
        box.evaluate("el => el.scrollTop = el.scrollHeight")
        expect(rows).to_have_count(expected)
        _htmx_idle(page)
        assert page.evaluate("document.documentElement.scrollHeight") == doc_height


def test_record_picker_search_then_click_fires_no_extra_request(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    expect(panel.locator("input[type=search]")).to_be_focused()  # panel ready
    panel.locator("input[type=search]").fill("part 01")
    expect(panel.locator(".gth-table-summary")).to_contain_text("1–10 of 10")  # search landed
    _htmx_idle(page)
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "record-picker" in r.url else None)
    row = panel.locator("[data-gth-pick]").nth(2)
    label = row.get_attribute("data-label")
    row.click()  # blurs the search box: its `change` must not re-request the table
    expect(page.locator(PART_TRIGGER)).to_have_text(label)
    page.wait_for_timeout(300)
    assert requests == []


def test_record_picker_row_swapped_out_mid_click_is_still_picked(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    expect(panel.locator("[data-gth-pick]")).to_have_count(10)
    _htmx_idle(page)
    row = panel.locator("[data-gth-pick]").nth(3)
    label = row.get_attribute("data-label")
    box = row.bounding_box()
    page.mouse.move(box["x"] + 20, box["y"] + box["height"] / 2)
    page.mouse.down()
    # A swap lands between press and release (as a debounced search would).
    page.evaluate("""() => htmx.ajax('GET', '/v07-demo/record-picker?for=page&page=2',
                                      {target: '#picker-page', swap: 'outerHTML'})""")
    expect(panel.locator(".gth-table-summary")).to_contain_text("11–20 of 120")
    page.mouse.up()
    expect(page.locator(PART_TRIGGER)).to_have_text(label)  # the pressed row, not page 2's
    expect(panel).to_be_hidden()


def test_record_picker_escape_before_panel_loads_keeps_modal(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click("#gth-field-record-trigger")
    page.keyboard.press("Escape")  # immediately: focus may still be on the trigger
    expect(page.locator("#gth-field-record-panel")).to_be_hidden()
    expect(page.locator(MODAL)).to_be_visible()


def test_record_picker_expand_shrink_and_dismiss(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    search = panel.locator("input[type=search]")
    expect(search).to_be_focused()
    search.fill("bravo")
    expect(panel.locator(".gth-table-summary")).to_contain_text("of 20")
    small = panel.bounding_box()
    backdrop = page.locator("[data-gth-record-picker-backdrop][data-for=gth-field-part-panel]")

    toggle = panel.locator("[data-gth-record-picker-size]")
    toggle.click()
    expect(panel).to_have_class(re.compile("gth-record-picker-panel--modal"))
    expect(toggle).to_have_attribute("aria-pressed", "true")
    expect(backdrop).to_be_visible()
    big = panel.bounding_box()
    assert big["width"] > small["width"]
    assert abs((big["x"] + big["width"] / 2) - 640) < 4  # centred
    assert search.input_value() == "bravo"  # content kept, not reloaded
    expect(panel.locator(".gth-table-summary")).to_contain_text("of 20")

    # Tab wraps inside the panel at modal size.
    panel.locator("[data-gth-record-picker-size]").focus()
    page.keyboard.press("Shift+Tab")
    focused_inside = page.evaluate(
        "document.getElementById('gth-field-part-panel').contains(document.activeElement)")
    assert focused_inside

    toggle.click()  # shrink: back under the trigger
    expect(backdrop).to_be_hidden()
    trigger_box = page.locator(PART_TRIGGER).bounding_box()
    assert abs(panel.bounding_box()["y"] - (trigger_box["y"] + trigger_box["height"])) < 10

    toggle.click()
    backdrop.click(position={"x": 10, "y": 10})  # dismiss via the backdrop
    expect(panel).to_be_hidden()
    expect(backdrop).to_be_hidden()
    expect(page.locator(PART_TRIGGER)).to_be_focused()
    assert "gth-picker-modal-open" not in (page.locator("body").get_attribute("class") or "")

    page.click(PART_TRIGGER)  # reopens at its configured size (panel)
    expect(panel).not_to_have_class(re.compile("gth-record-picker-panel--modal"))
    panel.locator("[data-gth-record-picker-close]").click()
    expect(panel).to_be_hidden()


def test_record_picker_modal_size_inside_bootstrap_modal(page, playground_url):
    _open_v07_modal(page, playground_url)
    page.click("#gth-field-record-trigger")
    panel = page.locator("#gth-field-record-panel")
    expect(panel.locator("input[type=search]")).to_be_focused()
    panel.locator("[data-gth-record-picker-size]").click()
    expect(panel).to_have_class(re.compile("gth-record-picker-panel--modal"))
    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(page.locator(MODAL)).to_be_visible()  # only the picker closed

    page.click("#gth-field-record-trigger")
    panel.locator("[data-gth-record-picker-size]").click()
    row = panel.locator("[data-gth-pick]").first
    label = row.get_attribute("data-label")
    row.click()
    expect(page.locator("#gth-field-record-trigger")).to_have_text(label)
    expect(page.locator("[data-gth-record-picker-backdrop][data-for=gth-field-record-panel]")).to_be_hidden()


# ── gth-sidebar (layout="sidebar") ───────────────────────────────────────

SB = "#gth-sidebar-nav"


def _group(page, label):
    return page.locator(f"[data-gth-sidebar-group='{label}']")


def test_sidebar_active_trail_and_remembered_groups(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar/archive/2024")
    active = page.locator(f"{SB} [aria-current=page]")
    expect(active).to_have_text("2024")
    expect(_group(page, "Inventory")).to_have_attribute("aria-expanded", "true")
    expect(_group(page, "Archive")).to_have_attribute("aria-expanded", "true")
    expect(_group(page, "Reports")).to_have_attribute("aria-expanded", "false")

    _group(page, "Reports").click()
    expect(page.locator(f"{SB} a:has-text('Monthly')")).to_be_visible()
    page.locator(f"{SB} a:has-text('Settings')").click()
    expect(page.locator("#sidebar-demo-path")).to_have_text("/layouts/sidebar/settings")
    # Reports was opened by hand: remembered on the next page.
    expect(_group(page, "Reports")).to_have_attribute("aria-expanded", "true")

    # Breadcrumbs derived from the nav tree (url-less groups aren't links).
    page.goto(f"{playground_url}/layouts/sidebar/reports/monthly")
    crumbs = page.locator("nav[aria-label=breadcrumb]")
    expect(crumbs.locator("a")).to_have_text(["Reports"])
    expect(crumbs.locator("[aria-current=page]")).to_have_text("Monthly")


def test_sidebar_filter_hides_expands_and_restores(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar")
    page.evaluate("localStorage.removeItem('gth-sidebar-open')")
    page.reload()
    flt = page.locator("[data-gth-sidebar-filter]")
    flt.fill("mon")
    expect(page.locator(f"{SB} a:has-text('Monthly')")).to_be_visible()
    expect(page.locator(f"{SB} a:has-text('Settings')")).to_be_hidden()
    expect(_group(page, "Reports")).to_have_attribute("aria-expanded", "true")
    flt.fill("zzz")
    expect(page.locator(f"{SB} [data-gth-sidebar-empty]")).to_be_visible()
    flt.fill("")
    expect(page.locator(f"{SB} a:has-text('Settings')")).to_be_visible()
    expect(_group(page, "Reports")).to_have_attribute("aria-expanded", "false")  # restored
    expect(page.locator(f"{SB} [data-gth-sidebar-empty]")).to_be_hidden()


def test_sidebar_rail_persists_and_flyout(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar/parts")
    sidebar = page.locator("#gth-sidebar")
    full_width = sidebar.bounding_box()["width"]
    rail = page.locator("[data-gth-sidebar-rail]")
    rail.click()
    expect(rail).to_have_attribute("aria-pressed", "true")
    page.wait_for_timeout(250)  # width transition
    assert sidebar.bounding_box()["width"] < full_width / 2
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-gth-sidebar", "rail")
    expect(rail).to_have_attribute("aria-label", "Expand sidebar")

    reports = _group(page, "Reports")
    reports.click()
    flyout = page.locator(f"{SB} li.gth-flyout-open > ul")
    expect(flyout).to_be_visible()
    expect(flyout.locator("a:has-text('Monthly')")).to_be_visible()
    # Above the page's content, not behind it.
    box = flyout.bounding_box()
    x, y = box["x"] + 30, box["y"] + 15
    top = page.evaluate(f"document.elementFromPoint({x}, {y}).closest('ul')?.id")
    assert top == flyout.get_attribute("id")
    page.keyboard.press("Escape")
    expect(flyout).to_be_hidden()
    expect(reports).to_be_focused()
    # The Inventory group (open on this page) doesn't show as a flyout.
    expect(page.locator(f"{SB} a:has-text('Suppliers')")).to_be_hidden()

    page.locator("[data-gth-sidebar-rail]").click()  # back to full
    expect(page.locator(f"{SB} a:has-text('Suppliers')")).to_be_visible()


def test_sidebar_drawer_on_mobile(page, playground_url):
    page.set_viewport_size({"width": 375, "height": 740})
    page.goto(f"{playground_url}/layouts/sidebar")
    drawer = page.locator("#gth-sidebar")
    expect(drawer).to_be_hidden()
    expect(page.locator("[data-gth-sidebar-rail]")).to_be_hidden()
    page.click(".gth-sidebar-open")
    expect(drawer).to_be_visible()
    expect(drawer).to_have_class(re.compile("(^| )show( |$)"))  # done animating; Bootstrap
    expect(drawer).not_to_have_class(re.compile("showing"))   # ignores keys until then
    page.keyboard.press("Escape")
    expect(drawer).to_be_hidden()
    expect(page.locator(".gth-sidebar-open")).to_be_focused()

    page.click(".gth-sidebar-open")
    expect(drawer).not_to_have_class(re.compile("showing"))
    page.locator(f"{SB} a:has-text('Settings')").click()
    expect(page.locator("#sidebar-demo-path")).to_have_text("/layouts/sidebar/settings")
    expect(page.locator("#gth-sidebar")).to_be_hidden()


def test_sidebar_live_badge_refreshes_on_event(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar/reports/health")
    badge = page.locator(f"{SB} a:has-text('Health') .gth-nav-badge")
    page.click("#health-reset")
    expect(badge).to_have_text("3")
    page.click("#health-resolve")
    expect(badge).to_have_text("2")
    for _ in range(2):
        page.click("#health-resolve")
    expect(badge.locator(".badge")).to_have_count(0)  # zero: hidden
    page.click("#health-reset")
    expect(badge).to_have_text("3")


# ── gth-command-palette ──────────────────────────────────────────────────

CMD = "dialog[data-gth-command]"


def test_command_palette_keyboard_navigation(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar")
    page.locator("body").click()
    page.keyboard.press("Control+k")
    dialog = page.locator(CMD)
    expect(dialog).to_be_visible()
    expect(dialog.locator("[data-gth-command-input]")).to_be_focused()
    expect(dialog.locator("[data-gth-command-pages] [data-gth-command-option]")).to_have_count(9)

    page.keyboard.type("month")
    first = dialog.locator("[data-gth-command-option]").first
    expect(first).to_contain_text("Monthly")
    expect(first).to_contain_text("Reports › Monthly")
    expect(first).to_have_attribute("aria-selected", "true")
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile("/layouts/sidebar/reports/monthly$"))
    expect(page.locator(CMD)).to_be_hidden()


def test_command_palette_button_escape_and_server_results(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar")
    button = page.locator("[data-gth-command-open]")
    button.click()
    dialog = page.locator(CMD)
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(button).to_be_focused()

    button.click()
    page.keyboard.type("kilo part 01")
    results = dialog.locator("[data-gth-command-remote] [data-gth-command-option]")
    expect(results.first).to_contain_text("Kilo part 010")
    expect(dialog.locator("[data-gth-command-pages]")).to_be_hidden()  # no page matches
    expect(results.first).to_have_attribute("aria-selected", "true")
    page.keyboard.press("ArrowDown")
    expect(results.nth(1)).to_have_attribute("aria-selected", "true")
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"/layouts/sidebar/parts\?id="))

    page.locator("[data-gth-command-open]").click()
    page.keyboard.type("zzzz")
    expect(page.locator(f"{CMD} [data-gth-command-empty]")).to_be_visible()
    page.mouse.click(5, 5)  # the backdrop closes it
    expect(page.locator(CMD)).to_be_hidden()


# ── gth-tree ─────────────────────────────────────────────────────────────


def _node(page, tree, node_id):
    return page.locator(f"#{tree} [data-gth-node='{node_id}']")


def test_tree_keyboard_lazy_once_and_detail_pane(page, playground_url):
    page.goto(f"{playground_url}/tree")
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/tree/nodes" in r.url else None)
    sensor = _node(page, "explorer", "c:Sensor")
    sensor.focus()
    expect(sensor).to_have_attribute("tabindex", "0")
    page.keyboard.press("ArrowRight")  # expand
    expect(sensor).to_have_attribute("aria-expanded", "true")
    page.keyboard.press("ArrowRight")  # into the first child
    alpha = _node(page, "explorer", "a:Sensor:Alpha")
    expect(alpha).to_be_focused()
    page.keyboard.press("ArrowRight")  # expand → lazy load
    part = _node(page, "explorer", "p:12")
    expect(part).to_be_visible()
    page.keyboard.press("ArrowDown")
    expect(part).to_be_focused()
    expect(page.locator("#explorer [role=treeitem][tabindex='0']")).to_have_count(1)
    page.keyboard.press("Enter")  # select + detail
    expect(part).to_have_attribute("aria-selected", "true")
    expect(page.locator("#tree-detail [data-tree-detail=p]")).to_contain_text("Alpha part 012")
    expect(page.locator("[data-gth-tree-wrap] input[name=node]")).to_have_value("p:12")

    page.keyboard.press("ArrowLeft")  # leaf → parent
    expect(alpha).to_be_focused()
    page.keyboard.press("ArrowLeft")  # collapse
    expect(alpha).to_have_attribute("aria-expanded", "false")
    page.keyboard.press("ArrowRight")  # re-expand: no second request
    expect(part).to_be_visible()
    assert len(requests) == 1

    page.keyboard.press("Home")
    expect(sensor).to_be_focused()
    page.keyboard.press("m")  # type-ahead
    expect(_node(page, "explorer", "c:Motor")).to_be_focused()
    page.keyboard.press("End")
    expect(_node(page, "explorer", "c:Board")).to_be_focused()


def test_tree_tri_state_and_form_round_trip(page, playground_url):
    page.goto(f"{playground_url}/tree")
    motor = _node(page, "reorder", "c:Motor")
    bravo = _node(page, "reorder", "a:Motor:Bravo")
    motor.locator("> .gth-tree-row .gth-tree-twisty").click()
    bravo.locator("> .gth-tree-row .gth-tree-twisty").click()
    p1 = _node(page, "reorder", "p:1")
    expect(p1).to_be_visible()

    p1.locator("> .gth-tree-row").click()  # one part → ancestors mixed
    expect(p1).to_have_attribute("aria-checked", "true")
    expect(bravo).to_have_attribute("aria-checked", "mixed")
    expect(motor).to_have_attribute("aria-checked", "mixed")
    values = page.locator("#tree-reorder [data-gth-tree-values] input")
    expect(values).to_have_count(1)

    bravo.focus()
    page.keyboard.press(" ")  # check the whole assembly
    expect(bravo).to_have_attribute("aria-checked", "true")
    expect(bravo.locator("[role=treeitem][aria-checked=false]")).to_have_count(0)
    expect(values).to_have_count(1)  # top-most only: the assembly
    expect(values.first).to_have_value("a:Motor:Bravo")

    # Check every Motor assembly → the category becomes checked, one value.
    for item in motor.locator("> [role=group] > [role=treeitem]").all():
        if item.get_attribute("aria-checked") != "true":
            item.locator("> .gth-tree-row").click()
    expect(motor).to_have_attribute("aria-checked", "true")
    expect(values).to_have_count(1)
    expect(values.first).to_have_value("c:Motor")

    page.click("#tree-reorder button[type=submit]")
    expect(page.locator("#tree-reorder-result")).to_contain_text("30 parts")
    expect(page.locator("#tree-reorder-result")).to_contain_text("c:Motor")
    expect(_node(page, "reorder", "c:Motor")).to_have_attribute("aria-checked", "true")

    # Uncheck everything → 422 with the error, tree still interactive.
    _node(page, "reorder", "c:Motor").locator("> .gth-tree-row").click()
    page.click("#tree-reorder button[type=submit]")
    expect(page.locator("#tree-reorder-error")).to_contain_text("Tick at least one")
    _node(page, "reorder", "c:Board").locator("> .gth-tree-row").click()
    expect(page.locator("#tree-reorder [data-gth-tree-values] input")).to_have_value("c:Board")


def test_tree_lazy_children_of_a_checked_parent_arrive_checked(page, playground_url):
    page.goto(f"{playground_url}/tree")
    cable = _node(page, "reorder", "c:Cable")
    cable.locator("> .gth-tree-row").click()  # check before anything is loaded
    cable.locator("> .gth-tree-row .gth-tree-twisty").click()
    asm = cable.locator("> [role=group] > [role=treeitem]").first
    asm.locator("> .gth-tree-row .gth-tree-twisty").click()
    parts = asm.locator("> [role=group] > [role=treeitem]")
    expect(parts).to_have_count(10)
    expect(asm.locator("[role=treeitem][aria-checked=true]")).to_have_count(10)
    expect(page.locator("#tree-reorder [data-gth-tree-values] input")).to_have_value("c:Cable")


# ── Playground on layout="sidebar" ───────────────────────────────────────

MAIN_NAV = "#gth-sidebar-nav"


def test_playground_sidebar_trail_breadcrumbs_and_anchor_scroll(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/tables")
    expect(page.locator(f"{MAIN_NAV} [aria-current=page]")).to_have_text("Data tables")
    expect(page.locator(f"{MAIN_NAV} [data-gth-sidebar-group='Data']")).to_have_attribute(
        "aria-expanded", "true")
    crumbs = page.locator("main nav[aria-label=breadcrumb]").first
    expect(crumbs.locator("a")).to_have_text(["Data"])

    # An in-page anchor lands below the sticky navbar, not under it.
    page.locator(f"{MAIN_NAV} [data-gth-sidebar-group='Forms']").click()
    page.locator(f"{MAIN_NAV} a:has-text('Multiselect + tags')").click()
    expect(page).to_have_url(re.compile("/forms#multiselect$"))
    heading = page.locator("#multiselect h2")
    navbar_bottom = page.locator("nav.gth-navbar").bounding_box()
    expect(heading).to_be_in_viewport()
    assert heading.bounding_box()["y"] >= navbar_bottom["y"] + navbar_bottom["height"]


def test_playground_watchlist_live_badge(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/overlays")
    badge = page.locator(f"{MAIN_NAV} a:has-text('Confirm delete') .gth-nav-badge")
    items = page.locator("#watchlist-demo-list .list-group-item")
    count = items.count()  # server state: other tests may have deleted some
    if count == 0:
        expect(badge.locator(".badge")).to_have_count(0)
        return
    expect(badge).to_have_text(str(count))
    page.locator("#watchlist-demo-list").get_by_role("button", name="Remove").first.click()
    page.locator(".gth-modal.show").get_by_role("button", name="Delete").click()
    expect(items).to_have_count(count - 1)
    if count - 1:
        expect(badge).to_have_text(str(count - 1))
    else:
        expect(badge.locator(".badge")).to_have_count(0)


def test_playground_palette_reaches_demo_anchors(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(playground_url)
    page.locator("main h1").click()  # focus the page, away from any link
    page.keyboard.press("Control+k")
    page.keyboard.type("record pick")
    first = page.locator("dialog[data-gth-command] [data-gth-command-option]").first
    expect(first).to_contain_text("Forms › Record picker")
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile("/forms#record-picker$"))


# ── gth-toast ────────────────────────────────────────────────────────────


def _fire_toast(page, detail):
    page.evaluate(
        "d => document.body.dispatchEvent(new CustomEvent('showToast', {detail: d}))", detail)


def test_toast_message_is_text_not_html(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    _fire_toast(page, {"message": '<img src=x onerror="window.__pwned=1">Hi', "kind": "info"})
    toast = page.locator(DYNAMIC_TOAST).last
    expect(toast).to_contain_text('<img src=x onerror="window.__pwned=1">Hi')
    expect(toast.locator("img")).to_have_count(0)
    assert page.evaluate("window.__pwned") is None


def test_toast_warning_close_button_is_readable(page, playground_url):
    page.goto(f"{playground_url}/feedback")  # dark mode: Bootstrap inverts .btn-close
    for kind, dark_close in (("warning", True), ("info", True), ("danger", False)):
        _fire_toast(page, {"message": kind, "kind": kind, "variant": "solid"})
        close = page.locator(f"{DYNAMIC_TOAST} .btn-close").last
        expect(close).to_be_visible()
        # The white close is an inverting filter; on a light fill it must be off.
        inverted = close.evaluate("el => getComputedStyle(el).filter") not in ("none", "")
        assert inverted is not dark_close, kind


def _preset(page, name):
    page.click(f"[data-toast-preset='{name}']")
    return page.locator(DYNAMIC_TOAST).last


def test_toast_presets_render_every_option(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    for kind in ("success", "info", "warning", "danger", "neutral"):
        toast = _preset(page, kind)
        expect(toast).to_have_class(re.compile(f"gth-toast-{kind} gth-toast-surface"))
        urgent = kind in ("warning", "danger")
        expect(toast).to_have_attribute("role", "alert" if urgent else "status")
        expect(toast).to_have_attribute("aria-live", "assertive" if urgent else "polite")
        expect(toast.locator(".gth-toast-progress")).to_have_count(1)

    toast = _preset(page, "title")
    expect(toast.locator(".gth-toast-title")).to_have_text("Deploy finished")
    toast = _preset(page, "action")
    expect(toast.locator("a.gth-toast-action")).to_have_attribute("href", "/feedback#toast")
    toast = _preset(page, "icon")
    expect(toast.locator(".gth-toast-icon")).to_have_class(re.compile("bi-rocket-takeoff"))
    toast = _preset(page, "html")
    expect(toast.locator(".gth-toast-message strong")).to_have_text("Trusted markup")
    toast = _preset(page, "solid-warning")
    expect(toast).to_have_class(re.compile("text-bg-warning"))


def test_toast_sticky_stays_and_quick_leaves(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    sticky = _preset(page, "sticky")
    expect(sticky.locator(".gth-toast-progress")).to_have_count(0)
    quick = _preset(page, "quick")
    expect(quick).to_be_visible()
    page.mouse.move(5, 5)  # not hovering either: hovering pauses auto-hide
    expect(page.locator(f"{DYNAMIC_TOAST}:has-text('Gone in 1.5 seconds')")).to_have_count(
        0, timeout=4000)
    page.wait_for_timeout(5500)  # past the default duration too
    expect(page.locator(f"{DYNAMIC_TOAST}:has-text('stays until you close it')")).to_be_visible()
    page.locator(f"{DYNAMIC_TOAST}:has-text('stays until you close it') .btn-close").click()
    gone = page.locator("#gth-toast-container :has-text('stays until you close it')")
    expect(gone).to_have_count(0)


def test_toast_extra_events_refresh_the_nav_badge(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/feedback")
    requests = []
    page.on("request",
            lambda r: requests.append(r.url) if "/nav-badges/watchlist" in r.url else None)
    _preset(page, "events")
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("watchlistChanged")
    page.wait_for_timeout(300)
    assert requests, "the extra HX-Trigger event re-fetched the live badge"


# ── gth-back-to-top ──────────────────────────────────────────────────────


def test_back_to_top_appears_scrolls_up_and_focuses_main(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 700})
    page.emulate_media(reduced_motion="reduce")  # instant scroll: deterministic
    page.goto(f"{playground_url}/forms")
    button = page.locator("[data-gth-back-to-top]")
    expect(button).to_be_hidden()
    page.evaluate("window.scrollTo(0, 300)")
    expect(button).to_be_hidden()  # under the 400px threshold
    page.evaluate("window.scrollTo(0, 1200)")
    expect(button).to_be_visible()
    button.click()
    page.wait_for_function("window.scrollY === 0")
    expect(page.locator("main")).to_be_focused()
    expect(button).to_be_hidden()


def test_back_to_top_lifts_the_toast_stack(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 700})
    page.goto(f"{playground_url}/feedback")
    page.evaluate("document.body.style.minHeight = '3000px'; window.scrollTo(0, 1500)")
    button = page.locator("[data-gth-back-to-top]")
    expect(button).to_be_visible()
    page.evaluate("""document.body.dispatchEvent(new CustomEvent('showToast',
        {detail: {message: 'Over the button?', kind: 'info', duration: 0}}))""")
    toast = page.locator(DYNAMIC_TOAST).last
    expect(toast).to_be_visible()
    t, b = toast.bounding_box(), button.bounding_box()
    assert t["y"] + t["height"] <= b["y"], "the toast stack sits above the button"


def test_record_picker_near_page_end_makes_room_for_the_whole_panel(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/forms")
    trigger = page.locator(PART_TRIGGER)
    top = trigger.evaluate("e => e.getBoundingClientRect().top + scrollY")
    page.evaluate("y => window.scrollTo(0, y)", top - 800 + 330)  # 330px from the bottom
    doc_height = page.evaluate("document.documentElement.scrollHeight")
    trigger.click()
    panel = page.locator(PART_PANEL)
    expect(panel.locator("[data-gth-pick]")).to_have_count(10)
    _htmx_idle(page)
    rect = panel.evaluate("e => e.getBoundingClientRect().toJSON()")
    assert rect["bottom"] <= page.evaluate("innerHeight"), "the whole panel is on screen"
    pager = panel.locator(".gth-table-pager").evaluate("e => e.getBoundingClientRect().toJSON()")
    assert pager["bottom"] <= rect["bottom"], "the pager is inside the panel's visible area"
    # The trigger stays visible below the sticky navbar.
    nav_bottom = page.locator("nav.gth-navbar").evaluate("e => e.getBoundingClientRect().bottom")
    assert trigger.evaluate("e => e.getBoundingClientRect().top") >= nav_bottom

    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(page.locator("[data-gth-picker-spacer]")).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollHeight") == doc_height


def test_record_picker_modal_size_scrolls_only_the_table(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    expect(panel.locator("input[type=search]")).to_be_focused()
    panel.locator("[data-gth-record-picker-size]").click()
    _htmx_idle(page)
    panel.locator(".gth-table-size").select_option("50")
    expect(panel.locator("[data-gth-pick]")).to_have_count(50)
    _htmx_idle(page)
    search = panel.locator("input[type=search]")
    pager = panel.locator(".gth-table-pager")
    before = (search.bounding_box(), pager.bounding_box())
    scroller = panel.locator(".gth-data-table > .gth-table-wrapper")
    assert scroller.evaluate("e => e.scrollHeight > e.clientHeight"), "the table overflows"
    scroller.evaluate("e => e.scrollTop = e.scrollHeight")
    page.wait_for_timeout(100)
    assert (search.bounding_box(), pager.bounding_box()) == before
    assert page.evaluate("""() => { const p = document.querySelector('#gth-field-part-panel');
        const pr = p.getBoundingClientRect();
        const g = p.querySelector('.gth-table-pager').getBoundingClientRect();
        return g.bottom <= pr.bottom && g.top >= pr.top; }""")


def test_record_picker_room_keeps_the_sidebar_column(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/forms")
    trigger = page.locator(PART_TRIGGER)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    trigger.click()
    expect(page.locator(f"{PART_PANEL} [data-gth-pick]")).to_have_count(10)
    _htmx_idle(page)
    assert page.locator("main [data-gth-picker-spacer]").count() == 1
    sidebar = page.locator("#gth-sidebar").bounding_box()
    assert sidebar["y"] + sidebar["height"] >= page.evaluate("innerHeight") - 1, \
        "the sticky sidebar still reaches the bottom of the viewport"
