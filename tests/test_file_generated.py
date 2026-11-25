"""tools/assets/file_generated.py: rooms and footage filed in the asset pack."""

import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("file_generated", ROOT / "tools" / "assets" / "file_generated.py")
fg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fg)

QUAD = [(471.3, 187.7), (1056.0, 188.1), (1040.0, 633.9), (480.5, 640.2)]


def _apply(h, x, y):
    s, t, w = np.array(h).reshape(3, 3) @ np.array([x, y, 1.0])
    return s / w, t / w


def test_homography_puts_the_corners_on_the_unit_square():
    h = fg.homography(QUAD)
    for (x, y), want in zip(QUAD, [(0, 0), (1, 0), (1, 1), (0, 1)], strict=True):
        assert np.allclose(_apply(h, x, y), want, atol=1e-5)
    cx, cy = np.mean(QUAD, axis=0)
    s, t = _apply(h, cx, cy)
    assert 0.4 < s < 0.6 and 0.4 < t < 0.6


def test_fill_holes_closes_islands_but_not_the_outside():
    a = np.zeros((40, 60), dtype=np.uint8)
    a[10:30, 10:50] = 255
    a[15:20, 20:25] = 0  # a hole in the glass
    out = np.asarray(fg.fill_holes(Image.fromarray(a, "L")))
    assert out[17, 22] == 255 and out[2, 2] == 0 and out[35, 55] == 0 and out[12, 12] == 255


def test_rooms_are_filed_within_the_size_limit(tmp_path):
    src = tmp_path / "rooms"
    (src / "mask").mkdir(parents=True)
    Image.new("RGB", (1536, 864), (90, 60, 40)).save(src / "den.png")
    Image.new("L", (1536, 864), 0).save(src / "mask" / "den.png")
    (src / "den.json").write_text(json.dumps({"corners": [[400, 200], [1100, 200], [1100, 650], [400, 650]]}), encoding="utf-8")
    rooms = fg.file_rooms(src, tmp_path / "pack")
    assert [r["name"] for r in rooms] == ["den"]
    assert Image.open(tmp_path / "pack" / "rooms" / "den.png").size == (1280, 720)
    assert Image.open(tmp_path / "pack" / "rooms" / "mask" / "den.png").size == (1280, 720)
    index = json.loads((tmp_path / "pack" / "rooms" / "rooms.json").read_text(encoding="utf-8"))
    r = index["rooms"][0]
    assert np.allclose(_apply(r["to_screen"], *r["corners"][2]), (1, 1), atol=1e-5)
    assert abs(r["aspect"] - 700 / 450) < 0.01 and np.allclose(r["centre"], (750 / 1536, 425 / 864), atol=1e-4)
    head, row = (tmp_path / "pack" / "rooms" / "rooms.tsv").read_text(encoding="utf-8").splitlines()
    assert head.split("\t")[:6] == ["name", "file", "mask", "cx", "cy", "aspect"] and len(row.split("\t")) == 16
    assert fg.file_rooms(src, tmp_path / "pack2", leave_out=["den"]) == []
