# Contact sheet of captures (runs outside TouchDesigner):  python sheet.py <prefix> <count> <out.png> [cols]
import sys
from pathlib import Path

from PIL import Image

here = Path(__file__).resolve().parent.as_posix() + "/captures/"
prefix, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
w, h = 480, 270
rows = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
for i in range(n):
    im = Image.open(here + "%s%d.png" % (prefix, i)).convert("RGB").resize((w, h))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(here + out)
print(out)
