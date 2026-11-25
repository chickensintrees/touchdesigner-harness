"""tools/imageprep/prepare.py: a folder of pictures becomes a prepared set with a manifest."""

import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare", ROOT / "tools" / "imageprep" / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

COLOURS = {"blue": (20, 40, 220), "red": (230, 30, 20), "grey_dark": (40, 40, 40), "green": (30, 200, 60), "grey_light": (210, 210, 210)}


@pytest.fixture()
def source(tmp_path):
    folder = tmp_path / "client"
    folder.mkdir()
    for i, (name, rgb) in enumerate(COLOURS.items()):
        size = (300 + 200 * i, 400)  # mixed shapes, like a real folder
        Image.new("RGB", size, rgb).save(folder / (name + (".png" if i % 2 else ".jpg")))
    # one big picture, one with a subject on a flat ground, one file that is not a picture
    Image.new("RGB", (3000, 1500), (240, 200, 0)).save(folder / "yellow_big.jpg")
    subject = Image.new("RGB", (400, 400), (250, 120, 160))
    subject.paste((10, 10, 10), (150, 150, 250, 250))
    subject.save(folder / "pink_subject.png")
    (folder / "notes.txt").write_text("not a picture", encoding="utf-8")
    (folder / "broken.jpg").write_bytes(b"not really a jpeg")
    return folder


def test_every_picture_is_listed_with_its_files(source, tmp_path):
    out = tmp_path / "set"
    m = prepare.prepare(source, out)
    assert m["count"] == 7
    assert [s["source"] for s in m["skipped"]] == ["broken.jpg"]
    on_disk = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == m
    for im in m["images"]:
        for key in ("file", "depth", "cutout"):
            assert (out / im[key]).is_file(), (im["source"], key)
        w, h = Image.open(out / im["file"]).size
        assert (w, h) == (im["width"], im["height"])
        assert max(w, h) <= 1024
        assert Image.open(out / im["depth"]).size == (w, h)
        assert Image.open(out / im["cutout"]).mode == "RGBA"
        assert len(im["palette"]) == 5


def test_order_is_by_colour_with_greys_last(source, tmp_path):
    m = prepare.prepare(source, tmp_path / "set")
    names = [im["source"].split(".")[0] for im in m["images"]]
    assert names[-2:] == ["grey_dark", "grey_light"]
    hues = [im["hue"] for im in m["images"][:-2]]
    assert hues == sorted(hues)
    assert names[0] == "red"


def test_palette_finds_the_dominant_colour(source, tmp_path):
    m = prepare.prepare(source, tmp_path / "set")
    by = {im["source"]: im for im in m["images"]}
    r, g, b = (int(by["red.png"]["palette"][0][i : i + 2], 16) for i in (1, 3, 5))
    assert r > 200 and g < 60 and b < 60
    subject = by["pink_subject.png"]
    assert subject["palette_share"][0] > 0.8  # the ground dominates


def test_atlas_and_table_fit_touchdesigner(source, tmp_path):
    out = tmp_path / "set"
    m = prepare.prepare(source, out)
    atlas = Image.open(out / "atlas.png")
    a = m["atlas"]
    assert atlas.size == (a["cols"] * a["tile"], a["rows"] * a["tile"])
    assert max(atlas.size) <= 1280
    assert a["cols"] * a["rows"] >= m["count"]
    # the first tile is the first picture in colour order (red)
    r, g, b = atlas.getpixel((a["tile"] // 2, a["tile"] // 2))
    assert r > 200 and g < 70
    assert Image.open(out / "palette.png").size == (5, m["count"])
    rows = (out / "table.tsv").read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == m["count"] + 1
    assert rows[0].split("\t")[:4] == ["id", "file", "depth", "cutout"]


def test_rough_cutout_keeps_the_subject_and_drops_the_ground(source, tmp_path):
    out = tmp_path / "set"
    m = prepare.prepare(source, out)
    im = next(i for i in m["images"] if i["source"] == "pink_subject.png")
    assert im["cutout_source"] == "rough"
    alpha = np.asarray(Image.open(out / im["cutout"]))[:, :, 3]
    assert alpha[200, 200] > 240  # the dark square
    assert alpha[20, 20] < 15  # the pink ground


def test_provided_depth_and_cutouts_replace_the_guesses(source, tmp_path):
    depth = tmp_path / "depth_in"
    cuts = tmp_path / "cut_in"
    depth.mkdir()
    cuts.mkdir()
    Image.new("L", (64, 64), 200).save(depth / "red.png")
    Image.new("RGBA", (64, 64), (255, 0, 0, 128)).save(cuts / "red.png")
    out = tmp_path / "set"
    m = prepare.prepare(source, out, depth_from=depth, cutouts_from=cuts)
    by = {im["source"]: im for im in m["images"]}
    assert by["red.png"]["depth_source"] == "provided"
    assert by["red.png"]["cutout_source"] == "provided"
    assert by["blue.jpg"]["depth_source"] == "guess"
    assert Image.open(out / by["red.png"]["depth"]).getpixel((5, 5)) == 200
    assert m["tiers"]["depth"] == ["guess", "provided"]


def test_running_twice_gives_the_same_set(source, tmp_path):
    a = prepare.prepare(source, tmp_path / "a")
    b = prepare.prepare(source, tmp_path / "a")
    assert a == b


def test_image_folders_are_never_committed():
    for folder in ("image_sources/x.jpg", "image_sets/x/manifest.json"):
        r = subprocess.run(["git", "check-ignore", "-q", folder], cwd=ROOT)
        assert r.returncode == 0, folder + " is not ignored by git"


def test_left_out_pictures_are_skipped_and_named(source, tmp_path):
    m = prepare.prepare(source, tmp_path / "set", leave_out=["red", "not_there"])
    assert m["count"] == 6
    assert m["left_out"] == ["red"]
    assert "red" not in [im["name"] for im in m["images"]]
    head, first = (tmp_path / "set" / "table.tsv").read_text(encoding="utf-8").splitlines()[:2]
    assert head.split("\t")[-1] == "name" and first.split("\t")[-1] == m["images"][0]["name"]
