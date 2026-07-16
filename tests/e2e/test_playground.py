"""Playwright smoke tests against the real /playground app (docs/testing.md).

Skips cleanly (not fails) if playwright isn't installed — see conftest.py's
`pytest.importorskip`. No gth-modal test: it doesn't exist yet.
"""

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
