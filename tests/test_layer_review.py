"""The layer review film's drawing, checked without TouchDesigner and without a project."""

import importlib.util
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("layer_review", Path(__file__).parent.parent / "tools" / "review" / "layer_review.py")
lr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lr)

N = 48


def spec(panels=3):
    s = lr.spec_example()
    s["panels"] = s["panels"][:panels] if panels == 3 else [s["panels"][0], s["panels"][2]]
    s["captions"] = [[f"shot {f // 24 + 1}" for f in range(N)]] + [[""] * N] * (panels - 1)
    return s


def pictures(panels=3):
    """Flat grey panels, each a different shade, so a pasted panel can be found in the frame."""
    return [[np.full((72, 128, 3), 40 + 60 * i, np.uint8) for _ in range(N)] for i in range(panels)]


def arr(im):
    return np.asarray(im).astype(int)


@pytest.mark.parametrize("panels", [2, 3])
def test_every_panel_is_on_screen_at_sixteen_by_nine(panels):
    im = arr(lr.frame_image(spec(panels), pictures(panels), 0))
    assert im.shape == (lr.H, lr.W, 3)
    lay = lr.layout(panels)
    assert abs(lay["pw"] / lay["ph"] - 16 / 9) < 0.01
    for i, x in enumerate(lay["xs"]):
        mid = im[lay["top"] + lay["ph"] // 2, x + lay["pw"] // 2]
        assert tuple(mid) == (40 + 60 * i,) * 3, f"panel {i} is not where the layout says"
    assert lay["timeline"][1] >= lay["now_y"] + 30 + lr.ROWS * 38, "the rows and the timeline must not overlap"


def test_the_playhead_moves_with_the_frame():
    s, p = spec(), pictures()
    x0, y0, x1, y1 = lr.layout(3)["timeline"]

    def playhead(f):
        row = arr(lr.frame_image(s, p, f))[y1 - 2, x0:x1 + 4]
        return int(np.argmax((row == 255).all(axis=1)))

    a, b = playhead(6), playhead(30)
    assert 0 < a < b
    assert abs((b - a) - (x1 - x0) * 24 / N) <= 3


def test_an_event_is_listed_on_its_frame_and_not_before():
    s, p = spec(), pictures()
    lay = lr.layout(3)
    rows = slice(lay["now_y"] + 22, lay["now_y"] + 24 + lr.ROWS * 38)

    def ink(f):
        return int((arr(lr.frame_image(s, p, f))[rows, 30:1900].max(axis=2) > 200).sum())

    assert ink(5) == 0, "nothing is live before the first event"
    assert ink(11) > 500, "the title is listed from its first frame"
    assert ink(24) > ink(23), "the cut and the accent join it on their frame"


def test_what_is_live_and_in_what_order():
    s = spec()
    assert [e["name"] for e, _ in lr.live_events(s, 5)] == []
    assert [e["name"] for e, _ in lr.live_events(s, 12)] == ["TITLE"]
    assert [e["name"] for e, _ in lr.live_events(s, 24)] == ["CUT", "ACCENT"], "the span has ended; quiet events are listed last"
    assert [e["name"] for e, _ in lr.live_events(s, 33)] == ["CUT"], "an accent's row is short-lived; an instant lingers"
    assert [e["name"] for e, _ in lr.live_events(s, 24 + lr.LINGER)] == []


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="needs ffmpeg")
def test_the_film_plays_twice_the_second_time_at_half_speed(tmp_path):
    s = spec()
    s.pop("audio")
    s["out"] = str(tmp_path / "review.mp4")
    out = lr.render(s, pictures())
    got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,width,height",
                          "-of", "csv=p=0", str(out)], capture_output=True, text=True, check=True).stdout.strip()
    assert got == f"{lr.W},{lr.H},{N * 3}"
