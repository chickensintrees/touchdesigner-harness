# Contact sheet helper: python sheet.py out.png cols in1.png in2.png ...
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w = 640; h = 360
ims = [im.resize((w, h)) for im in ims]
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
