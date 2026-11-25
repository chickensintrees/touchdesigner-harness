"""File generated footage and rooms in the asset pack.

    python tools/assets/file_generated.py --footage <folder of clips> --rooms <folder of rooms> [--pack assets]

Footage: every .mp4 in the folder is copied to <pack>/footage/ and listed in
<pack>/footage/footage.json (name, file, frames, fps, size), read with ffprobe.

Rooms: a room is <name>.png (a photograph of a room with a switched-off screen in
it), <name>.json (the four corners of the screen in pixels: top-left, top-right,
bottom-right, bottom-left) and mask/<name>.png (white where the glass is). Each
is written to <pack>/rooms/ no larger than 1280 px a side (the Non-Commercial
TouchDesigner limit), holes in the mask are filled, and <pack>/rooms/rooms.json
lists every room with its corners as fractions of the picture and the matrix
that turns a place in the picture into a place on the screen (see homography()).
<pack>/rooms/rooms.tsv holds the same rows for a Table DAT: name, file, mask, the
middle of the screen (cx, cy), its shape (aspect), how bright the switched-off
glass is (glass, 0..1) and the matrix (m0..m8).

Runs offline, never inside TouchDesigner. Needs Pillow and numpy; ffprobe for footage.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

LIMIT = 1280


def homography(corners):
    """The 3x3 matrix H (row-major list of 9) that maps the quadrilateral `corners`
    (top-left, top-right, bottom-right, bottom-left; any units, y down) onto the unit
    square (0,0) (1,0) (1,1) (0,1): for a point (x, y), (s, t, w) = H @ (x, y, 1) and
    the place on the screen is (s / w, t / w), t measured down from the top edge."""
    target = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    a, b = [], []
    for (x, y), (s, t) in zip(corners, target, strict=True):
        a.append([x, y, 1, 0, 0, 0, -s * x, -s * y])
        b.append(s)
        a.append([0, 0, 0, x, y, 1, -t * x, -t * y])
        b.append(t)
    h = np.linalg.solve(np.array(a, dtype=np.float64), np.array(b, dtype=np.float64))
    return [round(float(v), 9) for v in h] + [1.0]


def fill_holes(mask):
    """A greyscale mask with every dark island that does not touch the border made white."""
    grey = mask.convert("L")
    binary = grey.point(lambda v: 255 if v > 127 else 0)
    flooded = Image.new("L", (binary.width + 2, binary.height + 2), 0)  # a dark border so one fill reaches every outside region
    flooded.paste(binary, (1, 1))
    ImageDraw.floodfill(flooded, (0, 0), 128)
    inside = np.asarray(flooded.crop((1, 1, binary.width + 1, binary.height + 1)))
    out = np.asarray(grey).copy()
    out[inside == 0] = 255
    return Image.fromarray(out, "L")


def _probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": int(s["width"]), "height": int(s["height"]), "fps": round(float(num) / float(den), 4), "frames": int(s["nb_read_frames"])}


def file_footage(source, pack):
    out = Path(pack) / "footage"
    out.mkdir(parents=True, exist_ok=True)
    clips = []
    for clip in sorted(Path(source).glob("*.mp4")):
        shutil.copyfile(clip, out / clip.name)
        clips.append({"name": clip.stem, "file": clip.name, **_probe(clip)})
    (out / "footage.json").write_text(json.dumps({"clips": clips}, indent=1) + "\n", encoding="utf-8")
    return clips


def file_rooms(source, pack, leave_out=()):
    source, out = Path(source), Path(pack) / "rooms"
    (out / "mask").mkdir(parents=True, exist_ok=True)
    rooms = []
    for meta in sorted(source.glob("*.json")):
        name = meta.stem
        if name in leave_out:
            continue
        info = json.loads(meta.read_text(encoding="utf-8"))
        picture = Image.open(source / (name + ".png")).convert("RGB")
        w, h = picture.size
        scale = min(1.0, LIMIT / max(w, h))
        size = (round(w * scale), round(h * scale))
        picture = picture.resize(size, Image.LANCZOS)
        picture.save(out / (name + ".png"))
        mask = fill_holes(Image.open(source / "mask" / (name + ".png"))).resize(size, Image.LANCZOS)
        mask.save(out / "mask" / (name + ".png"))
        on_glass = np.asarray(mask) > 200
        glass = float(np.asarray(picture.convert("L"))[on_glass].mean() / 255.0) if on_glass.any() else 0.0
        corners = [[round(x / w, 6), round(y / h, 6)] for x, y in info["corners"]]
        (tl, tr, br, bl) = info["corners"]
        wide = (np.hypot(tr[0] - tl[0], tr[1] - tl[1]) + np.hypot(br[0] - bl[0], br[1] - bl[1])) / 2
        tall = (np.hypot(bl[0] - tl[0], bl[1] - tl[1]) + np.hypot(br[0] - tr[0], br[1] - tr[1])) / 2
        rooms.append({"name": name, "file": name + ".png", "mask": "mask/" + name + ".png", "width": size[0], "height": size[1],
                      "corners": corners, "centre": [round(float(np.mean([c[i] for c in corners])), 6) for i in (0, 1)],
                      "aspect": round(float(wide / tall), 4), "glass": round(glass, 4), "to_screen": homography(corners)})
    index = {
        "corners": "top-left, top-right, bottom-right, bottom-left, as fractions of the picture, y down",
        "to_screen": "3x3 row-major: (s, t, w) = M @ (x, y, 1); the place on the screen is (s/w, t/w), 0..1, t down",
        "rooms": rooms,
    }
    (out / "rooms.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    lines = ["\t".join(["name", "file", "mask", "cx", "cy", "aspect", "glass"] + ["m%d" % i for i in range(9)])]
    for r in rooms:
        lines.append("\t".join(str(v) for v in [r["name"], r["file"], r["mask"], *r["centre"], r["aspect"], r["glass"], *r["to_screen"]]))
    (out / "rooms.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rooms


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--footage", help="folder of .mp4 clips")
    ap.add_argument("--rooms", help="folder of rooms (name.png, name.json, mask/name.png)")
    ap.add_argument("--leave-out", nargs="*", default=[], metavar="ROOM")
    ap.add_argument("--pack", default=str(Path(__file__).resolve().parents[2] / "assets"))
    a = ap.parse_args(argv)
    if a.footage:
        print("%d clips -> %s/footage" % (len(file_footage(a.footage, a.pack)), a.pack))
    if a.rooms:
        print("%d rooms -> %s/rooms" % (len(file_rooms(a.rooms, a.pack, a.leave_out)), a.pack))
    return 0


if __name__ == "__main__":
    sys.exit(main())
