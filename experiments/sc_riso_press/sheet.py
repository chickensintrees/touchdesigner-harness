# Contact sheet of captures: python sheet.py out.png a.png b.png ...   (3 columns)
import os
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
cols = 3
w, h = 640, 360
rows = (len(files) + cols - 1) // cols
im = Image.new('RGB', (cols * w, rows * h), (20, 20, 20))
d = ImageDraw.Draw(im)
for i, f in enumerate(files):
    t = Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS)
    im.paste(t, ((i % cols) * w, (i // cols) * h))
    label = os.path.basename(f)[:-4]
    d.rectangle([(i % cols) * w, (i // cols) * h, (i % cols) * w + 8 * len(label) + 8, (i // cols) * h + 16], fill=(0, 0, 0))
    d.text(((i % cols) * w + 4, (i // cols) * h + 2), label, fill=(255, 255, 255))
im.save(out)
