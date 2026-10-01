import struct
import zlib

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


def test_favicon_is_a_64px_square_png():
    # app.html declares sizes="64x64"; scripts/make_favicon.py regenerates it.
    data = (greentechhub_ui.static_path / "logo" / "favicon.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    assert struct.unpack(">II", data[16:24]) == (64, 64)


def _png_alpha(data: bytes) -> list[list[int]]:
    """The alpha channel of an 8-bit RGBA PNG, decoded with the standard
    library only (Pillow isn't a test dependency)."""
    width, height, depth, colour = struct.unpack(">IIBB", data[16:26])
    assert (depth, colour) == (8, 6), "expected 8-bit RGBA"
    pos, idat = 8, b""
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"IDAT":
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length
    raw, bpp, stride = zlib.decompress(idat), 4, width * 4
    rows, prev = [], bytes(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            if kind == 1:
                line[i] = (line[i] + a) & 255
            elif kind == 2:
                line[i] = (line[i] + b) & 255
            elif kind == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif kind == 4:
                p_ = a + b - c
                pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([line[x * 4 + 3] for x in range(width)])
        prev = bytes(line)
    return rows


def test_favicon_is_a_rounded_tile_that_fills_the_square():
    # The mark is portrait, so the icon is a tile: transparent rounded
    # corners, opaque right out to the middle of every edge.
    alpha = _png_alpha((greentechhub_ui.static_path / "logo" / "favicon.png").read_bytes())
    assert alpha[0][0] == 0 and alpha[63][63] == 0
    for x, y in ((32, 0), (0, 32), (63, 32), (32, 63)):
        assert alpha[y][x] == 255, (x, y)
