"""Playwright smoke tests against the real /playground app (docs/testing.md).

Skips cleanly (not fails) if playwright isn't installed — see conftest.py's
`pytest.importorskip`.
"""

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect

# Every playground page (the category pages the sidebar links to, plus the
# data-table / tree / standalone sidebar demos).
PAGES = ["/", "/layout", "/data", "/forms", "/feedback", "/overlays", "/navigation",
         "/extensibility", "/settings", "/tables", "/tree", "/layouts/sidebar"]

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


def test_theme_toggle_saves_to_the_server(page, playground_url):
    page.goto(playground_url)
    html = page.locator("html")
    assert html.get_attribute("data-bs-theme") == "dark"

    with page.expect_response(lambda r: r.url.endswith("/demo/theme")) as saved:
        page.click(".gth-theme-toggle")
    assert saved.value.status == 204

    # The server's theme_mode wins even with localStorage gone (another device, cleared storage).
    page.evaluate("localStorage.clear()")
    page.reload()
    assert html.get_attribute("data-bs-theme") == "light"
    assert page.evaluate("localStorage.getItem('gth-theme-mode')") == "light"


def test_system_theme_follows_the_os_live(page, playground_url):
    host = urlparse(playground_url).hostname
    page.context.add_cookies([{"name": "playground-theme", "value": "system", "domain": host,
                               "path": "/"}])
    page.emulate_media(color_scheme="light")
    page.goto(playground_url)
    html = page.locator("html")
    assert html.get_attribute("data-gth-theme-mode") == "system"
    assert html.get_attribute("data-bs-theme") == "light"

    page.emulate_media(color_scheme="dark")
    expect(html).to_have_attribute("data-bs-theme", "dark")

    # A click picks an explicit mode, which stops following the OS.
    page.click(".gth-theme-toggle")
    expect(html).to_have_attribute("data-bs-theme", "light")
    page.emulate_media(color_scheme="dark")
    expect(html).to_have_attribute("data-gth-theme-mode", "light")
    expect(html).to_have_attribute("data-bs-theme", "light")


def test_form_validation_and_success_toast(page, playground_url):
    page.goto(f"{playground_url}/forms")

    page.fill("#gth-field-budget", "-5")
    page.click("#form-demo-container button[type=submit]")
    page.wait_for_selector("#gth-field-budget.is-invalid")
    assert "greater than or equal to 0" in page.inner_text("#form-demo-container")
    expect(page.locator(DYNAMIC_TOAST)).to_have_count(0)  # 422 = inline errors, no error toast

    page.fill("#gth-field-budget", "250")
    page.click("#form-demo-container button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved budget")


def test_settings_section_validates_saves_and_submits_unchecked_switch(page, playground_url):
    _impersonate(page, playground_url, "admin")  # the App section needs settings.manage
    page.goto(f"{playground_url}/settings")
    prefs = "#gth-settings-preferences"
    page_size = "[id='gth-field-ui.page_size']"  # setting keys have dots, so no #id selector

    page.fill(page_size, "500")
    page.click(f"{prefs} button[type=submit]")
    page.wait_for_selector(f"{page_size}.is-invalid")
    assert "Must be between 5 and 200." in page.inner_text(prefs)
    expect(page.locator(DYNAMIC_TOAST)).to_have_count(0)

    page.fill(page_size, "50")
    page.click(f"{prefs} label:has-text('Dark')")
    page.click(f"{prefs} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Preferences saved")
    expect(page.locator(page_size)).to_have_value("50")

    # An unchecked switch still submits "false" (gth_switch off_value) and saves.
    app = "#gth-settings-app"
    expect(page.locator("[id='gth-field-site.maintenance']")).not_to_be_checked()
    page.click(f"{app} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("App saved")


def test_app_site_banner_shows_above_every_page(page, playground_url):
    _impersonate(page, playground_url, "admin")
    try:
        page.goto(f"{playground_url}/settings")
        app = "#gth-settings-app"
        page.fill("[id='gth-field-site.banner']", "Maintenance at 9pm: saving is paused.")
        page.select_option("[id='gth-field-site.banner_tone']", "bad")
        page.click(f"{app} button[type=submit]")
        expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("App saved")

        page.goto(f"{playground_url}/data")
        banner = page.locator("[data-gth-banner='site']")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Maintenance at 9pm")
        expect(banner).to_have_class(re.compile("alert-danger"))
        # Above the navbar, like any site banner.
        assert banner.bounding_box()["y"] < page.locator(".gth-navbar").bounding_box()["y"]
    finally:
        page.request.post(f"{playground_url}/demo/reset")
        page.evaluate("""() => Object.keys(localStorage)
            .filter(k => k.startsWith("gth-banner:")).forEach(k => localStorage.removeItem(k))""")


def test_secret_setting_is_write_only(page, playground_url):
    page.goto(f"{playground_url}/settings")
    prefs = "#gth-settings-preferences"
    token = page.locator("[id='gth-field-demo.api_token']")
    help_text = page.locator("[id='gth-field-demo.api_token-help']")
    remove = page.locator("[id='gth-field-demo.api_token.__clear']")
    expect(token).to_have_attribute("type", "password")
    expect(remove).to_have_count(0)

    token.fill("tok-s3cret")
    page.click(f"{prefs} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Preferences saved")
    expect(help_text).to_contain_text("Saved. Leave blank to keep it.")
    expect(token).to_have_value("")
    assert "tok-s3cret" not in page.content()

    # A blank field keeps it, across a reload too.
    page.reload()
    expect(help_text).to_contain_text("Saved.")
    page.click(f"{prefs} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Preferences saved")
    expect(help_text).to_contain_text("Saved.")

    # Remove clears it.
    remove.check()
    page.click(f"{prefs} button[type=submit]")
    expect(remove).to_have_count(0)
    expect(help_text).not_to_contain_text("Saved.")


def test_theme_saved_from_settings_applies_without_reload_and_persists(page, playground_url):
    page.goto(f"{playground_url}/settings")
    html = page.locator("html")
    prefs = "#gth-settings-preferences"
    assert html.get_attribute("data-bs-theme") == "dark"

    page.click(f"{prefs} label:has-text('Light')")
    page.click(f"{prefs} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Preferences saved")
    # applied by the gth:theme event in the save response, no reload
    expect(html).to_have_attribute("data-bs-theme", "light")
    assert page.evaluate("localStorage.getItem('gth-theme-mode')") == "light"

    # saved server-side: wins with localStorage gone, and the form shows it
    page.evaluate("localStorage.clear()")
    page.reload()
    assert html.get_attribute("data-bs-theme") == "light"
    expect(page.locator("[id='gth-field-ui.theme-1']")).to_be_checked()

    # the navbar toggle writes the same store, so the form follows it
    with page.expect_response(lambda r: r.url.endswith("/demo/theme")):
        page.click(".gth-theme-toggle")
    page.reload()
    expect(page.locator("[id='gth-field-ui.theme-2']")).to_be_checked()


def _impersonate(page, playground_url, persona):
    page.goto(f"{playground_url}/personas")
    page.locator(f"[data-persona={persona}] button[type=submit]").click()
    expect(page.locator(f"[data-persona={persona}] .badge")).to_have_text("Current")


def test_user_menu_and_permissioned_nav(page, playground_url):
    app_link = "#gth-sidebar a[href='/settings#gth-settings-app']"
    page.goto(f"{playground_url}/extensibility")
    expect(page.locator(".gth-user-menu")).to_have_count(0)
    expect(page.locator(app_link)).to_have_count(0)

    _impersonate(page, playground_url, "admin")
    expect(page.locator(app_link)).to_have_count(1)

    page.click(".gth-user-menu .dropdown-toggle")
    page.click(".gth-user-menu a:has-text('Settings')")
    expect(page).to_have_url(re.compile(r"/settings$"))

    page.click(".gth-user-menu .dropdown-toggle")
    page.click(".gth-user-menu button:has-text('Log out')")
    expect(page).to_have_url(re.compile(r"/personas$"))
    expect(page.locator("[data-persona=anonymous] .badge")).to_have_text("Current")
    expect(page.locator(".gth-user-menu")).to_have_count(0)


def test_gated_page_redirects_to_personas_and_back(page, playground_url):
    roles_link = "#gth-sidebar a[href='/roles']"
    page.goto(f"{playground_url}/roles")
    expect(page).to_have_url(re.compile(r"/personas\?next=%2Froles&need=settings.manage$"))
    expect(page.locator("#gth-persona-need")).to_contain_text("settings.manage")

    page.locator("[data-persona=admin] button[type=submit]").click()
    expect(page).to_have_url(re.compile(r"/roles$"))
    expect(page.locator("#gth-roles")).to_be_visible()

    page.click(".gth-user-menu .dropdown-toggle")
    page.click(".gth-user-menu a:has-text('Switch persona')")
    expect(page).to_have_url(re.compile(r"/personas$"))
    page.locator("[data-persona=viewer] button[type=submit]").click()
    expect(page.locator("[data-persona=viewer] .badge")).to_have_text("Current")
    expect(page.locator(roles_link)).to_have_count(0)

    # the viewer sees Preferences only, not the App section
    page.goto(f"{playground_url}/settings")
    expect(page.locator("#gth-settings-preferences")).to_be_visible()
    expect(page.locator("#gth-settings-app")).to_have_count(0)

    # from a gated page's banner, the viewer can't open /roles: they land on Personas, no banner
    page.goto(f"{playground_url}/roles")
    expect(page.locator("#gth-persona-need")).to_be_visible()
    expect(page.locator("[data-persona=viewer] .gth-persona-cant-open")).to_contain_text("/roles")
    page.locator("[data-persona=anonymous] button[type=submit]").click()
    expect(page).to_have_url(re.compile(r"/personas$"))
    expect(page.locator("#gth-persona-need")).to_have_count(0)


def test_roles_page_assign_change_remove(page, playground_url):
    _impersonate(page, playground_url, "admin")
    page.click("#gth-sidebar a[href='/roles']")
    expect(page).to_have_url(re.compile(r"/roles$"))
    roles = page.locator("#gth-roles")

    subject = f"e2e-{datetime.now():%H%M%S%f}"
    page.fill("[id='gth-field-subject']", subject)
    page.click("label[for='gth-roles-add-1']")  # Viewer
    page.click("label[for='gth-roles-add-2']")  # Editor
    page.click(".gth-roles-add button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text(f"Roles assigned to {subject}")
    row = roles.locator("tr", has_text=subject)
    expect(row).to_have_count(1)

    # set the row to Admin only
    row.locator("label", has_text="Viewer").click()
    row.locator("label", has_text="Editor").click()
    row.locator("label", has_text="Admin").click()
    row.locator("button", has_text="Save").click()
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text(f"Roles saved for {subject}")
    row = roles.locator("tr", has_text=subject)
    expect(row.locator("input[value=admin]")).to_be_checked()
    expect(row.locator("input[value=viewer]")).not_to_be_checked()

    row.locator("button", has_text="Remove").click()
    page.locator(".modal.show .gth-confirm-delete-button").click()
    expect(roles.locator("tr", has_text=subject)).to_have_count(0)
    expect(page.locator(".modal-backdrop")).to_have_count(0)
    expect(page.locator("body")).not_to_have_class(re.compile("modal-open"))


def test_density_and_motion_preferences(page, playground_url):
    def padding_top(selector):
        return page.eval_on_selector(selector, "el => parseFloat(getComputedStyle(el).paddingTop)")

    page.goto(f"{playground_url}/settings")
    html = page.locator("html")
    field = "[id='gth-field-ui.page_size']"
    comfortable = padding_top(field)

    prefs = "#gth-settings-preferences"
    page.click(f"{prefs} label:has-text('Compact')")
    page.click(f"{prefs} label:has-text('Reduce')")
    page.click(f"{prefs} button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Preferences saved")
    page.reload()
    expect(html).to_have_attribute("data-gth-density", "compact")
    expect(html).to_have_attribute("data-gth-motion", "reduce")
    assert padding_top(field) < comfortable
    # the sidebar's width transition (0.15s) is cut to ~0
    duration = page.eval_on_selector(
        "#gth-sidebar", "el => getComputedStyle(el).transitionDuration")
    assert all(float(d.rstrip("s")) < 0.001 for d in duration.split(", ")), duration

    # a data table with nothing stored starts compact; its own toggle still wins
    page.goto(f"{playground_url}/tables")
    table = page.locator("table.gth-table").first
    expect(table).to_have_class(re.compile(r"\btable-sm\b"))
    page.click("#records-view-toggle")
    page.click("input[name=records-density][value=comfortable]")
    expect(table).not_to_have_class(re.compile(r"\btable-sm\b"))
    page.reload()
    expect(page.locator("table.gth-table").first).not_to_have_class(re.compile(r"\btable-sm\b"))


def test_sidebar_default_until_this_browser_toggles(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})  # the rail is >=992px only
    html = page.locator("html")
    page.goto(f"{playground_url}/settings")
    page.click("#gth-settings-preferences label:has-text('Icons only')")
    page.click("#gth-settings-preferences button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Preferences saved")

    page.evaluate("localStorage.removeItem('gth-sidebar-mode')")
    page.reload()
    expect(html).to_have_attribute("data-gth-sidebar", "rail")

    # this browser's toggle wins from then on
    page.locator("[data-gth-sidebar-rail]").click()
    expect(html).not_to_have_attribute("data-gth-sidebar", "rail")
    page.reload()
    expect(html).not_to_have_attribute("data-gth-sidebar", "rail")


def _nav_state(page):
    return page.evaluate("""() => {
        const n = document.querySelector('.gth-sidebar-nav');
        const a = n.querySelector('a[aria-current="page"]');
        const r = a.getBoundingClientRect(), nr = n.getBoundingClientRect();
        return {scroll: n.scrollTop, href: a.getAttribute('href'),
                visible: r.top >= nr.top && r.bottom <= nr.bottom, pageY: window.scrollY};
    }""")


def test_sidebar_keeps_its_scroll_across_page_loads(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 500})
    page.goto(f"{playground_url}/navigation")
    page.evaluate("document.querySelectorAll('[data-gth-sidebar-group][aria-expanded=false]')"
                  ".forEach(b => b.click())")
    page.evaluate("document.querySelector('.gth-sidebar-nav').scrollTop = 99999")
    page.locator("#gth-sidebar a[href='/personas']").click()
    expect(page).to_have_url(re.compile(r"/personas$"))
    state = _nav_state(page)
    assert state["href"] == "/personas" and state["visible"], state
    assert state["scroll"] > 0 and state["pageY"] == 0, state


def test_sidebar_brings_the_current_page_into_view_on_a_fresh_tab(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 400})
    page.goto(f"{playground_url}/personas")  # no saved scroll in this tab
    state = _nav_state(page)
    assert state["visible"] and state["pageY"] == 0, state


def test_choice_buttons_show_hover(page, playground_url):
    def background(locator):
        return locator.evaluate("el => getComputedStyle(el).backgroundColor")

    page.goto(f"{playground_url}/tables")
    segmented = page.locator(".gth-segmented").first
    unchecked, checked = segmented.locator("label").nth(1), segmented.locator("label").nth(0)
    resting, checked_bg = background(unchecked), background(checked)
    unchecked.hover()
    expect(unchecked).not_to_have_css("background-color", resting)
    checked.hover()
    expect(checked).to_have_css("background-color", checked_bg)

    page.goto(f"{playground_url}/forms")
    chip = page.locator(".gth-chips .btn-check:not(:checked) + .gth-chip").first
    resting = background(chip)
    chip.hover()
    expect(chip).not_to_have_css("background-color", resting)


def test_segmented_track_style(page, playground_url):
    page.goto(f"{playground_url}/settings")
    field = page.locator("#gth-settings-preferences .gth-segmented").first  # Theme
    track = field.locator(".gth-segmented-track")
    checked = field.locator(".btn-check:checked + .gth-segmented-option")
    unchecked = field.locator(".btn-check:not(:checked) + .gth-segmented-option").first

    brand = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--gth-brand-fg').trim()")
    brand_rgb = page.evaluate(
        """c => { const el = document.createElement('span'); el.style.color = c;
                  document.body.append(el); const v = getComputedStyle(el).color; el.remove();
                  return v; }""", brand)
    expect(checked).to_have_css("color", brand_rgb)
    assert checked.evaluate("el => getComputedStyle(el).backgroundColor") != track.evaluate(
        "el => getComputedStyle(el).backgroundColor")

    resting = unchecked.evaluate("el => getComputedStyle(el).backgroundColor")
    unchecked.hover()
    expect(unchecked).not_to_have_css("background-color", resting)

    # sized to its content, not stretched across the form
    form_width = page.locator("#gth-settings-preferences form").evaluate("el => el.clientWidth")
    assert track.evaluate("el => el.getBoundingClientRect().width") < form_width

    # keyboard: native radios, so arrows move the selection; the focus ring shows
    checked_input = field.locator(".btn-check:checked")
    checked_input.focus()
    before = checked_input.get_attribute("value")
    page.keyboard.press("ArrowRight")
    focused = page.evaluate("document.activeElement.value")
    assert focused != before
    ring = page.evaluate("getComputedStyle(document.activeElement.nextElementSibling).boxShadow")
    assert ring != "none"


# ── v0.12: one brand accent (theme.css "Brand accent") ────────────────────

BOOTSTRAP_BLUES = ("rgb(13, 110, 253)", "rgb(134, 183, 254)", "rgb(10, 88, 202)",
                   "rgba(13, 110, 253", "rgb(110, 168, 254)")

# WCAG contrast of an element's text (or a chosen property) against its own
# background, walking up to the first opaque background.
CONTRAST_JS = """([el, fgProp]) => {
  const rgb = v => (v.match(/[\\d.]+/g) || []).map(Number);
  const lum = c => { const [r, g, b] = c.slice(0, 3).map(x => { x /= 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  let n = el, bg = null;
  while (n && n.nodeType === 1) { const c = rgb(getComputedStyle(n).backgroundColor);
    if (c.length >= 3 && (c.length < 4 || c[3] > 0.5)) { bg = c; break; } n = n.parentElement; }
  const fg = rgb(getComputedStyle(el)[fgProp]);
  const [a, b] = [lum(fg), lum(bg || [255, 255, 255])].sort((x, y) => y - x);
  return (a + 0.05) / (b + 0.05);
}"""


def _themed(page, playground_url, scheme, path):
    page.context.add_cookies([{"name": "playground-theme", "value": scheme,
                               "url": playground_url}])
    page.goto(f"{playground_url}{path}")


def _contrast(locator, prop="color"):
    return locator.evaluate(f"el => ({CONTRAST_JS})([el, '{prop}'])")


def test_brand_accent_fills_clear_contrast_in_both_themes(page, playground_url):
    for scheme in ("dark", "light"):
        _themed(page, playground_url, scheme, "/forms")
        button = page.locator(".btn-primary").first
        assert _contrast(button) >= 4.5, (scheme, "btn-primary")

        chip = page.locator(".gth-chips .gth-chip").first
        chip.click()
        assert _contrast(chip) >= 4.5, (scheme, "checked chip")

        _themed(page, playground_url, scheme, "/settings")
        thumb = page.locator(".btn-check:checked + .gth-segmented-option").first
        assert _contrast(thumb) >= 4.5, (scheme, "segmented thumb")


def test_no_bootstrap_blue_left_on_brand_states(page, playground_url):
    def colours(locator):
        return locator.evaluate(
            "el => { const s = getComputedStyle(el); return [s.color, s.backgroundColor,"
            " s.borderTopColor, s.boxShadow].join(' | '); }")

    for scheme in ("dark", "light"):
        _themed(page, playground_url, scheme, "/forms")
        checks = {"btn-primary": page.locator(".btn-primary").first,
                  "link": page.locator("main a[href]:not(.btn)").first}
        field = page.locator("main input.form-control").first
        field.focus()
        checks["focused field"] = field
        switch = page.locator(".form-switch .form-check-input").first
        if not switch.is_checked():
            switch.check(force=True)
        checks["checked switch"] = switch
        multiselect = page.locator(".gth-multiselect-input").first
        multiselect.focus()
        checks["focused multiselect"] = page.locator(".gth-multiselect-control").first
        for name, locator in checks.items():
            value = colours(locator)
            assert not any(b in value for b in BOOTSTRAP_BLUES), (scheme, name, value)

        _themed(page, playground_url, scheme, "/tables")
        active_page = page.locator(".pagination .page-item.active .page-link").first
        value = colours(active_page)
        assert not any(b in value for b in BOOTSTRAP_BLUES), (scheme, "pagination", value)
        accent = page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--gth-accent').trim()")
        accent_rgb = page.evaluate(
            """c => { const el = document.createElement('span'); el.style.color = c;
                      document.body.append(el); const v = getComputedStyle(el).color; el.remove();
                      return v; }""", accent)
        expect(active_page).to_have_css("background-color", accent_rgb)


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


def _open_server_modal(page, playground_url):
    page.goto(f"{playground_url}/overlays")
    page.click("text=Open server-rendered modal")
    expect(page.locator(MODAL)).to_be_visible()


def test_combobox_search_clear_restores_full_list(page, playground_url):
    _open_server_modal(page, playground_url)
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
    _open_server_modal(page, playground_url)
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
    _open_server_modal(page, playground_url)
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
    button = page.locator("#busy-button .gth-busy-button[type=button]")
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


def test_busy_submit_button_busy_while_form_request_runs(page, playground_url):
    page.goto(f"{playground_url}/forms")
    button = page.locator("#busy-submit-demo .gth-busy-button")
    for submit in (button.click, lambda: page.locator("#busy-report-name").press("Enter")):
        submit()
        # start_toast comes from the submitter, though the form sends the request.
        expect(page.locator(DYNAMIC_TOAST).first).to_contain_text("Report started")
        expect(button).to_be_disabled()  # the form's hx-disabled-elt
        expect(button.locator(".gth-busy-button-busy")).to_be_visible()
        expect(button.locator(".gth-busy-button-idle")).to_be_hidden()

        expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Slow job finished", timeout=10000)
        expect(button).to_be_enabled()
        expect(button.locator(".gth-busy-button-idle")).to_be_visible()
        # Clear the toasts, so the Enter round checks fresh ones.
        closes = page.locator(f"{DYNAMIC_TOAST} .btn-close")
        closes.evaluate_all("els => els.forEach(b => b.click())")
        expect(page.locator(DYNAMIC_TOAST)).to_have_count(0)


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
    page.evaluate("htmx.ajax('GET', '/demo/modal', {target: '#gth-modal-host'})")
    expect(page.locator("#gth-modal-host .modal")).to_have_count(1)
    expect(page.locator(MODAL)).to_be_visible()
    expect(page.locator(".modal-backdrop")).to_have_count(1)


def test_combobox_options_get_panel_scoped_ids(page, playground_url):
    _open_server_modal(page, playground_url)
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
    button = page.locator("#busy-button .gth-busy-button[type=button]")  # btn-outline-secondary
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


# ── gth-data-table bulk selection ────────────────────────────────────────

BULK_BAR = "#records [data-gth-bulk]"
BULK_COUNT = "#records .gth-table-bulk-count"
SELECT_ALL = "#records [data-gth-select-all]"


def _row_box(page, n):
    return page.locator(f"{RECORD_ROWS} [data-gth-select]").nth(n)


def test_bulk_selection_survives_paging_and_sort_but_not_filters(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    expect(page.locator(BULK_BAR)).to_be_hidden()
    _row_box(page, 0).check()
    _row_box(page, 2).check()
    expect(page.locator(BULK_COUNT)).to_have_text("2 selected")
    expect(page.locator(RECORD_ROWS).nth(0)).to_have_class(re.compile("table-active"))
    expect(page.locator(SELECT_ALL)).to_have_js_property("indeterminate", True)

    page.click("#records .gth-table-pager a[aria-label='Page 2']")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("11–20")
    expect(page.locator(BULK_COUNT)).to_have_text("2 selected (2 on other pages)")
    _htmx_idle(page)
    page.click("#records .gth-table-pager a[aria-label='Page 1']")
    expect(_row_box(page, 0)).to_be_checked()
    expect(_row_box(page, 2)).to_be_checked()
    expect(_row_box(page, 1)).not_to_be_checked()

    _htmx_idle(page)
    name_header = page.locator("#records th:has-text('Name')")
    name_header.locator("button").click()  # re-sorts, same filters
    expect(name_header).to_have_attribute("aria-sort", "descending")
    expect(page.locator(BULK_COUNT)).to_contain_text("2 selected")

    _htmx_idle(page)
    page.click(".gth-table-filter label:has-text('Cable')")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 30")
    expect(page.locator(BULK_BAR)).to_be_hidden()
    expect(page.locator(f"{RECORD_ROWS} [data-gth-select]:checked")).to_have_count(0)


def test_bulk_select_all_and_shift_click_range(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    page.locator(SELECT_ALL).check()
    expect(page.locator(BULK_COUNT)).to_have_text("10 selected")
    _row_box(page, 4).uncheck()
    expect(page.locator(SELECT_ALL)).to_have_js_property("indeterminate", True)
    page.get_by_role("button", name="Clear selection").click()
    expect(page.locator(BULK_BAR)).to_be_hidden()

    _row_box(page, 1).click()
    _row_box(page, 5).click(modifiers=["Shift"])
    expect(page.locator(BULK_COUNT)).to_have_text("5 selected")
    expect(page.locator(f"{RECORD_ROWS} [data-gth-select]:checked")).to_have_count(5)


def test_bulk_selection_kept_across_load_more(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=load_more")
    page.locator(SELECT_ALL).check()
    expect(page.locator(BULK_COUNT)).to_have_text("10 selected")
    _htmx_idle(page)
    page.click("#records .gth-table-load-more button")
    expect(page.locator(RECORD_ROWS)).to_have_count(20)
    expect(page.locator(f"{RECORD_ROWS} [data-gth-select]:checked")).to_have_count(10)
    expect(_row_box(page, 15)).not_to_be_checked()
    expect(page.locator(SELECT_ALL)).to_have_js_property("indeterminate", True)
    expect(page.locator(BULK_COUNT)).to_have_text("10 selected")


def test_bulk_action_posts_every_selected_id_then_clears(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    first_stock = int(page.locator(RECORD_ROWS).nth(0).locator("td.text-end").first.inner_text())
    posted = []
    page.on("request", lambda r: posted.append(r.post_data)
            if r.url.endswith("/demo/records/restock") else None)
    try:
        _row_box(page, 0).check()
        page.click("#records .gth-table-pager a[aria-label='Page 2']")
        expect(page.locator(BULK_COUNT)).to_contain_text("on other pages")
        _htmx_idle(page)
        _row_box(page, 0).check()
        page.get_by_role("button", name="Restock +50", exact=True).click()
        expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Restocked 2 records.")
        expect(page.locator(BULK_BAR)).to_be_hidden()
        assert len(posted) == 1 and posted[0].count("ids=") == 2
        # refresh_event re-queries page 1, where the first row was restocked.
        expect(page.locator("#records .gth-table-summary")).to_contain_text("1–10")
        stock = page.locator(RECORD_ROWS).nth(0).locator("td.text-end").first
        expect(stock).to_have_text(str(first_stock + 50))
        expect(_row_box(page, 0)).not_to_be_checked()

        page.on("dialog", lambda d: d.accept())  # "Mark sold out" confirms first
        _row_box(page, 0).check()
        page.get_by_role("button", name="Mark sold out", exact=True).click()
        expect(stock).to_have_text("0")
    finally:
        page.request.post(f"{playground_url}/demo/reset")


def test_bulk_selection_by_keyboard(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    _row_box(page, 0).focus()
    page.keyboard.press("Space")
    expect(page.locator(BULK_COUNT)).to_have_text("1 selected")
    # Tab passes the row's actions (the Restock button, then "⋯") on its way.
    for _ in range(3):
        page.keyboard.press("Tab")
    expect(_row_box(page, 1)).to_be_focused()
    page.keyboard.press("Space")
    expect(page.locator(BULK_COUNT)).to_have_text("2 selected")
    expect(page.locator("#records-bulk-status")).to_have_text("2 selected")
    page.keyboard.press("Escape")
    expect(page.locator(BULK_BAR)).to_be_hidden()
    expect(page.locator("#records-bulk-status")).to_have_text("Selection cleared")


# ── gth-data-table view options ──────────────────────────────────────────

VIEW_TOGGLE = "#records-view-toggle"


def _col_toggle(page, key):
    return page.locator(f"#records [data-gth-col-toggle='{key}']")


def _header(page, key):
    return page.locator(f"#records thead th[data-gth-col='{key}']")


def _clear_views(page):
    page.evaluate("""() => Object.keys(localStorage)
        .filter(k => k.startsWith("gth-table-view:")).forEach(k => localStorage.removeItem(k))""")


def test_view_columns_hide_and_persist(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    try:
        # ID starts hidden (header and cells); Name is pinned.
        expect(_header(page, "id")).to_be_hidden()
        expect(page.locator(f"{RECORD_ROWS} >> nth=0 >> td >> nth=1")).to_be_hidden()
        page.click(VIEW_TOGGLE)
        expect(_col_toggle(page, "id")).not_to_be_checked()
        expect(_col_toggle(page, "name")).to_be_disabled()

        _col_toggle(page, "category").uncheck()
        expect(_header(page, "category")).to_be_hidden()
        expect(page.locator(f"{RECORD_ROWS} >> nth=0 >> td >> nth=3")).to_be_hidden()
        _col_toggle(page, "id").check()
        expect(_header(page, "id")).to_be_visible()
        page.keyboard.press("Escape")

        # A sort swap and a page change keep the view; so does a reload.
        _header(page, "price").locator("button").click()
        expect(_header(page, "price")).to_have_attribute("aria-sort", "ascending")
        expect(_header(page, "category")).to_be_hidden()
        _htmx_idle(page)
        page.click("#records .gth-table-pager a[aria-label='Page 2']")
        expect(page.locator("#records .gth-table-summary")).to_contain_text("11–20")
        expect(page.locator(f"{RECORD_ROWS} >> nth=0 >> td >> nth=3")).to_be_hidden()
        page.reload()
        expect(_header(page, "category")).to_be_hidden()
        expect(_header(page, "id")).to_be_visible()

        # Reset brings the defaults back.
        page.click(VIEW_TOGGLE)
        page.get_by_role("button", name="Reset view").click()
        expect(_header(page, "category")).to_be_visible()
        expect(_header(page, "id")).to_be_hidden()
    finally:
        _clear_views(page)


def test_view_keeps_one_column_and_covers_appended_rows(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=load_more")
    try:
        page.click(VIEW_TOGGLE)
        for key in ("category", "stock", "price", "added"):
            _col_toggle(page, key).uncheck()
        # Name is pinned, so every hideable column can go; the table keeps Name.
        expect(_header(page, "name")).to_be_visible()
        page.keyboard.press("Escape")
        _htmx_idle(page)
        page.click("#records .gth-table-load-more button")
        expect(page.locator(RECORD_ROWS)).to_have_count(20)
        expect(page.locator(f"{RECORD_ROWS} >> nth=15 >> td >> nth=3")).to_be_hidden()  # Category
        expect(page.locator(f"{RECORD_ROWS} >> nth=15 >> td >> nth=0")).to_be_visible()  # checkbox
        # The row actions column is never listed in the menu or hidden.
        expect(page.locator("#records [data-gth-col-toggle]")).to_have_count(6)
        expect(page.locator(f"{RECORD_ROWS} >> nth=0 >> td.gth-table-actions")).to_be_visible()
        expect(page.locator(f"{RECORD_ROWS} >> nth=15 >> td.gth-table-actions")).to_be_visible()
    finally:
        _clear_views(page)


def test_row_actions_post_their_row(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    row = page.locator(RECORD_ROWS).nth(0)
    name = row.locator("td").nth(2).inner_text()
    stock = row.locator("td.text-end").first
    first_stock = int(stock.inner_text())
    try:
        # inline=1: Restock is an icon button, the rest sit in the "⋯" menu.
        row.get_by_role("button", name=f"Restock +50 {name}").click()
        expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Restocked 1 record.")
        expect(stock).to_have_text(str(first_stock + 50))  # refresh_event re-queried the table

        page.on("dialog", lambda d: d.accept())
        row.get_by_role("button", name=f"Actions for {name}").click()
        row.get_by_role("button", name="Mark sold out").click()
        expect(stock).to_have_text("0")
        expect(page.locator(BULK_BAR)).to_be_hidden()  # row actions don't touch the selection
    finally:
        page.request.post(f"{playground_url}/demo/reset")


def test_picker_mode_has_no_row_actions(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages&pick_for=demo")
    expect(page.locator(RECORD_ROWS).first).to_be_visible()
    expect(page.locator("#records .gth-table-actions")).to_have_count(0)


def test_view_density_compact_persists(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    try:
        table = page.locator("#records table")
        expect(table).not_to_have_class(re.compile("table-sm"))
        page.click(VIEW_TOGGLE)
        page.get_by_label("Compact").check()
        expect(table).to_have_class(re.compile("table-sm"))
        page.reload()
        expect(page.locator("#records table")).to_have_class(re.compile("gth-table-compact"))
    finally:
        _clear_views(page)


def test_view_menu_by_keyboard(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    try:
        page.locator(VIEW_TOGGLE).focus()
        page.keyboard.press("Enter")
        expect(page.locator(VIEW_TOGGLE)).to_have_attribute("aria-expanded", "true")
        page.keyboard.press("Tab")  # into the menu: the first column's checkbox
        expect(_col_toggle(page, "id")).to_be_focused()
        page.keyboard.press("Space")
        expect(_header(page, "id")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator(VIEW_TOGGLE)).to_have_attribute("aria-expanded", "false")
    finally:
        _clear_views(page)


# ── TableState.export_url ─────────────────────────────────────────────────

def test_export_link_follows_filters_and_sort_and_downloads(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    export = page.locator("#records .gth-table-export")
    expect(export).to_have_attribute("href", "/tables/export.csv")
    page.click(".gth-table-filter label:has-text('Board')")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 30")
    _htmx_idle(page)
    price = page.locator("#records th:has-text('Price')")
    price.locator("button").click()
    expect(price).to_have_attribute("aria-sort", "ascending")
    expect(export).to_have_attribute(
        "href", "/tables/export.csv?category=Board&sort=price&dir=asc")

    with page.expect_download() as info:
        export.click()
    download = info.value
    assert download.suggested_filename == "records.csv"
    lines = Path(download.path()).read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == "ID,Name,Category,Stock,Price,Added"
    assert len(lines) == 31 and all(",Board," in line for line in lines[1:])


# ── gth-badge / gth-tabs / gth-chips / gth-switch ─────────────────────────


def test_tabs_lazy_load_once_and_keyboard(page, playground_url):
    page.goto(f"{playground_url}/layout")
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/demo/tab/" in r.url else None)
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


# ── gth-form-field extras ────────────────────────────────────────────────

NOTES = "#gth-field-notes"
NOTES_COUNTER = "#gth-field-notes-counter"
COUNTER_STATUS = "#gth-char-counter-status"


def test_form_field_counter_tracks_typing_and_announces_thresholds(page, playground_url):
    page.goto(f"{playground_url}/forms")
    counter = page.locator(NOTES_COUNTER)
    expect(counter).to_have_text("0 / 140")
    page.fill(NOTES, "Hello")
    expect(counter).to_have_text("5 / 140")
    expect(counter).not_to_have_class(re.compile("is-near"))

    page.fill(NOTES, "x" * 125)
    page.locator(NOTES).press("End")
    page.keyboard.type("y")  # 126 = 90% of 140
    expect(counter).to_have_text("126 / 140")
    expect(counter).to_have_class(re.compile("is-near"))
    expect(page.locator(COUNTER_STATUS)).to_have_text("14 characters left")

    page.keyboard.type("z" * 20)  # the browser stops at maxlength
    expect(counter).to_have_text("140 / 140")
    expect(counter).to_have_class(re.compile("is-full"))
    assert len(page.locator(NOTES).input_value()) == 140
    expect(page.locator(COUNTER_STATUS)).to_have_text("Character limit reached")

    # The server re-renders the value and the count (counter set before JS runs).
    page.click("#form-demo-container button[type=submit]")
    expect(page.locator(DYNAMIC_TOAST)).to_contain_text("Saved budget")
    expect(page.locator(NOTES_COUNTER)).to_have_text("140 / 140")


def test_form_field_affixes_wrap_the_input_and_errors_sit_below(page, playground_url):
    page.goto(f"{playground_url}/forms")
    group = page.locator("#form-demo-container .input-group").first
    expect(group.locator(".input-group-text").first).to_have_text("$")
    expect(group.locator(".input-group-text").last).to_have_text("AUD")
    described = page.locator("#gth-field-budget").get_attribute("aria-describedby")
    assert "gth-field-budget-prefix" in described and "gth-field-budget-suffix" in described
    page.fill("#gth-field-budget", "-5")
    page.click("#form-demo-container button[type=submit]")
    expect(page.locator("#gth-field-budget")).to_have_class(re.compile("is-invalid"))
    expect(page.locator("#gth-field-budget-error")).to_be_visible()
    expect(page.locator("#form-demo-container .input-group.has-validation")).to_have_count(1)


def test_form_field_counter_handles_any_field_name(page, playground_url):
    # A name with a quote makes an id that's an invalid CSS selector unless escaped.
    page.goto(f"{playground_url}/forms")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.evaluate("""() => {
        const form = document.getElementById("form-demo-container");
        form.insertAdjacentHTML("beforeend",
            '<input id=\\'gth-field-a"b\\' maxlength="5">' +
            '<div id="odd-counter" data-gth-counter-for=\\'gth-field-a"b\\'>0 / 5</div>');
    }""")
    page.locator("[maxlength='5']").type("hi")
    expect(page.locator("#odd-counter")).to_have_text("2 / 5")
    assert errors == []


# ── no script errors anywhere ─────────────────────────────────────────────

def test_no_console_errors_on_any_page(page, playground_url):
    """Every gth-ui script loads on every page (shell_globals), so each must
    run cleanly where its component is absent. Missing-resource noise (e.g.
    DevTools fetching vendored .map files) isn't a script error."""
    errors = []
    page.on("pageerror", lambda e: errors.append(f"{page.url}: {e}"))
    page.on("console", lambda m: errors.append(f"{page.url}: {m.text}")
            if m.type == "error" and "Failed to load resource" not in m.text else None)
    for path in [*PAGES, "/tables?mode=load_more", "/tables?mode=infinite&scroll=1"]:
        page.goto(f"{playground_url}{path}")
        _htmx_idle(page)
    # Swaps re-run every script's htmx:load hook.
    page.goto(f"{playground_url}/tables?mode=pages")
    page.click(".gth-table-filter label:has-text('Cable')")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 30")
    _htmx_idle(page)
    page.click("#records .gth-table-pager a[aria-label='Page 2']")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("11–20")
    assert errors == []


# ── gth-date-range ────────────────────────────────────────────────────────

DR = "#date-range-demo"


def test_date_range_presets_fill_inputs_and_fire_one_change(page, playground_url):
    page.clock.set_fixed_time(datetime(2026, 3, 15, 10))
    posts = []
    page.on("request", lambda r: posts.append(r) if r.url.endswith("/demo/date-range") else None)
    page.goto(f"{playground_url}/forms")
    result = page.locator("#date-range-demo-result")
    month = page.locator(f"{DR} [data-preset=month]")
    expect(month).to_be_visible()  # rendered hidden, shown by date-range.js

    month.click()
    expect(result).to_have_text("date_from=2026-03-01, date_to=2026-03-31")
    expect(month).to_have_attribute("aria-pressed", "true")
    expect(month.locator(".gth-chip-check")).to_be_visible()
    assert len(posts) == 1

    page.click(f"{DR} [data-preset=fy]")
    expect(result).to_have_text("date_from=2025-07-01, date_to=2026-06-30")
    expect(month).to_have_attribute("aria-pressed", "false")
    page.click(f"{DR} [data-preset=last_fy]")
    expect(result).to_have_text("date_from=2024-07-01, date_to=2025-06-30")
    page.click(f"{DR} [data-preset=today]")
    expect(result).to_have_text("date_from=2026-03-15, date_to=2026-03-15")
    assert len(posts) == 4

    # Editing a date by hand clears the pressed chip.
    page.fill("#gth-field-date_from", "2026-03-01")
    expect(page.locator(f"{DR} [data-preset=today]")).to_have_attribute("aria-pressed", "false")


def test_date_range_filters_the_data_table(page, playground_url):
    page.clock.set_fixed_time(datetime(2026, 3, 15, 10))
    page.goto(f"{playground_url}/tables?mode=pages&page=3")
    page.click(".gth-table-filter [data-preset=fy]")
    summary = page.locator("#records .gth-table-summary")
    expect(summary).to_contain_text("1–10 of 73")
    assert "date_from=2025-07-01" in page.url and "date_to=2026-06-30" in page.url
    # The filter bar isn't swapped, so the chip stays pressed.
    fy_chip = page.locator(".gth-table-filter [data-preset=fy]")
    expect(fy_chip).to_have_attribute("aria-pressed", "true")


def test_filter_bar_select_with_hidden_label(page, playground_url):
    # No record starts sold out: mark two, then filter for them.
    page.request.post(f"{playground_url}/demo/records/sold-out", form={"ids": "1"})
    page.request.post(f"{playground_url}/demo/records/sold-out", form={"ids": "2"})
    try:
        page.goto(f"{playground_url}/tables?mode=pages")
        select = page.locator(".gth-table-filter").get_by_label("Stock", exact=True)
        expect(select).to_be_visible()  # the hidden label still names it
        expect(page.locator(".gth-table-filter label[for='gth-field-stock']")).to_have_class(
            re.compile("visually-hidden"))
        summary = page.locator("#records .gth-table-summary")
        select.select_option("out")
        expect(summary).to_contain_text("1–2 of 2")
        assert "stock=out" in page.url
        stocks = page.locator(f"{RECORD_ROWS} td:nth-child(5)")  # select, ID, Name, Category, Stock
        expect(stocks).to_have_text(["0", "0"])
        select.select_option("")  # "Any stock"
        expect(summary).to_contain_text("of 120")
    finally:
        page.request.post(f"{playground_url}/demo/reset")


# ── gth-file-drop ─────────────────────────────────────────────────────────

FD = "#upload-demo [data-gth-file-drop]"
FD_INPUT = "#gth-field-files"
CSV = {"name": "a.csv", "mimeType": "text/csv", "buffer": b"x,y\n1,2\n"}


def _picked(page):
    return page.eval_on_selector(FD_INPUT, "el => [...el.files].map(f => f.name)")


def test_file_drop_lists_picks_and_rejects_bad_files(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.set_input_files(FD_INPUT, [CSV])
    files = page.locator(f"{FD} .gth-file-drop-file")
    expect(files).to_have_count(1)
    expect(files.first).to_contain_text("a.csv")
    expect(files.first.locator(".gth-file-drop-size")).to_have_text("8 B")

    page.set_input_files(FD_INPUT, [
        {"name": "notes.txt", "mimeType": "text/plain", "buffer": b"hi"},
        {"name": "big.csv", "mimeType": "text/csv", "buffer": b"x" * (1024 * 1024 + 1)},
        CSV,
    ])
    errors = page.locator(f"{FD} .gth-file-drop-errors li")
    expect(errors).to_have_text(["notes.txt — not an accepted file type",
                                 "big.csv — larger than 1 MB"])
    expect(files).to_have_count(1)
    assert _picked(page) == ["a.csv"]
    expect(page.locator(FD_INPUT)).to_have_attribute("aria-invalid", "true")

    page.set_input_files(FD_INPUT, [CSV])  # a clean pick clears the errors
    expect(errors).to_have_count(0)
    expect(page.locator(FD_INPUT)).not_to_have_attribute("aria-invalid", "true")


def test_file_drop_accepts_a_drop(page, playground_url):
    page.goto(f"{playground_url}/forms")
    zone = page.locator(f"{FD} .gth-file-drop-zone")
    zone.evaluate("""zone => {
        const dt = new DataTransfer();
        dt.items.add(new File(["a,b"], "dropped.csv", {type: "text/csv"}));
        const init = {dataTransfer: dt, bubbles: true, cancelable: true};
        zone.dispatchEvent(new DragEvent("dragover", init));
        window.__gthDragover = zone.classList.contains("is-dragover");
        zone.dispatchEvent(new DragEvent("drop", init));
    }""")
    assert page.evaluate("window.__gthDragover") is True
    expect(zone).not_to_have_class(re.compile("is-dragover"))
    assert _picked(page) == ["dropped.csv"]
    expect(page.locator(f"{FD} .gth-file-drop-file")).to_contain_text("dropped.csv")


def test_file_drop_uploads_with_progress_then_result(page, playground_url):
    page.goto(f"{playground_url}/forms")
    # Nothing chosen: the server's 422 is swapped in.
    page.click("#upload-demo button[type=submit]")
    expect(page.locator(f"{FD} .gth-file-drop-errors li")).to_have_text("Choose at least one file.")

    page.set_input_files(FD_INPUT, [CSV])
    page.click("#upload-demo button[type=submit]")
    progress = page.locator(f"{FD} .gth-file-drop-progress")
    expect(progress).to_be_visible()  # the demo server waits ~1s
    expect(page.locator("#upload-demo-result")).to_have_text("Uploaded: a.csv (8 B)")
    expect(page.locator(f"{FD} .gth-file-drop-progress")).to_be_hidden()


def _xhr(loaded, total):
    return {"lengthComputable": True, "loaded": loaded, "total": total}


def test_file_drop_progress_bar_follows_xhr_progress(page, playground_url):
    # Localhost uploads finish before a real progress event can be watched, so
    # drive the bar with the events htmx would fire.
    page.goto(f"{playground_url}/forms")
    page.set_input_files(FD_INPUT, [CSV])
    fire = """([name, detail]) => {
        const form = document.getElementById("upload-demo");
        form.dispatchEvent(new CustomEvent(name, {bubbles: true, detail: {elt: form, ...detail}}));
    }"""
    progress = page.locator(f"{FD} .gth-file-drop-progress")
    page.evaluate(fire, ["htmx:beforeRequest", {}])
    expect(progress).to_be_visible()
    expect(progress).to_have_attribute("aria-valuenow", "0")
    page.evaluate(fire, ["htmx:xhr:progress", _xhr(50, 100)])
    expect(progress).to_have_attribute("aria-valuenow", "50")
    assert progress.locator(".progress-bar").evaluate("el => el.style.width") == "50%"
    page.evaluate(fire, ["htmx:xhr:progress", _xhr(100, 100)])
    expect(progress).to_have_attribute("aria-valuetext", "Processing…")
    expect(progress.locator(".progress-bar")).to_have_text("Processing…")
    # The response download's own progress events don't move the bar back.
    page.evaluate(fire, ["htmx:xhr:progress", _xhr(10, 900)])
    expect(progress).to_have_attribute("aria-valuetext", "Processing…")
    page.evaluate(fire, ["htmx:afterRequest", {}])
    expect(progress).to_be_hidden()


def test_file_drop_input_is_keyboard_reachable(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.locator(FD_INPUT).focus()
    zone = page.locator(f"{FD} .gth-file-drop-zone")
    shadow = zone.evaluate("el => getComputedStyle(el).boxShadow")
    assert shadow != "none"  # the hidden input's focus ring is drawn on the zone


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
    _open_server_modal(page, playground_url)
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
    page.evaluate("""() => htmx.ajax('GET', '/demo/record-picker?for=page&page=2',
                                      {target: '#picker-page', swap: 'outerHTML'})""")
    expect(panel.locator(".gth-table-summary")).to_contain_text("11–20 of 120")
    page.mouse.up()
    expect(page.locator(PART_TRIGGER)).to_have_text(label)  # the pressed row, not page 2's
    expect(panel).to_be_hidden()


def test_record_picker_full_page_picks_from_the_list_tab(page, playground_url):
    page.goto(f"{playground_url}/forms")
    page.click(PART_TRIGGER)
    panel = page.locator(PART_PANEL)
    full = panel.locator("[data-gth-record-picker-full]")
    expect(full).to_have_attribute("href", re.compile(r"^/tables\?pick_for=[\w-]+$"))

    with page.context.expect_page() as new_tab:
        full.click()
    expect(panel).to_be_hidden()
    tab = new_tab.value
    tab.wait_for_load_state()
    expect(tab).to_have_url(re.compile(r"/tables\?pick_for="))
    expect(tab.locator("[data-gth-pick-banner]")).to_contain_text("Choose a record for Part")

    # The table's own swaps keep pick_for, so its rows keep their buttons.
    _htmx_idle(tab)
    tab.get_by_role("link", name="Page 2", exact=True).click()
    expect(tab.locator(".gth-table-summary")).to_contain_text("11–20 of 120")
    use = tab.locator("[data-gth-pick-return]")
    expect(use).to_have_count(10)
    label = use.first.get_attribute("data-label")
    value = use.first.get_attribute("data-value")

    with tab.expect_event("close", timeout=5000):
        use.first.click()
    expect(page.locator(PART_TRIGGER)).to_have_text(label)
    expect(page.locator("#record-demo input[name=part]")).to_have_value(value)
    expect(page.locator("#record-demo-result")).to_have_text(f"part={value} ({label})")


def test_record_pick_without_a_form_tab_says_so(page, playground_url):
    page.goto(f"{playground_url}/tables?pick_for=nobody")
    page.locator("[data-gth-pick-return]").first.click()
    expect(page.locator("[data-gth-pick-status]")).to_have_text(
        "Couldn't find the form. Is its tab still open?")


def test_tables_without_pick_for_has_no_pick_buttons(page, playground_url):
    page.goto(f"{playground_url}/tables")
    expect(page.locator("[data-gth-pick-banner]")).to_have_count(0)
    expect(page.locator("[data-gth-pick-return]")).to_have_count(0)


def test_record_picker_escape_before_panel_loads_keeps_modal(page, playground_url):
    _open_server_modal(page, playground_url)
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
    _open_server_modal(page, playground_url)
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
    # Every navigable demo-nav entry, the "Back to playground" link included.
    expect(dialog.locator("[data-gth-command-pages] [data-gth-command-option]")).to_have_count(10)

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
    # Other tests delete from the shared demo list: reset it (list + badge refresh).
    page.click("#demo-reset")
    expect(items).to_have_count(3)
    expect(badge).to_have_text("3")
    count = 3
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


def test_login_page_is_a_branded_auth_screen(page, playground_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{playground_url}/login-demo")
    expect(page.locator(".gth-navbar")).to_have_count(0)  # layout="auth": no app chrome
    expect(page.locator(".gth-auth-service")).to_have_text("Playground")
    expect(page.locator("#gth-field-user_id")).to_be_focused()
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    # The colour mode can change before signing in.
    html = page.locator("html")
    expect(html).to_have_attribute("data-bs-theme", "dark")
    page.click(".gth-auth-corner .gth-theme-toggle")
    expect(html).to_have_attribute("data-bs-theme", "light")
    page.click(".gth-auth-corner .gth-theme-toggle")  # back, for the tests after this one
    # A failed sign-in keeps the user ID and moves focus to the password.
    page.fill("#gth-field-user_id", "bob")
    page.fill("#gth-field-password", "nope")
    page.click("form[action='/login-demo'] button[type=submit]")
    expect(page.locator(".gth-auth-card .gth-toast-danger")).to_contain_text("Incorrect user ID")
    expect(page.locator("#gth-field-user_id")).to_have_value("bob")
    expect(page.locator("#gth-field-password")).to_be_focused()


def test_register_page_is_a_branded_auth_screen(page, playground_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{playground_url}/login-demo")
    page.click(".gth-auth-switch a")  # "No account? Create one"
    expect(page).to_have_url(f"{playground_url}/register-demo")
    expect(page.locator(".gth-navbar")).to_have_count(0)
    expect(page.locator("#gth-field-user_id")).to_be_focused()
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    # A mismatched confirmation comes back with the error, the user ID kept.
    page.fill("#gth-field-user_id", "newcomer")
    page.fill("#gth-field-password", "long-enough")
    page.fill("#gth-field-password_confirm", "long-enougH")
    page.click("form[action='/register-demo'] button[type=submit]")
    expect(page.locator("#gth-field-password_confirm-error")).to_contain_text("don't match")
    expect(page.locator("#gth-field-user_id")).to_have_value("newcomer")
    expect(page.locator("#gth-field-password")).to_be_focused()
    # Fixed, it signs in and lands on the playground.
    page.fill("#gth-field-password", "long-enough")
    page.fill("#gth-field-password_confirm", "long-enough")
    page.click("form[action='/register-demo'] button[type=submit]")
    expect(page).to_have_url(f"{playground_url}/")


def test_inline_alert_is_page_content_not_a_toast(page, playground_url):
    page.goto(f"{playground_url}/feedback#inline-alert")
    alerts = page.locator("#alerts-demo .gth-toast-inline")
    expect(alerts).to_have_count(6)
    first = alerts.first
    expect(first).to_be_visible()
    # Its container's width (a toast is a 24rem card) and no shadow or close button.
    width = first.evaluate("el => el.getBoundingClientRect().width")
    container = page.locator("#alerts-demo").evaluate("el => el.getBoundingClientRect().width")
    assert abs(width - container) < 1 and width > 24 * 16
    expect(first).to_have_css("box-shadow", "none")
    expect(page.locator("#alerts-demo .btn-close")).to_have_count(0)
    # The surface variant keeps the toast's kind accent bar.
    expect(first).to_have_css("border-left-width", "4px")


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


def test_sidebar_demo_links_back_to_the_playground(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/layouts/sidebar/parts")
    page.locator(f"{SB} a:has-text('Back to playground')").click()
    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.locator("main h1")).to_have_text("greentechhub-ui playground")


def test_logo_is_48px_and_the_sidebar_docks_under_the_navbar(page, playground_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{playground_url}/forms")
    logo = page.locator(".gth-navbar-brand img:visible").first
    assert logo.bounding_box()["height"] == 48
    page.evaluate("window.scrollTo(0, 2000)")
    page.wait_for_timeout(100)
    nav_bottom = page.locator("nav.gth-navbar").evaluate("e => e.getBoundingClientRect().bottom")
    sidebar_top = page.locator("#gth-sidebar").evaluate("e => e.getBoundingClientRect().top")
    assert abs(sidebar_top - nav_bottom) <= 1

    page.goto(f"{playground_url}/layouts/sidebar")  # the logo in the other demo too
    assert page.locator(".gth-navbar-brand img:visible").first.bounding_box()["height"] == 48


def _error_button(page, label):
    page.locator("#error-toasts").get_by_role("button", name=label, exact=True).click()
    return page.locator(DYNAMIC_TOAST).last


def test_failed_requests_toast_with_status_or_server_detail(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    toast = _error_button(page, "404 with detail")
    expect(toast.locator(".gth-toast-title")).to_have_text("Not found")
    # the JSON detail
    expect(toast.locator(".gth-toast-message")).to_have_text("Widget #42 not found")
    expect(toast).to_have_class(re.compile("gth-toast-danger"))

    toast = _error_button(page, "403")
    expect(toast.locator(".gth-toast-title")).to_have_text("Not allowed")
    expect(toast).to_have_class(re.compile("gth-toast-warning"))

    toast = _error_button(page, "500")
    expect(toast.locator(".gth-toast-title")).to_have_text("Server error")
    expect(toast.locator(".gth-toast-message")).to_have_text(
        "Something went wrong on the server (500).")


def test_failed_request_toasts_are_deduped_and_stand_down(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    server_error = page.locator(f"{DYNAMIC_TOAST}:has-text('Server error')")

    _error_button(page, "500")
    expect(server_error).to_have_count(1)
    _error_button(page, "500")  # same failure again within a few seconds: no second toast
    page.wait_for_timeout(500)
    expect(server_error).to_have_count(1)

    # A response with its own toast gets only that one.
    _error_button(page, "500 with its own toast")
    expect(page.locator(f"{DYNAMIC_TOAST}:has-text('Reports unavailable')")).to_have_count(1)
    expect(server_error).to_have_count(1)

    # Opted out: nothing at all.
    before = page.locator(DYNAMIC_TOAST).count()
    with page.expect_response(re.compile("/demo/error/500$")):
        _error_button(page, "500, opted out")
    page.wait_for_timeout(300)
    expect(page.locator(DYNAMIC_TOAST)).to_have_count(before)


def test_network_failure_toasts(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    page.route(re.compile("/demo/error/403$"), lambda route: route.abort())
    toast = _error_button(page, "403")
    expect(toast.locator(".gth-toast-title")).to_have_text("Can't reach the server")


def test_data_table_refresh_event_keeps_sort_and_filters(page, playground_url):
    page.goto(f"{playground_url}/tables?mode=pages")
    stock_header = page.locator("#records th:has-text('Stock')")
    page.click(".gth-table-filter label:has-text('Sensor')")
    expect(page.locator("#records .gth-table-summary")).to_contain_text("of 30")
    _htmx_idle(page)
    stock_header.locator("button").click()
    expect(stock_header).to_have_attribute("aria-sort", "ascending")
    _htmx_idle(page)
    page.locator("#records .gth-table-pager a[aria-label='Page 2']").click()
    expect(page.locator("#records .gth-table-summary")).to_contain_text("11–20 of 30")
    _htmx_idle(page)

    try:
        page.get_by_role("button", name="Add record").click()
        # Re-queried from page 1 with the same filter + sort: the new stock-1 sensor leads.
        expect(page.locator("#records .gth-table-summary")).to_contain_text("1–10 of 31")
        expect(page.locator(RECORD_ROWS).first).to_contain_text("Added sensor 1")
        expect(stock_header).to_have_attribute("aria-sort", "ascending")
    finally:
        page.request.post(f"{playground_url}/demo/reset")


def test_action_menu_row_actions(page, playground_url):
    page.goto(f"{playground_url}/data#action-menu")
    section = page.locator("#action-menu")
    toggles = section.locator(".gth-action-menu-toggle")
    expect(toggles).to_have_count(8)
    expect(section.locator(".gth-action-menu-button")).to_have_count(0)

    # The last row's menu opens in full although its box scrolls (fixed strategy).
    last = toggles.last
    last.scroll_into_view_if_needed()
    last.click()
    menu = section.locator(".dropdown-menu.show")
    expect(menu).to_be_visible()
    box = menu.bounding_box()
    hit = page.evaluate(
        "([x, y]) => !!document.elementFromPoint(x, y)?.closest('.dropdown-menu.show')",
        [box["x"] + box["width"] / 2, box["y"] + box["height"] - 4])
    assert hit, "the menu's bottom edge is clipped"

    # Keyboard: Esc closes and returns focus; Enter reopens; ↓ moves in.
    page.keyboard.press("Escape")
    expect(menu).to_have_count(0)
    expect(last).to_be_focused()
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    expect(section.locator(".dropdown-menu.show .dropdown-item").first).to_be_focused()
    page.keyboard.press("Escape")

    # Archive posts and toasts; Delete confirms first.
    toggles.first.click()
    section.locator(".dropdown-menu.show").get_by_text("Archive").click()
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Archived")
    page.once("dialog", lambda dialog: dialog.accept())
    toggles.first.click()
    section.locator(".dropdown-menu.show").get_by_text("Delete").click()
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Deleted")

    # Edit opens the server-rendered modal (hx-target in attrs).
    toggles.first.click()
    section.locator(".dropdown-menu.show").get_by_text("Edit").click()
    expect(page.locator("#server-modal")).to_be_visible()
    page.locator("#server-modal").get_by_role("button", name="Cancel").click()
    expect(page.locator("#server-modal")).to_be_hidden()


def test_action_menu_inline_layouts(page, playground_url):
    page.goto(f"{playground_url}/data#action-menu")
    section = page.locator("#action-menu")
    section.locator("label:has-text('Two icons')").click()
    expect(section.locator(".gth-action-menu-button")).to_have_count(16)
    expect(section.get_by_role("button", name="Edit Fix flaky CI job")).to_be_visible()
    expect(section.locator(".gth-action-menu-toggle")).to_have_count(8)
    section.locator("label:has-text('All icons')").click()
    expect(section.locator(".gth-action-menu-toggle")).to_have_count(0)
    delete = section.get_by_role("button", name="Delete Fix flaky CI job")
    expect(delete).to_be_visible()
    # A danger icon button is red, not the body colour its text-body class
    # would otherwise force (in either colour mode).
    edit = section.get_by_role("button", name="Edit Fix flaky CI job")
    for _ in range(2):
        danger = page.evaluate("""() => { const p = document.createElement('span');
            p.style.color = 'rgb(var(--bs-danger-rgb))'; document.body.append(p);
            const c = getComputedStyle(p).color; p.remove(); return c; }""")
        expect(delete).to_have_css("color", danger)
        assert edit.evaluate("el => getComputedStyle(el).color") != danger
        page.click(".gth-theme-toggle")


def test_description_list_layouts(page, playground_url):
    page.set_viewport_size({"width": 1400, "height": 900})
    page.goto(f"{playground_url}/data#description-list")
    section = page.locator("#description-list")
    expect(section.locator("dd", has_text="—").first).to_be_visible()  # Supplier: None
    expect(section.locator(".badge", has_text="Cable").first).to_be_visible()  # Markup value

    # columns=2: two label/value pairs share a row.
    # (Measured in one evaluate: the #hash scroll may still be moving the page.)
    rects = """sel => [...document.querySelectorAll(sel)].slice(0, 2).map(e => {
        const r = e.getBoundingClientRect(); return {x: r.x, y: r.y, h: r.height}; })"""
    first, second = page.evaluate(rects, "#description-list-wide .gth-dl-term")
    assert abs(first["y"] - second["y"]) < 1 and second["x"] > first["x"]

    # Phone: each value sits under its label.
    page.set_viewport_size({"width": 400, "height": 900})
    t, d = page.evaluate(rects, "#description-list .gth-dl > :is(dt, dd)")
    assert d["y"] >= t["y"] + t["h"] - 1 and abs(d["x"] - t["x"]) < 1


def test_progress_bars_and_live_sync(page, playground_url):
    page.goto(f"{playground_url}/data#progress")
    section = page.locator("#progress")
    upload = section.get_by_role("progressbar", name="Uploading statements")
    expect(upload).to_have_attribute("aria-valuenow", "42")
    expect(upload.locator(".progress-bar")).to_have_attribute("style", "width: 42%")
    full = section.get_by_role("meter").nth(2)
    expect(full).to_have_attribute("aria-valuetext", "7.6 of 8 GB")
    expect(full.locator(".progress-bar")).to_have_class(re.compile(r"\bbg-danger\b"))
    expect(section.get_by_role("meter").nth(1).locator(".progress-bar")).to_have_class(
        re.compile(r"\bbg-warning\b"))
    busy = section.get_by_role("progressbar", name="Contacting the mail server")
    assert busy.get_attribute("aria-valuenow") is None

    # Live: polls every second until 100%, then stops and toasts.
    polls = []
    page.on("request", lambda r: polls.append(r.url) if r.url.endswith("/demo/progress") else None)
    section.get_by_role("button", name="Start sync").click()
    live = page.locator("#progress-live [role=progressbar]")
    expect(live).to_have_attribute("aria-valuenow", "100", timeout=10000)
    expect(page.locator(DYNAMIC_TOAST).last).to_contain_text("Sync complete")
    expect(page.locator("#progress-live")).not_to_have_attribute("hx-trigger", re.compile("."))
    count = len(polls)
    page.wait_for_timeout(2500)
    assert len(polls) == count == 4  # stopped once the bar came back without poll_url


def test_progress_stripes_stop_under_reduced_motion(page, playground_url):
    page.goto(f"{playground_url}/data#progress")
    page.evaluate("document.documentElement.setAttribute('data-gth-motion', 'reduce')")
    bar = page.locator("#progress .progress-bar-animated").first
    assert bar.evaluate("el => getComputedStyle(el).animationName") == "none"


INTRO_BANNER = "[data-gth-banner='playground-intro']"


def test_site_banner_dismissal_is_remembered_per_message(page, playground_url):
    page.goto(f"{playground_url}/feedback")
    intro = page.locator(INTRO_BANNER)
    expect(intro).to_be_visible()
    assert intro.evaluate("el => el.compareDocumentPosition(document.querySelector('nav')) & 4")
    intro.get_by_role("button", name="Dismiss").click()
    expect(intro).to_have_count(0)

    # Reload: hidden from first paint, not removed after a flash.
    page.goto(f"{playground_url}/feedback", wait_until="domcontentloaded")
    assert page.locator(INTRO_BANNER).evaluate("el => getComputedStyle(el).display") == "none"

    # An edited message shows again.
    page.goto(f"{playground_url}/feedback?banner_v=2")
    expect(page.locator(INTRO_BANNER)).to_be_visible()
    expect(page.locator(INTRO_BANNER)).to_contain_text("message changed")


def test_banner_without_id_only_closes_for_the_page_view(page, playground_url):
    page.goto(f"{playground_url}/feedback#alert-banner")
    warn = page.locator("#banner-tones .gth-alert-banner", has_text="Degraded")
    warn.get_by_role("button", name="Dismiss").click()
    expect(warn).to_have_count(0)
    page.reload()
    expect(page.locator("#banner-tones .gth-alert-banner", has_text="Degraded")).to_be_visible()
    # Non-dismissible ones have no close button; the bad tone announces as an alert.
    bad = page.locator("#banner-tones .gth-alert-banner", has_text="Maintenance tonight")
    expect(bad).to_have_attribute("role", "alert")
    expect(bad.get_by_role("button", name="Dismiss")).to_have_count(0)


def test_banner_dismiss_from_the_keyboard(page, playground_url):
    page.goto(f"{playground_url}/feedback#alert-banner")
    good = page.locator("#banner-tones .gth-alert-banner", has_text="All systems normal")
    good.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(good).to_have_count(0)


def test_notification_bell_panel_and_mark_read(page, playground_url):
    page.request.post(f"{playground_url}/demo/reset")
    _impersonate(page, playground_url, "viewer")
    badge = page.locator(".gth-notification-bell .gth-notification-badge")
    expect(badge).to_contain_text("2")
    page.click(".gth-notification-bell > button")
    panel = page.locator(".gth-notification-panel")
    expect(panel.locator(".gth-notification")).to_have_count(3)
    expect(panel.locator(".gth-notification-unread")).to_have_count(2)
    # Marking one read updates the badge and the open panel, with no page load.
    panel.locator(".gth-notification-unread .gth-notification-read button").first.click()
    expect(badge).to_contain_text("1")
    expect(panel.locator(".gth-notification-unread")).to_have_count(1)
    # The full page: "Mark all read" empties the unread view and hides the badge.
    page.goto(f"{playground_url}/notifications?unread=1")
    expect(page.locator("#gth-notifications-list .gth-notification")).to_have_count(1)
    page.click(".gth-notifications-read-all button")
    expect(page.locator("#gth-notifications-list")).to_contain_text("No unread notifications.")
    expect(badge).to_have_text("")
    page.request.post(f"{playground_url}/demo/reset")


def test_forgot_password_through_the_outbox(page, playground_url):
    page.request.post(f"{playground_url}/demo/reset")
    page.goto(f"{playground_url}/login-demo")
    page.click(".gth-auth-forgot a")
    expect(page).to_have_url(f"{playground_url}/forgot-password-demo")
    expect(page.locator("#gth-field-identifier")).to_be_focused()
    page.fill("#gth-field-identifier", "demo")
    page.click("form[action='/forgot-password-demo'] button[type=submit]")
    expect(page.locator(".gth-auth-card")).to_contain_text("Check your email")
    page.goto(f"{playground_url}/demo/outbox")
    page.locator("[data-outbox-link]").first.click()
    page.fill("#gth-field-password", "brand-new-1")
    page.fill("#gth-field-password_confirm", "brand-new-1")
    page.click(".gth-auth-card button[type=submit]")
    expect(page.locator(".gth-auth-card")).to_contain_text("Your password has been changed.")
    page.click(".gth-auth-card a.btn")  # Sign in
    page.fill("#gth-field-user_id", "demo")
    page.fill("#gth-field-password", "brand-new-1")
    page.click("form[action='/login-demo'] button[type=submit]")
    expect(page).to_have_url(f"{playground_url}/")
    page.request.post(f"{playground_url}/demo/reset")


def test_the_user_menu_follows_the_profiles_display_name(page, playground_url):
    page.request.post(f"{playground_url}/demo/reset")
    _impersonate(page, playground_url, "admin")
    expect(page.locator(".gth-user-menu .gth-avatar")).to_have_text("AA")
    expect(page.locator(".gth-user-menu-name")).to_have_text("Ada Admin")
    page.goto(f"{playground_url}/settings")
    page.fill("#gth-settings-profile [name='display_name']", "Grace Hopper")
    page.click("#gth-settings-profile button[type=submit]")
    expect(page.locator(".toast")).to_contain_text("Profile saved")
    page.reload()
    expect(page.locator(".gth-user-menu .gth-avatar")).to_have_text("GH")
    expect(page.locator(".gth-user-menu-name")).to_have_text("Grace Hopper")
    page.request.post(f"{playground_url}/demo/reset")


def test_sign_up_with_an_email_and_confirm_it(page, playground_url):
    page.request.post(f"{playground_url}/demo/reset")
    page.goto(f"{playground_url}/register-demo")
    page.fill("#gth-field-user_id", "ada")
    page.fill("#gth-field-email", "ada@example.com")
    page.fill("#gth-field-password", "long-enough")
    page.fill("#gth-field-password_confirm", "long-enough")
    page.click("form[action='/register-demo'] button[type=submit]")
    expect(page.locator(".gth-auth-card")).to_contain_text("Check your email")
    page.goto(f"{playground_url}/demo/outbox")
    page.locator("[data-outbox-link]").first.click()
    expect(page.locator(".gth-auth-card")).to_contain_text("Your email address is confirmed.")
    page.request.post(f"{playground_url}/demo/reset")
