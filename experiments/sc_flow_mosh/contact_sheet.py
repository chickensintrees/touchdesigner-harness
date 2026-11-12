# Contact sheet of take captures. Usage (plain Python with PIL, outside TouchDesigner):
#   python contact_sheet.py <tag> <out.png> [suffixes, default "_a,"] [takes, default 7]
# Rows are takes, columns the suffixes (e.g. "_a" then "" for <tag>_<n>_a.png, <tag>_<n>.png).
import os
import sys

from PIL import Image, ImageDraw

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
tag, out = sys.argv[1], sys.argv[2]
suffixes = sys.argv[3].split(",") if len(sys.argv) > 3 else ["_a", ""]
takes = int(sys.argv[4]) if len(sys.argv) > 4 else 7
W, H = 480, 270
cols = len(suffixes)
if cols == 1:                      # one picture per take: wrap into a grid 4 wide
    per = 4
    sheet = Image.new("RGB", (per * W, ((takes + per - 1) // per) * H), (40, 40, 40))
    cells = [(n, suffixes[0], (n % per) * W, (n // per) * H) for n in range(takes)]
else:
    sheet = Image.new("RGB", (cols * W, takes * H), (40, 40, 40))
    cells = [(n, s, j * W, n * H) for n in range(takes) for j, s in enumerate(suffixes)]
d = ImageDraw.Draw(sheet)
for n, s, x, y in cells:
    p = os.path.join(here, "%s_%d%s.png" % (tag, n, s))
    if not os.path.exists(p):
        continue
    sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
    d.rectangle([x, y, x + 46, y + 16], fill=(0, 0, 0))
    d.text((x + 4, y + 2), "%d%s" % (n, s), fill=(255, 255, 0))
sheet.save(os.path.join(here, out))
print(out, sheet.size)
