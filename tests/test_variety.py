"""The repetition measure: alike pictures must match, different ones must not."""

import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "measure", Path(__file__).parent.parent / "tools" / "variety" / "measure.py"
)
measure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure)

H, W = measure.H, measure.W


def _picture(kind, colour, jitter=0.0, seed=0):
    """A synthetic frame: a shape on a ground, with a little noise like a live render."""
    rng = np.random.default_rng(seed)
    f = np.full((H, W, 3), 0.05, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    if kind == "disc":
        mask = (xx - W / 2 - jitter) ** 2 + (yy - H / 2) ** 2 < (H / 3) ** 2
    elif kind == "left_bar":
        mask = xx < W / 4 + jitter
    elif kind == "stripes":
        mask = (yy // 9) % 2 == 0
    elif kind == "corner":
        mask = (xx > W * 0.6 + jitter) & (yy > H * 0.5)
    else:
        mask = np.zeros_like(xx, dtype=bool)
    f[mask] = colour
    return np.clip(f + rng.normal(0, 0.02, f.shape).astype(np.float32), 0, 1)


RED, GREEN, BLUE, CREAM = (0.9, 0.1, 0.1), (0.1, 0.8, 0.2), (0.1, 0.2, 0.9), (0.93, 0.89, 0.78)


def _clip(shots, per_shot=8):
    frames = []
    for n, (kind, colour) in enumerate(shots):
        frames += [_picture(kind, colour, jitter=k * 0.3, seed=n * 100 + k) for k in range(per_shot)]
    return np.stack(frames)


def test_one_shot_held_is_one_look():
    r = measure.measure(_clip([("disc", RED)] * 6), step=0.5, gap=8)
    assert r["distinct_looks"] == 1
    assert r["seen_before"] > 0.5


def test_different_layouts_are_different_looks():
    shots = [("disc", RED), ("left_bar", RED), ("stripes", RED), ("corner", RED)]
    r = measure.measure(_clip(shots), step=0.5, gap=8)
    assert r["distinct_looks"] == 4
    assert r["seen_before"] == 0.0


def test_same_layout_in_another_colour_is_a_different_look():
    shots = [("disc", RED), ("disc", GREEN), ("disc", BLUE), ("disc", CREAM)]
    r = measure.measure(_clip(shots), step=0.5, gap=8)
    assert r["distinct_looks"] == 4


def test_returning_to_a_shot_counts_as_seen_before():
    a, b, c = ("disc", RED), ("left_bar", GREEN), ("stripes", BLUE)
    repeating = measure.measure(_clip([a, b, c] * 4, per_shot=8), step=0.5, gap=8)
    fresh_shots = [(k, col) for k in ("disc", "left_bar", "stripes", "corner") for col in (RED, GREEN, BLUE)]
    fresh = measure.measure(_clip(fresh_shots, per_shot=8), step=0.5, gap=8)
    assert repeating["distinct_looks"] == 3
    assert repeating["seen_before"] > 0.6
    assert fresh["distinct_looks"] == 12
    assert fresh["seen_before"] == 0.0
    assert fresh["longest_new_run_s"] > repeating["longest_new_run_s"]


def test_small_motion_inside_a_shot_is_not_a_new_look():
    frames = np.stack([_picture("disc", RED, jitter=k * 0.4, seed=k) for k in range(12)])
    assert measure.measure(frames, step=0.5, gap=8)["distinct_looks"] == 1
