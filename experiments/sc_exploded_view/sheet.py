# Contact sheet of take captures (offline): python sheet.py <prefix> <out.png> [cols]
import sys, glob, os
from PIL import Image
prefix, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
here = os.path.dirname(os.path.abspath(__file__))
files = sorted((f for f in glob.glob(os.path.join(here, 'captures', prefix + '*.png')) if 'sheet' not in f), key=lambda f: int(''.join(ch for ch in os.path.basename(f)[len(prefix):] if ch.isdigit()) or 0))
tw, th = 640, 360
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (20, 20, 20))
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
sheet.save(os.path.join(here, 'captures', out))
print(len(files), 'tiles')
