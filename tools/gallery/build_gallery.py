"""Build the preset gallery (docs/GALLERY.md and docs/media/gallery/) from captures.

    python tools/gallery/build_gallery.py <raw_dir>

<raw_dir> is what tools/gallery/capture_td.py wrote: <scene>/take_<n>_<frame>.jpg,
_treatments/treat_<n>_00.jpg, and optionally _layers/ and _transitions/.
Each scene's words come from experiments/<scene>/preset.json:

    {"title": "...", "technique": "one sentence", "music": "what follows what",
     "takes": [{"name": "...", "description": "..."}, ...]}

For every scene this writes a contact sheet of its takes (one frame each) and a
short silent animation that plays one second of each take. Needs Pillow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "media" / "gallery"
CELL = (426, 240)
ANIM = (480, 270)
COLS = 3


def _font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _label(im, text):
    draw = ImageDraw.Draw(im)
    font = _font(15)
    w = draw.textlength(text, font=font)
    draw.rectangle((0, 0, w + 14, 24), fill=(0, 0, 0))
    draw.text((7, 3), text, fill=(255, 255, 255), font=font)
    return im


def sheet(images, labels, cell=CELL, cols=COLS):
    rows = (len(images) + cols - 1) // cols
    out = Image.new("RGB", (cell[0] * cols, cell[1] * rows), (12, 12, 12))
    for k, (im, text) in enumerate(zip(images, labels, strict=True)):
        tile = _label(im.convert("RGB").resize(cell, Image.LANCZOS), text)
        out.paste(tile, ((k % cols) * cell[0], (k // cols) * cell[1]))
    return out


def take_frames(scene_dir):
    """{take number: [frame paths in order]}"""
    takes = {}
    for f in sorted(scene_dir.glob("take_*_*.jpg")):
        _, n, _ = f.stem.split("_")
        takes.setdefault(int(n), []).append(f)
    return takes


def load_preset(slug):
    path = REPO / "experiments" / slug / "preset.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"title": slug, "technique": "", "music": "", "takes": []}


def build_scene(slug, scene_dir):
    preset = load_preset(slug)
    takes = take_frames(scene_dir)
    if not takes:
        return None
    names = []
    stills = []
    frames = []
    for n in sorted(takes):
        meta = preset["takes"][n] if n < len(preset["takes"]) else {}
        names.append("%d  %s" % (n, meta.get("name", "")))
        files = takes[n]
        stills.append(Image.open(files[len(files) // 2]))
        for f in files:
            frames.append(_label(Image.open(f).convert("RGB").resize(ANIM, Image.LANCZOS), "take %d" % n))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet(stills, names).save(OUT / (slug + "_takes.jpg"), quality=84)
    frames[0].save(OUT / (slug + ".webp"), save_all=True, append_images=frames[1:], duration=83, loop=0, quality=62, method=4)
    return preset, sorted(takes)


def build_strip(raw, folder, prefix, names, out_name, cols=4):
    src = raw / folder
    files = sorted(src.glob(prefix + "_*.jpg")) + sorted(src.glob(prefix + "_*.png"))
    if not files:
        return False
    images, labels = [], []
    for f in files:
        n = int(f.stem.split("_")[1])
        images.append(Image.open(f))
        labels.append(names[n] if n < len(names) and names[n] else "none")
    sheet(images, labels, cols=cols).save(OUT / out_name, quality=84)
    return True


def cutter_lists():
    """TREATMENTS, TRANSITIONS and LAYER_MODES as sw_cut/build.py defines them."""
    text = (REPO / "experiments" / "sw_cut" / "build.py").read_text(encoding="utf-8")
    scope = {}
    for line in text.splitlines():
        if line.startswith(("TREATMENTS", "TRANSITIONS", "LAYER_MODES")):
            exec(line, scope)  # three literal list assignments in our own file
    return scope["TREATMENTS"], scope["TRANSITIONS"], scope["LAYER_MODES"]


def main(raw_dir):
    raw = Path(raw_dir)
    treatments, transitions, layer_modes = cutter_lists()
    scenes = []
    for scene_dir in sorted(p for p in raw.iterdir() if p.is_dir() and p.name.startswith("sc_")):
        built = build_scene(scene_dir.name, scene_dir)
        if built:
            scenes.append((scene_dir.name, *built))
    has_treat = build_strip(raw, "_treatments", "treat", treatments, "treatments.jpg")
    has_layer = build_strip(raw, "_layers", "layer", layer_modes, "layers.jpg", cols=3)
    has_trans = build_strip(raw, "_transitions", "trans", transitions, "transitions.jpg")

    total = sum(len(t) for _, _, t in scenes)
    md = [
        "# Preset gallery",
        "",
        "Every picture here was captured from the running network, driven by the same music track.",
        "A **preset** is a scene, one of its takes, and optionally a treatment: %d scenes, %d takes, %d treatments."
        % (len(scenes), total, len(treatments) - 1),
        "",
        "To call one up by hand, open the `sw_cut` component's **Manual** page, turn **Cut With The Music** off, "
        "and set Scene, Take, Seed and Treatment. With it on, the cutter picks presets itself, in time with the music.",
        "",
        "| Scene | Technique | Takes |",
        "|---|---|---|",
    ]
    for slug, preset, takes in scenes:
        md.append("| [%s](#%s) | %s | %d |" % (preset["title"], slug, preset.get("technique", ""), len(takes)))
    md += ["", "## Scenes", ""]
    for slug, preset, takes in scenes:
        md += [
            '<a id="%s"></a>' % slug,
            "### %s" % preset["title"],
            "",
            "`%s` · %s" % (slug, preset.get("technique", "")),
            "",
        ]
        if preset.get("music"):
            md += ["**Follows the music:** %s" % preset["music"], ""]
        md += [
            "![%s in motion](media/gallery/%s.webp)" % (preset["title"], slug),
            "",
            "![%s takes](media/gallery/%s_takes.jpg)" % (preset["title"], slug),
            "",
        ]
        for n in takes:
            meta = preset["takes"][n] if n < len(preset["takes"]) else {}
            if meta:
                md.append("- **%d %s**: %s" % (n, meta.get("name", ""), meta.get("description", "")))
        md.append("")
    md += ["## Treatments", "", "A treatment re-sees the shot's picture for as long as the shot lasts.", ""]
    if has_treat:
        md += ["![treatments](media/gallery/treatments.jpg)", ""]
    md += ["## Layers", "", "Some shots run two scenes at once.", ""]
    if has_layer:
        md += ["![layer modes](media/gallery/layers.jpg)", ""]
    md += ["## Transitions", "", "How a shot arrives over the last one (each caught part-way through).", ""]
    if has_trans:
        md += ["![transitions](media/gallery/transitions.jpg)", ""]
    (REPO / "docs" / "GALLERY.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(json.dumps({"scenes": len(scenes), "takes": total, "treatments": has_treat, "layers": has_layer, "transitions": has_trans}))


if __name__ == "__main__":
    main(sys.argv[1])
