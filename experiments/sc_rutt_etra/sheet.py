# contact sheet helper: python sheet.py out.png a.png b.png ...
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = 640, 360
cols = 4 if len(ims) > 6 else (3 if len(ims) > 4 else 2)
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    sh.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
sh.save(out)
