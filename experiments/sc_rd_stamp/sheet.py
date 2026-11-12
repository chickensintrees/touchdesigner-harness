# Dev helper, run in a shell (not TouchDesigner): contact sheet of captures.
#   python sheet.py out.png name1 name2 ...     (names without .png, from captures/)
import os
import sys
from PIL import Image, ImageDraw

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
out, names = sys.argv[1], sys.argv[2:]
cols = 4 if len(names) > 6 else 3
w, h = 426, 240
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
for i, n in enumerate(names):
    im = Image.open(os.path.join(here, n + ".png")).convert("RGB").resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 4), n, fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(os.path.join(here, out))
print(out, sheet.size)
