from greentechhub_ui.theme import brand_context


def test_brand_context_defaults_have_no_logo_or_favicon():
    brand = brand_context(service_name="Playground")
    assert brand["logo_url"] is None
    assert brand["favicon_url"] is None


def test_brand_context_show_logo_uses_different_assets_for_navbar_and_favicon():
    brand = brand_context(service_name="Playground", show_logo=True)
    assert brand["logo_url"] == "/static/logo/logo.png"
    assert brand["favicon_url"] == "/static/logo/logo-light.png"
    assert brand["logo_url"] != brand["favicon_url"]


def test_brand_context_respects_static_url_prefix():
    brand = brand_context(show_logo=True, static_url_prefix="/gth-assets")
    assert brand["logo_url"] == "/gth-assets/logo/logo.png"
    assert brand["favicon_url"] == "/gth-assets/logo/logo-light.png"


def test_brand_context_logo_light_url_is_the_light_variant():
    assert brand_context()["logo_light_url"] is None
    brand = brand_context(show_logo=True, static_url_prefix="/gth-assets")
    assert brand["logo_light_url"] == "/gth-assets/logo/logo-light.png"
