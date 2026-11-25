# Contact sheet of captures. Run in the shell (not TouchDesigner):
#   python contact.py out.png a.png b.png ...     (4 columns, 480 px thumbnails, file names burnt in)
import sys
from PIL import Image, ImageDraw

out, files = sys.argv[1], sys.argv[2:]
cols = 4 if len(files) > 4 else max(1, len(files))
tw, th = 480, 270
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(im, (x, y))
    label = f.replace('\\', '/').split('/')[-1]
    d.rectangle((x, y, x + 8 * len(label) + 6, y + 14), fill=(0, 0, 0))
    d.text((x + 3, y + 1), label, fill=(255, 255, 0))
sheet.save(out)
