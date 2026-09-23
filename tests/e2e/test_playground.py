"""Playwright smoke tests against the real /playground app (docs/testing.md).

Skips cleanly (not fails) if playwright isn't installed — see conftest.py's
`pytest.importorskip`.
"""

from urllib.parse import urlparse

from playwright.sync_api import expect

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
    page.goto(playground_url)

    page.fill("#gth-field-budget", "-5")
    page.click("#form-demo-container button[type=submit]")
    page.wait_for_selector("#gth-field-budget.is-invalid")
    assert "greater than or equal to 0" in page.inner_text("#form-demo-container")

    page.fill("#gth-field-budget", "250")
    page.click("#form-demo-container button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved budget")


def test_standalone_toast_trigger(page, playground_url):
    page.goto(playground_url)
    page.click("text=Trigger a toast")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Demo toast triggered")


def test_table_filter_and_keyboard_focus(page, playground_url):
    page.goto(playground_url)
    assert "Design onboarding flow" in page.inner_text("#tasks-tbody")

    page.locator("#task-q-input").focus()
    page.keyboard.type("CI")

    tbody = page.locator("#tasks-tbody")
    expect(tbody).not_to_contain_text("Design onboarding flow")
    expect(tbody).to_contain_text("Fix flaky CI job")


def test_extra_css_and_js_and_head_slots_actually_work(page, playground_url):
    page.goto(playground_url)

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
    page.goto(playground_url)
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
    page.goto(playground_url)
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
    page.goto(playground_url)
    page.wait_for_load_state("networkidle")

    assert off_origin_urls == []


# ── v0.7: modal host, combobox, segmented, busy button, table load-more ────

MODAL = "#gth-modal-host .modal.show"
COMBO_INPUT = "#gth-field-widget-search"
COMBO_VALUE = "#gth-modal-host input[name=widget]"
COMBO_RESULTS = "#gth-field-widget-results"


def _open_v07_modal(page, playground_url):
    page.goto(playground_url)
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
    page.goto(playground_url)
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
    page.goto(playground_url)
    rows = page.locator("#widgets-tbody tr:not(.gth-table-load-more)")
    expect(rows).to_have_count(5)
    for expected in (10, 15, 16):
        page.click("#widgets-tbody .gth-table-load-more button")
        expect(rows).to_have_count(expected)
    expect(page.locator("#widgets-tbody .gth-table-load-more")).to_have_count(0)


def test_modal_host_reopen_does_not_leak_backdrops(page, playground_url):
    page.goto(playground_url)
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
    page.goto(playground_url)
    button = page.locator(".gth-busy-button")  # btn-outline-secondary
    # to_have_css retries: .btn transitions its color
    expect(button).to_have_css("color", "rgb(206, 212, 218)")  # #ced4da: 10.3:1 on dark
    page.click(".gth-theme-toggle")
    expect(button).to_have_css("color", "rgb(108, 117, 125)")  # Bootstrap's light value
