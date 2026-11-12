# Contact sheet of captures: python sheet.py <prefix> <out name> [cols]
# Finds the captures folder from this file's own location, so it runs from any directory.
import sys
from pathlib import Path
from PIL import Image, ImageDraw
pre, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
import glob, os
CAP = Path(__file__).resolve().parent / 'captures'
files = sorted(glob.glob(str(CAP / ('%s*.png' % pre))))
W, H = 480, 270
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * H), (40, 40, 40))
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    ImageDraw.Draw(sheet).text(((i % cols) * W + 6, (i // cols) * H + 4), os.path.basename(f), fill=(255, 255, 0))
sheet.save(str(CAP / ('%s.png' % out)))
print(len(files))
