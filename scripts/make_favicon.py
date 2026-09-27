"""Regenerate static/logo/favicon.png from static/logo/logo-light.png.

logo-light.png is a 512x512 canvas whose mark only fills about 67% x 85% of
it; that padding is fine for the navbar but makes the favicon look smaller
than other sites' tab icons. This crops to the mark, centres it on a square
with MARGIN px of air at the target size, and resizes to SIZE x SIZE.

Dev-only (needs Pillow, which isn't a package dependency):

    python scripts/make_favicon.py

Then update the favicon.png row (SHA256, size) in static/VENDORED.md.
"""

from pathlib import Path

from PIL import Image

LOGO_DIR = Path(__file__).resolve().parent.parent / "src" / "greentechhub_ui" / "static" / "logo"
SIZE = 64
MARGIN = 1  # px at SIZE, so the mark doesn't touch the tab icon's edge
ALPHA_THRESHOLD = 8  # ignore near-invisible antialiasing fringe when cropping


def main() -> None:
    logo = Image.open(LOGO_DIR / "logo-light.png").convert("RGBA")
    mask = logo.getchannel("A").point(lambda a: 255 if a > ALPHA_THRESHOLD else 0)
    mark = logo.crop(mask.getbbox())

    side = round(max(mark.size) * SIZE / (SIZE - 2 * MARGIN))
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))

    out = LOGO_DIR / "favicon.png"
    square.resize((SIZE, SIZE), Image.Resampling.LANCZOS).save(out, optimize=True)
    print(f"wrote {out} ({SIZE}x{SIZE}, mark {mark.size} from {logo.size})")


if __name__ == "__main__":
    main()
