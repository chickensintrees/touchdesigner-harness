# Contact sheet of take captures (plain python + Pillow): python sheet.py out.png a.png b.png ...
import os
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
cols = 4 if len(files) > 4 else len(files)
rows = (len(files) + cols - 1) // cols
W, H = 480, 270
sheet = Image.new('RGB', (cols * W, rows * H), 'black')
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H
    sheet.paste(im, (x, y))
    d.text((x + 6, y + 4), os.path.basename(f), fill=(255, 255, 255))
sheet.save(out)
