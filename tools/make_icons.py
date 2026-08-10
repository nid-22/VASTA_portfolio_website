"""Regenerate the site favicons from the VAST wordmark.

Google's favicon crawler prefers the largest declared icon, so every icon we
declare has to be the real logo -- a leftover template icon anywhere in the set
is what ends up in the search results.

Usage:  python tools/make_icons.py
"""
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "vasta_portfolio" / "static" / "assets" / "img"
SOURCE = IMG_DIR / "vastarchitects.png"

# Crop box of the "va" mark inside the full "vast architects" wordmark.
# The full lockup is unreadable below ~200px, so the icon uses the first two
# glyphs only.
MARK_BOX = (40, 36, 261, 197)

BACKGROUND = (255, 255, 255, 255)
PADDING = 0.14  # share of the canvas left empty on each side

# 48px is Google's minimum useful favicon size; the rest cover tabs, Android
# home screens and iOS.
PNG_SIZES = [48, 96, 192, 512]
ICO_SIZES = [16, 32, 48]
APPLE_TOUCH_SIZE = 180


def build_master(size=1024):
    """Return a square canvas with the mark centred on a white background."""
    mark = Image.open(SOURCE).convert("RGBA").crop(MARK_BOX)

    inner = int(size * (1 - 2 * PADDING))
    scale = min(inner / mark.width, inner / mark.height)
    mark = mark.resize(
        (max(1, round(mark.width * scale)), max(1, round(mark.height * scale))),
        Image.LANCZOS,
    )

    canvas = Image.new("RGBA", (size, size), BACKGROUND)
    canvas.paste(
        mark,
        ((size - mark.width) // 2, (size - mark.height) // 2),
        mark,
    )
    return canvas


def main():
    master = build_master()

    for size in PNG_SIZES:
        out = IMG_DIR / f"favicon-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(out, optimize=True)
        print("wrote", out.relative_to(BASE_DIR))

    apple = IMG_DIR / "apple-touch-icon.png"
    master.resize((APPLE_TOUCH_SIZE, APPLE_TOUCH_SIZE), Image.LANCZOS).convert(
        "RGB"
    ).save(apple, optimize=True)
    print("wrote", apple.relative_to(BASE_DIR))

    # Served from the domain root -- Google probes /favicon.ico directly.
    ico = IMG_DIR / "favicon.ico"
    master.convert("RGB").save(ico, sizes=[(s, s) for s in ICO_SIZES])
    print("wrote", ico.relative_to(BASE_DIR))


if __name__ == "__main__":
    main()
