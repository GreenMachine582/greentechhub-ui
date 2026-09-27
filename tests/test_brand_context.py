import struct

import greentechhub_ui
from greentechhub_ui.theme import brand_context


def test_brand_context_defaults_have_no_logo_or_favicon():
    brand = brand_context(service_name="Playground")
    assert brand["logo_url"] is None
    assert brand["favicon_url"] is None


def test_brand_context_show_logo_uses_different_assets_for_navbar_and_favicon():
    brand = brand_context(service_name="Playground", show_logo=True)
    assert brand["logo_url"] == "/static/logo/logo.png"
    assert brand["favicon_url"] == "/static/logo/favicon.png"
    assert len({brand["logo_url"], brand["logo_light_url"], brand["favicon_url"]}) == 3


def test_brand_context_respects_static_url_prefix():
    brand = brand_context(show_logo=True, static_url_prefix="/gth-assets")
    assert brand["logo_url"] == "/gth-assets/logo/logo.png"
    assert brand["favicon_url"] == "/gth-assets/logo/favicon.png"


def test_brand_context_logo_light_url_is_the_light_variant():
    assert brand_context()["logo_light_url"] is None
    brand = brand_context(show_logo=True, static_url_prefix="/gth-assets")
    assert brand["logo_light_url"] == "/gth-assets/logo/logo-light.png"


def test_favicon_is_a_tight_64px_square_png():
    # app.html declares sizes="64x64"; scripts/make_favicon.py regenerates it.
    data = (greentechhub_ui.static_path / "logo" / "favicon.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    assert struct.unpack(">II", data[16:24]) == (64, 64)
