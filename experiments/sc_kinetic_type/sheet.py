# Contact sheet of captures (runs outside TouchDesigner):
#   python sheet.py out.png cols file1.png file2.png ...
import sys
from PIL import Image, ImageDraw

out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tw, th = 426, 240
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((tw - 4, th - 4), Image.LANCZOS)
    x, y = (i % cols) * tw + 2, (i // cols) * th + 2
    sheet.paste(im, (x, y))
    label = f.replace('\\', '/').split('/')[-1][:-4]
    d.rectangle([x, y, x + 8 + 6 * len(label), y + 13], fill=(0, 0, 0))
    d.text((x + 3, y + 1), label, fill=(255, 255, 0))
sheet.save(out)
print(out, sheet.size)
