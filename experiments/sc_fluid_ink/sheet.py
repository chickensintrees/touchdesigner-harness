# Contact sheet of captures (plain Python, outside TouchDesigner).
#   python sheet.py out.png cols a.png b.png ...     (names relative to captures/)
import os
import sys

from PIL import Image, ImageDraw

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
out, cols, names = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
W, H = 640, 360
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * H), (30, 30, 30))
draw = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(here, n)).convert("RGB").resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H
    sheet.paste(im, (x, y))
    draw.rectangle([x, y, x + 8 * len(n) + 8, y + 16], fill=(0, 0, 0))
    draw.text((x + 4, y + 2), n, fill=(255, 255, 255))
sheet.save(os.path.join(here, out))
print(out, sheet.size)
