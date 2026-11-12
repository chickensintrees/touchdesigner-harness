# contact sheet helper: python sheet.py out.png a.png b.png ...
# env COLS overrides the column count, env CELL the width of one thumbnail in pixels
import os
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB') for f in files]
w = int(os.environ.get('CELL', ims[0].size[0]))
h = w * ims[0].size[1] // ims[0].size[0]
cols = int(os.environ.get('COLS', 3 if len(ims) > 4 else 2))
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    sh.paste(im.resize((w, h), Image.LANCZOS), ((i % cols) * w, (i // cols) * h))
sh.save(out)
