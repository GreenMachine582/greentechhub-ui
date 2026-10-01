"""Regenerate static/logo/favicon.png from static/logo/logo-light.png.

The mark in logo-light.png is portrait (about 3:4), so cropping it to a
square still leaves gaps either side and the tab icon looks narrow next to
other sites'. Instead the mark sits on a dark, rounded-square tile (the
brand's near-black green) that fills the icon: a solid square on light and
dark tab strips alike, with the green mark standing out even at 16px.

Rendered at CANVAS px and downscaled once with LANCZOS, so the tile's
rounded corners and the mark stay smooth at SIZE (browsers scale the 64px
icon down to their 16/32px tab size themselves).

Dev-only (needs Pillow, which isn't a package dependency):

    python scripts/make_favicon.py

Then update the favicon.png row (SHA256, size) in static/VENDORED.md.
"""

from pathlib import Path

from PIL import Image, ImageDraw

LOGO_DIR = Path(__file__).resolve().parent.parent / "src" / "greentechhub_ui" / "static" / "logo"
SIZE = 64
CANVAS = 256  # draw large, downscale once
TILE_COLOR = (11, 31, 11, 255)  # #0b1f0b, theme.css's --gth-on-accent in dark mode
TILE_RADIUS = 0.22  # corner radius, as a fraction of the side
MARK_HEIGHT = 0.86  # the mark's height, as a fraction of the side
ALPHA_THRESHOLD = 8  # ignore near-invisible antialiasing fringe when cropping


def main() -> None:
    logo = Image.open(LOGO_DIR / "logo-light.png").convert("RGBA")
    mask = logo.getchannel("A").point(lambda a: 255 if a > ALPHA_THRESHOLD else 0)
    mark = logo.crop(mask.getbbox())

    tile = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle(
        (0, 0, CANVAS - 1, CANVAS - 1), radius=round(CANVAS * TILE_RADIUS), fill=TILE_COLOR
    )
    height = round(CANVAS * MARK_HEIGHT)
    width = round(mark.width * height / mark.height)
    mark = mark.resize((width, height), Image.Resampling.LANCZOS)
    tile.alpha_composite(mark, ((CANVAS - width) // 2, (CANVAS - height) // 2))

    out = LOGO_DIR / "favicon.png"
    tile.resize((SIZE, SIZE), Image.Resampling.LANCZOS).save(out, optimize=True)
    print(f"wrote {out} ({SIZE}x{SIZE}, mark {width}x{height} on a {CANVAS}px tile)")


if __name__ == "__main__":
    main()
