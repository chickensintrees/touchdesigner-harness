"""Write the asset pack's aliases.json and the flat sheets' model folders.

    python tools/assets/make_aliases.py <pack_dir>

aliases.json tells experiments/sw_hub/paths_module.py which file of a pack answers
a name the pack does not hold. The scenes ask for this pack's models by their own
names, so the table holds only the entries in FIXED, plus one per name listed
under an optional "stands_in_for" in tools/assets/objects.json.

Each flat sheet (pack/sheets/<name>.png) also gets a folder
models/<name>/ with basecolor.png and a thin slab model.obj in the sheet's
proportions, because scenes ask for sheets the way they ask for models.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent

# Requested name -> this pack's file, for things that are not 3D objects.
FIXED = {
    "fonts/ChicagoFLF.ttf": "fonts/IBMPlexMono-Medium.ttf",
}


def slab_obj(width, height, depth=0.004):
    """A thin box, longest side 1, lying in the XY plane and facing +Z, with UVs on both faces."""
    longest = max(width, height)
    w, h, d = width / longest / 2, height / longest / 2, depth / 2
    v = [(-w, -h, d), (w, -h, d), (w, h, d), (-w, h, d), (-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d)]
    vt = [(0, 0), (1, 0), (1, 1), (0, 1)]
    vn = [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
    faces = [  # (vertex, uv, normal) triples, counter-clockwise from outside
        [(1, 1, 1), (2, 2, 1), (3, 3, 1)], [(1, 1, 1), (3, 3, 1), (4, 4, 1)],          # front
        [(6, 1, 2), (5, 2, 2), (8, 3, 2)], [(6, 1, 2), (8, 3, 2), (7, 4, 2)],          # back
        [(2, 1, 3), (6, 2, 3), (7, 3, 3)], [(2, 1, 3), (7, 3, 3), (3, 4, 3)],          # right
        [(5, 1, 4), (1, 2, 4), (4, 3, 4)], [(5, 1, 4), (4, 3, 4), (8, 4, 4)],          # left
        [(4, 1, 5), (3, 2, 5), (7, 3, 5)], [(4, 1, 5), (7, 3, 5), (8, 4, 5)],          # top
        [(5, 1, 6), (6, 2, 6), (2, 3, 6)], [(5, 1, 6), (2, 3, 6), (1, 4, 6)],          # bottom
    ]
    lines = ["# a flat sheet"]
    lines += ["v %.6f %.6f %.6f" % p for p in v]
    lines += ["vt %.6f %.6f" % p for p in vt]
    lines += ["vn %.6f %.6f %.6f" % p for p in vn]
    lines += ["f " + " ".join("%d/%d/%d" % t for t in face) for face in faces]
    return "\n".join(lines) + "\n"


def main(pack_dir):
    pack = Path(pack_dir)
    spec = json.loads((HERE / "objects.json").read_text(encoding="utf-8"))
    table = dict(FIXED)
    missing = []
    for obj in spec["objects"]:
        if not (pack / "models" / obj["name"] / "model.obj").exists():
            missing.append(obj["name"])
        for asked in obj.get("stands_in_for", []):
            table["models/" + asked] = "models/" + obj["name"]
    for sheet in spec["sheets"]["items"]:
        source = pack / "sheets" / (sheet["name"] + ".png")
        if not source.exists():
            missing.append("sheets/" + sheet["name"])
            continue
        folder = pack / "models" / sheet["name"]
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.open(source).convert("RGB")
        image.save(folder / "basecolor.png")
        (folder / "model.obj").write_text(slab_obj(*image.size), encoding="ascii", newline="\n")
        (folder / "info.json").write_text(json.dumps({"name": sheet["name"], "triangles": 12, "description": "A flat printed sheet."}, indent=1), encoding="utf-8")
        for asked in sheet.get("stands_in_for", []):
            table["models/" + asked] = "models/" + sheet["name"]
    (pack / "aliases.json").write_text(json.dumps(dict(sorted(table.items())), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"aliases": len(table), "missing": missing}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
