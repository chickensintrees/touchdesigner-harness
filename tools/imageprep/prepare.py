"""Prepare a folder of images for the image templates (sw_images, im_depth_relief, im_montage).

    python tools/imageprep/prepare.py <folder of images> [--name NAME] [--out image_sets/NAME]

Runs offline, never inside TouchDesigner. It reads a folder of pictures in any
mix of sizes and formats and writes a *prepared set*: every picture normalised,
measured and put in colour order, plus one manifest that lists each picture and
every file derived from it. The TouchDesigner templates read only the prepared
set, so the source folder can stay wherever it is.

Tier 0 (this file, no GPU, needs only Pillow and numpy):
  img/NNN.jpg      the picture, upright, RGB, longest side <= --max, in colour order
  depth/NNN.png    a depth GUESS from brightness and height in frame (not real depth)
  cut/NNN.png      a ROUGH cut-out keyed from the border colour (good on flat grounds only)
  atlas.png        every picture as a square tile, in colour order (<= 1280 px a side)
  palette.png      5 pixels per picture: its dominant colours, one row per picture
  table.tsv        the manifest's per-picture rows, for a Table DAT
  manifest.json    everything above, with where each file came from

Tier 1 (optional, made elsewhere, for example by a ComfyUI batch): give this tool
the folders that hold the results and it files them in the set and the manifest.
Files are matched to pictures by the source file's name without its extension.
  --depth-from DIR     real depth maps      (name.png)        -> depth/NNN.png, depth_source "provided"
  --cutouts-from DIR   real cut-outs, RGBA  (name.png)        -> cut/NNN.png,   cutout_source "provided"
  --meshes-from DIR    models               (name.glb)        -> listed as mesh_source; convert with tools/models
  --clips-from DIR     video clips          (name.mp4/.mov)   -> clip/NNN.<ext>
  --leave-out NAME ... pictures to skip, by file name without extension (listed in the manifest as left_out)

The Non-Commercial TouchDesigner licence limits any picture to 1280 px a side,
which is why --max defaults to 1024 and the atlas never exceeds 1280.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

VERSION = 1
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
ATLAS_LIMIT = 1280


def find_images(folder):
    return sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)


def load(path, max_side):
    """The picture upright, RGB, on white where it was transparent, longest side <= max_side."""
    im = ImageOps.exif_transpose(Image.open(path))
    if getattr(im, "n_frames", 1) > 1:
        im.seek(0)
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        im = Image.alpha_composite(base, rgba)
    im = im.convert("RGB")
    scale = max_side / max(im.size)
    if scale < 1:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    return im


def palette(im, k=5, seed=7):
    """k dominant colours, most common first, as 0-255 RGB triples (plain k-means on a thumbnail)."""
    small = np.asarray(im.resize((48, 48), Image.BILINEAR), dtype=np.float32).reshape(-1, 3)
    rng = np.random.default_rng(seed)
    centres = small[rng.choice(len(small), k, replace=False)].copy()
    for _ in range(10):
        d = ((small[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
        nearest = d.argmin(axis=1)
        for j in range(k):
            members = small[nearest == j]
            if len(members):
                centres[j] = members.mean(axis=0)
    counts = np.bincount(nearest, minlength=k)
    order = np.argsort(-counts)
    return [[int(round(v)) for v in centres[j]] for j in order], [float(counts[j]) / len(small) for j in order]


def hexcode(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def colour_stats(im):
    mean = np.asarray(im.resize((32, 32), Image.BILINEAR), dtype=np.float32).reshape(-1, 3).mean(axis=0) / 255.0
    h, s, v = colorsys.rgb_to_hsv(*[float(x) for x in mean])
    return [round(float(x), 4) for x in mean], round(h, 4), round(s, 4), round(v, 4)


def colour_order(rows):
    """Colourful pictures first, round the hue wheel; near-greys after them, dark to light."""
    def key(r):
        if r["sat"] < 0.12:
            return (1, 0.0, r["val"])
        return (0, r["hue"], r["val"])
    return sorted(rows, key=key)


def cluster(rows, k=6, seed=7):
    """Group pictures by mean colour. Returns a cluster number for each row."""
    pts = np.array([r["mean"] for r in rows], dtype=np.float32)
    k = min(k, len(rows))
    rng = np.random.default_rng(seed)
    centres = pts[rng.choice(len(pts), k, replace=False)].copy()
    nearest = np.zeros(len(pts), dtype=int)
    for _ in range(12):
        d = ((pts[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
        nearest = d.argmin(axis=1)
        for j in range(k):
            if (nearest == j).any():
                centres[j] = pts[nearest == j].mean(axis=0)
    return [int(n) for n in nearest]


def depth_guess(im):
    """A stand-in for depth when no depth model was run: brighter and lower in frame reads as nearer.

    It is a guess, and the manifest says so (depth_source "guess"). It gives a relief
    something to push, and nothing more.
    """
    grey = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(max(im.size) / 60)), dtype=np.float32) / 255.0
    rows = np.linspace(0.0, 1.0, im.height, dtype=np.float32)[:, None]
    depth = 0.65 * grey + 0.35 * rows
    depth = (depth - depth.min()) / max(1e-6, float(depth.max() - depth.min()))
    return Image.fromarray((depth * 255).astype(np.uint8), "L")


def rough_cutout(im):
    """Key the picture against the colour of its own border. Only convincing on flat grounds."""
    a = np.asarray(im, dtype=np.float32)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    ground = np.median(edge, axis=0)
    spread = float(np.abs(edge - ground).mean())
    dist = np.sqrt(((a - ground) ** 2).sum(axis=2))
    lo = 18 + spread * 1.5
    alpha = np.clip((dist - lo) / 40.0, 0.0, 1.0)
    alpha_im = Image.fromarray((alpha * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.2))
    out = im.convert("RGBA")
    out.putalpha(alpha_im)
    return out, round(float(alpha.mean()), 4)


def square(im, side):
    return ImageOps.fit(im, (side, side), Image.LANCZOS)


def build_atlas(pictures, limit=ATLAS_LIMIT):
    n = len(pictures)
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    tile = min(256, limit // max(cols, rows))
    atlas = Image.new("RGB", (cols * tile, rows * tile), (0, 0, 0))
    for i, im in enumerate(pictures):
        atlas.paste(square(im, tile), ((i % cols) * tile, (i // cols) * tile))
    return atlas, cols, rows, tile


def _match(folder, stem, extensions):
    if not folder:
        return None
    for ext in extensions:
        hit = Path(folder) / (stem + ext)
        if hit.is_file():
            return hit
    return None


def prepare(source, out, name=None, max_side=1024, depth_from=None, cutouts_from=None, meshes_from=None, clips_from=None,
            leave_out=()):
    source, out = Path(source), Path(out)
    files = find_images(source)
    left_out = sorted(p.stem for p in files if p.stem in set(leave_out))
    files = [p for p in files if p.stem not in set(leave_out)]
    if not files:
        raise SystemExit("no images found in %s" % source)
    if max_side > ATLAS_LIMIT:
        raise SystemExit("--max above %d would not load under the Non-Commercial licence" % ATLAS_LIMIT)
    for sub in ("img", "depth", "cut", "clip"):
        folder = out / sub
        if folder.exists():
            shutil.rmtree(folder)
    for sub in ("img", "depth", "cut"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    rows, skipped = [], []
    for path in files:
        try:
            im = load(path, max_side)
        except (OSError, ValueError) as err:
            skipped.append({"source": path.name, "why": str(err)})
            continue
        colours, shares = palette(im)
        mean, hue, sat, val = colour_stats(im)
        rows.append({"source": path.name, "stem": path.stem, "im": im, "palette": colours, "shares": shares,
                     "mean": mean, "hue": hue, "sat": sat, "val": val})
    if not rows:
        raise SystemExit("none of the %d files in %s could be read" % (len(files), source))

    groups = cluster(rows)
    for r, g in zip(rows, groups):
        r["cluster"] = g
    rows = colour_order(rows)

    images = []
    for i, r in enumerate(rows):
        im = r["im"]
        tag = "%03d" % i
        im.save(out / "img" / (tag + ".jpg"), quality=92)

        given = _match(depth_from, r["stem"], (".png", ".jpg", ".exr"))
        if given and given.suffix != ".exr":
            Image.open(given).convert("L").resize(im.size, Image.BILINEAR).save(out / "depth" / (tag + ".png"))
            depth_source = "provided"
        else:
            depth_guess(im).save(out / "depth" / (tag + ".png"))
            depth_source = "guess"

        given = _match(cutouts_from, r["stem"], (".png", ".webp"))
        if given:
            cut = Image.open(given).convert("RGBA").resize(im.size, Image.LANCZOS)
            cover = round(float(np.asarray(cut)[:, :, 3].mean() / 255.0), 4)
            cutout_source = "provided"
        else:
            cut, cover = rough_cutout(im)
            cutout_source = "rough"
        cut.save(out / "cut" / (tag + ".png"))

        mesh = _match(meshes_from, r["stem"], (".glb",))
        clip = _match(clips_from, r["stem"], (".mp4", ".mov", ".webm"))
        clip_rel = None
        if clip:
            (out / "clip").mkdir(exist_ok=True)
            clip_rel = "clip/%s%s" % (tag, clip.suffix.lower())
            shutil.copyfile(clip, out / clip_rel)

        images.append({
            "id": tag,
            "source": r["source"],
            "name": r["stem"],
            "file": "img/%s.jpg" % tag,
            "width": im.width,
            "height": im.height,
            "aspect": round(im.width / im.height, 4),
            "palette": [hexcode(c) for c in r["palette"]],
            "palette_share": [round(s, 3) for s in r["shares"]],
            "mean": r["mean"],
            "hue": r["hue"],
            "sat": r["sat"],
            "val": r["val"],
            "cluster": r["cluster"],
            "depth": "depth/%s.png" % tag,
            "depth_source": depth_source,
            "cutout": "cut/%s.png" % tag,
            "cutout_source": cutout_source,
            "cutout_cover": cover,
            "mesh_source": mesh.name if mesh else None,
            "clip": clip_rel,
        })

    atlas, cols, nrows, tile = build_atlas([r["im"] for r in rows])
    atlas.save(out / "atlas.png")
    pal = np.array([r["palette"] for r in rows], dtype=np.uint8)  # (n, 5, 3): one row per picture
    Image.fromarray(pal, "RGB").save(out / "palette.png")

    head = ["id", "file", "depth", "cutout", "aspect", "r", "g", "b", "hue", "sat", "val", "cluster", "c0", "c1", "c2", "c3", "c4",
            "depth_source", "cutout_source", "cutout_cover", "name"]
    lines = ["\t".join(head)]
    for m in images:
        cells = [m["id"], m["file"], m["depth"], m["cutout"], m["aspect"], *m["mean"], m["hue"], m["sat"], m["val"], m["cluster"],
                 *m["palette"], m["depth_source"], m["cutout_source"], m["cutout_cover"], m["name"]]
        lines.append("\t".join(str(c) for c in cells))
    (out / "table.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "version": VERSION,
        "name": name or out.name,
        "count": len(images),
        "order": "colour: hue round the wheel, then near-greys dark to light",
        "max_side": max_side,
        "atlas": {"file": "atlas.png", "cols": cols, "rows": nrows, "tile": tile},
        "palette": {"file": "palette.png", "colours_per_image": 5},
        "table": "table.tsv",
        "tiers": {
            "depth": sorted({m["depth_source"] for m in images}),
            "cutout": sorted({m["cutout_source"] for m in images}),
            "meshes": sum(1 for m in images if m["mesh_source"]),
            "clips": sum(1 for m in images if m["clip"]),
        },
        "skipped": skipped,
        "left_out": left_out,
        "images": images,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", help="folder of images (it is only read)")
    ap.add_argument("--name", help="name of the set (default: the source folder's name)")
    ap.add_argument("--out", help="where to write the set (default: <repo>/image_sets/<name>)")
    ap.add_argument("--max", type=int, default=1024, dest="max_side", help="longest side of a normalised picture")
    ap.add_argument("--depth-from")
    ap.add_argument("--cutouts-from")
    ap.add_argument("--meshes-from")
    ap.add_argument("--clips-from")
    ap.add_argument("--leave-out", nargs="*", default=[], metavar="NAME")
    a = ap.parse_args(argv)
    name = a.name or Path(a.source).resolve().name
    out = Path(a.out) if a.out else Path(__file__).resolve().parents[2] / "image_sets" / name
    m = prepare(a.source, out, name, a.max_side, a.depth_from, a.cutouts_from, a.meshes_from, a.clips_from, a.leave_out)
    print("%d pictures -> %s (depth: %s, cut-outs: %s, skipped: %d)" % (
        m["count"], out.as_posix(), ",".join(m["tiers"]["depth"]), ",".join(m["tiers"]["cutout"]), len(m["skipped"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
