# Asserts that the takes differ at a glance, and builds the contact sheet.
# Run in a shell (not in TouchDesigner):
#   python check_takes.py                 captures/take_*.png -> captures/takes_sheet.png
#   python check_takes.py out.png a.png b.png ...     any files, sheet only
# "At a glance" is measured the way a thumbnail shows it: each capture is reduced
# to 32x18 grey, and every pair must differ by MIN_DIFF mean absolute difference.
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
# Calibration (2026-11-10): the scene before takes existed measured 0.029 between two
# captures in one section and 0.138 across a section change (captures/v_before_1..3.png).
# The floor sits above that: two takes must differ more than the old scene ever did.
# A snare-inverted capture inflates the distance, so capture takes between snares.
MIN_DIFF = 0.15


def sheet(paths, out, cols=4, w=480):
    ims = [Image.open(p).convert('RGB') for p in paths]
    h = int(w * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    page = Image.new('RGB', (cols * (w + 8) + 8, rows * (h + 30) + 8), (40, 40, 60))
    d = ImageDraw.Draw(page)
    for i, (p, im) in enumerate(zip(paths, ims)):
        x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 30)
        page.paste(im.resize((w, h), Image.LANCZOS), (x, y))
        d.text((x + 2, y + h + 6), os.path.basename(p), fill=(255, 255, 255))
    page.save(out)
    return out


def thumb(p):
    im = Image.open(p).convert('L').resize((32, 18), Image.BOX)
    return [v / 255.0 for v in im.getdata()]


def distances(paths):
    t = [thumb(p) for p in paths]
    out = {}
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            out[(i, j)] = sum(abs(a - b) for a, b in zip(t[i], t[j])) / len(t[i])
    return out


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print(sheet(sys.argv[2:], sys.argv[1]))
        sys.exit(0)
    paths = sorted(glob.glob(os.path.join(HERE, 'captures', 'take_[0-9].png')))
    if len(paths) < 6:
        print('FAIL: need at least six captures/take_<n>.png, found', len(paths))
        sys.exit(1)
    print(sheet(paths, os.path.join(HERE, 'captures', 'takes_sheet.png')))
    d = distances(paths)
    bad = [(k, v) for k, v in d.items() if v < MIN_DIFF]
    for (i, j), v in sorted(d.items(), key=lambda kv: kv[1])[:6]:
        print('closest: take %d vs take %d  %.3f' % (i, j, v))
    if bad:
        print('FAIL: pairs too alike:', bad)
        sys.exit(1)
    print('PASS: %d takes, smallest pair distance %.3f (floor %.2f)' % (len(paths), min(d.values()), MIN_DIFF))
