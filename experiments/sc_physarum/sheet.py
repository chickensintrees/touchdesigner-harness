# contact sheet helper: python sheet.py out.png cols a.png b.png ...
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = 640, 360
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    sh.paste(im.resize((w, h), Image.LANCZOS), ((i % cols) * w, (i // cols) * h))
sh.save(out)
