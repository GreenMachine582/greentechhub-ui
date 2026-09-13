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
