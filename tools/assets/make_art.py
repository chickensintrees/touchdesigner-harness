"""Lettering for the asset pack: large words as PNG files, drawn with the pack's own fonts.

    python tools/assets/make_art.py <pack_dir>

Writes <pack_dir>/art/mark_rgb.png, mark_alpha.png, stack_rgb.png, stack_alpha.png
(1920x1440). The _rgb files are white lettering on black; the _alpha files are
white lettering on a transparent ground. Fonts are read from <pack_dir>/fonts.
Needs Pillow.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = (1920, 1440)
MARGIN = 150
PIECES = {
    "mark": (["HARNESS"], "ArchivoBlack-Regular.ttf"),
    "stack": (["REAL", "TIME"], "ArchivoBlack-Regular.ttf"),
}


def fit_font(font_file, lines, width, height):
    """The largest size at which every line fits the width and the block fits the height."""
    size = 40
    best = ImageFont.truetype(str(font_file), size)
    while size < 1400:
        font = ImageFont.truetype(str(font_file), size)
        widths = [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]
        line_height = font.getbbox("HXE")[3] - font.getbbox("HXE")[1]
        block = line_height * len(lines) + int(line_height * 0.18) * (len(lines) - 1)
        if max(widths) > width or block > height:
            break
        best = font
        size += 8
    return best


def draw(lines, font_file):
    """White lettering as an 8-bit mask, centred."""
    mask = Image.new("L", SIZE, 0)
    pen = ImageDraw.Draw(mask)
    font = fit_font(font_file, lines, SIZE[0] - 2 * MARGIN, SIZE[1] - 2 * MARGIN)
    top, bottom = font.getbbox("HXE")[1], font.getbbox("HXE")[3]
    line_height = bottom - top
    gap = int(line_height * 0.18)
    block = line_height * len(lines) + gap * (len(lines) - 1)
    y = (SIZE[1] - block) // 2
    for line in lines:
        left, _, right, _ = font.getbbox(line)
        x = (SIZE[0] - (right - left)) // 2 - left
        pen.text((x, y - top), line, font=font, fill=255)
        y += line_height + gap
    return mask


def main(pack_dir):
    pack = Path(pack_dir)
    out = pack / "art"
    out.mkdir(parents=True, exist_ok=True)
    for name, (lines, font_name) in PIECES.items():
        mask = draw(lines, pack / "fonts" / font_name)
        Image.merge("RGB", (mask, mask, mask)).save(out / (name + "_rgb.png"))
        white = Image.new("L", SIZE, 255)
        Image.merge("RGBA", (white, white, white, mask)).save(out / (name + "_alpha.png"))
        print(name, mask.getbbox())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
