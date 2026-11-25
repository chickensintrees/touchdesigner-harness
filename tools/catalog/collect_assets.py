"""Gather the assets of one or more packs into a catalog folder, so each can be voted on.

    python tools/catalog/collect_assets.py <catalog folder> "Shipped pack=assets" ["My pack=<folder>" ...]
        [--objects <objects.json> --concepts <folder of <name>.png> --objects-label "New objects"]
        [--images "Reference set=<prepared image set folder>"]
        [--previews <folder of <model name>*.jpg|png>]

Writes <catalog>/assets.json (read by build_catalog.py) and copies small pictures and
sound into <catalog>/assets/. Tabs: Models, Sheets and lettering, Fonts, Music, Image
sets. Inside a tab each pack is a section; models whose info.json has a "group" are grouped
by it, and proposed objects are grouped by family.
A pack is laid out as assets/README.md describes: models/<name>/, sheets/, art/, fonts/,
music/ and feeds/<track>/feed.json.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
THUMB = 480


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def thumb(src, dst, flatten=(238, 236, 230)):
    """A small JPEG of a picture; transparent pictures are laid on a plain ground."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        ground = Image.new("RGBA", im.size, flatten + (255,))
        im = Image.alpha_composite(ground, im)
    im = im.convert("RGB")
    im.thumbnail((THUMB, THUMB))
    im.save(dst, quality=85)


def specimen(font, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (THUMB, THUMB), (246, 244, 239))
    d = ImageDraw.Draw(im)
    y = 24
    for size, text in ((92, "Aa Rg"), (44, "HAMBURGEFONS"), (30, "0123456789 !?&"), (22, "The quick brown fox jumps"), (22, "over the lazy dog.")):
        d.text((24, y), text, font=ImageFont.truetype(str(font), size), fill=(27, 26, 23))
        y += int(size * 1.35)
    im.save(dst, quality=88)


def preview_for(name, folders):
    for folder in folders:
        hits = sorted(p for p in Path(folder).glob(name + "*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") and p.is_file())
        if hits:
            return hits[0]
    return None


def collect(folder, packs, objects=None, concepts=None, objects_label="New objects", images=(), previews=()):
    folder = Path(folder)
    items = []
    for label, pack in packs:
        pack = Path(pack) if Path(pack).is_absolute() else REPO / pack
        key = slug(label)
        for model in sorted(p for p in (pack / "models").glob("*") if (p / "model.obj").exists() or (p / "info.json").exists()):
            info = json.loads((model / "info.json").read_text(encoding="utf-8")) if (model / "info.json").exists() else {}
            src = preview_for(model.name, previews) or (model / "basecolor.png" if (model / "basecolor.png").exists() else None)
            rel = f"assets/{key}/models/{model.name}.jpg"
            if src:
                thumb(src, folder / rel)
            text = info.get("prompt", "")
            if info.get("triangles"):
                text = (text + " " if text else "") + f"({info['triangles']:,} triangles)"
            items.append({"id": f"model:{key}:{model.name}", "title": model.name.replace("_", " "), "text": text,
                          "tab": "Models", "section": f"{label}: {info['group']}" if info.get("group") else label, "image": rel if src else ""})
        for sub, section in (("sheets", "sheets"), ("art", "lettering and marks")):
            for pic in sorted((pack / sub).rglob("*.png")) if (pack / sub).is_dir() else []:
                if pic.stem.endswith("_alpha"):
                    continue  # the alpha half of a pair; its colour half is shown
                rel = f"assets/{key}/{sub}/{pic.stem}.jpg"
                thumb(pic, folder / rel)
                items.append({"id": f"{sub}:{key}:{pic.stem}", "title": pic.stem.replace("_", " "), "text": "",
                              "tab": "Sheets and lettering", "section": f"{label}: {section}", "image": rel})
        for font in sorted((pack / "fonts").glob("*.[to]tf")) if (pack / "fonts").is_dir() else []:
            rel = f"assets/{key}/fonts/{font.stem}.jpg"
            specimen(font, folder / rel)
            items.append({"id": f"font:{key}:{font.stem}", "title": font.stem, "text": "", "tab": "Fonts", "section": label, "image": rel})
        for track in sorted(p for p in (pack / "music").glob("*") if p.suffix.lower() in (".wav", ".mp3", ".flac")) if (pack / "music").is_dir() else []:
            rel = f"assets/{key}/music/{track.stem}.mp3"
            dst = folder / rel
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(track), "-vn", "-c:a", "libmp3lame", "-b:a", "128k", str(dst)], check=True)
            feed = pack / "feeds" / track.stem / "feed.json"
            text, title = "No analysis yet: scenes cannot follow it.", track.stem
            if feed.exists():
                meta = json.loads(feed.read_text(encoding="utf-8"))
                title = Path(str(meta.get("source") or track.stem)).stem
                text = f"{meta['duration_s'] // 60:.0f}:{meta['duration_s'] % 60:02.0f}, {meta.get('bpm', 0):.0f} bpm by the analysis, {meta.get('bars', 0)} bars."
            items.append({"id": f"music:{key}:{track.stem}", "title": title, "text": text, "tab": "Music", "section": label, "audio": rel})
    if objects:
        for obj in json.loads(Path(objects).read_text(encoding="utf-8")):
            src = preview_for(obj["name"], [concepts] if concepts else [])
            rel = f"assets/{slug(objects_label)}/{obj['name']}.jpg"
            if src:
                thumb(src, folder / rel)
            items.append({"id": f"model:{slug(objects_label)}:{obj['name']}", "title": obj["name"].replace("_", " "), "text": obj.get("prompt", ""),
                          "tab": "Models", "section": f"{objects_label}: {obj.get('group', 'other')}", "image": rel if src else ""})
    for label, images_folder in images:
        images_folder = Path(images_folder) if Path(images_folder).is_absolute() else REPO / images_folder
        for pic in sorted((images_folder / "img").glob("*")):
            rel = f"assets/{slug(label)}/{pic.stem}.jpg"
            thumb(pic, folder / rel)
            items.append({"id": f"image:{slug(label)}:{pic.stem}", "title": f"picture {pic.stem}", "text": "", "tab": "Image sets", "section": label, "image": rel})
    (folder / "assets.json").write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    return items


def _pair(text):
    label, _, path = text.partition("=")
    return label.strip(), path.strip()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder")
    ap.add_argument("packs", nargs="*", type=_pair)
    ap.add_argument("--objects")
    ap.add_argument("--concepts")
    ap.add_argument("--objects-label", default="New objects")
    ap.add_argument("--images", action="append", type=_pair, default=[])
    ap.add_argument("--previews", action="append", default=[])
    a = ap.parse_args()
    found = collect(a.folder, a.packs, a.objects, a.concepts, a.objects_label, a.images, a.previews)
    tabs = {}
    for item in found:
        tabs[item["tab"]] = tabs.get(item["tab"], 0) + 1
    print(len(found), "assets:", tabs)
