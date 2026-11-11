"""Measure how repetitive a recording is.

    python measure.py <video> [--step 0.5] [--gap 8] [--json out.json]

Samples a small frame every `step` seconds and describes each by coarse layout
(a 12x7 grey thumbnail, brightness-normalised) and colour (a 4x4x4 RGB histogram).
Two samples "look alike" when both descriptions are close. Reports:

- distinct_looks: how many groups of alike samples there are (greedy clustering)
- looks_per_minute: the same, per minute of video
- seen_before: the share of samples that look like some sample at least `gap`
  seconds earlier (what a viewer feels as "this again")
- longest_new_run_s: longest stretch in which every sample was new

Needs ffmpeg on PATH and numpy. The thresholds are calibrated by tests/test_variety.py
on synthetic clips: identical shots must match, different shots must not.
"""

from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np

W, H = 48, 27
# Set on the first eight-scene cut (2026-11-10): at these values its samples grouped
# into runs that matched the shots, and returns to a scene matched its earlier
# visits (18 looks, 68% seen before). Tighter values split a single moving shot.
LAYOUT_MAX = 0.20  # mean absolute difference of normalised 12x7 grey thumbnails
COLOUR_MAX = 0.50  # half the L1 distance between colour histograms (0 same, 1 disjoint)


def read_frames(video, step):
    cmd = ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{step},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255.0


def describe(frames):
    """(layout, colour) for each frame."""
    grey = frames.mean(axis=3)
    # 48x27 -> 12x7 by block mean (drop the last row of 27 to divide evenly: 24 rows / 4 is 6; use 28 -> pad)
    grey = np.concatenate([grey, grey[:, -1:, :]], axis=1)  # 28 rows
    layout = grey.reshape(len(frames), 7, 4, 12, 4).mean(axis=(2, 4)).reshape(len(frames), -1)
    spread = layout.std(axis=1, keepdims=True)
    layout = (layout - layout.mean(axis=1, keepdims=True)) / np.maximum(spread, 0.04)
    layout = layout * 0.25  # so a typical difference between unrelated images is about 0.25 to 0.35
    bins = np.minimum((frames * 4).astype(np.int32), 3)
    index = bins[..., 0] * 16 + bins[..., 1] * 4 + bins[..., 2]
    # Colour is judged on the lit pixels only: a red and a green object on the same
    # black ground share most of their pixels, and still read as different shots.
    lit = frames.max(axis=3) > 0.15
    rows = []
    for i, mask in zip(index, lit, strict=True):
        use = i[mask] if mask.mean() > 0.03 else i.ravel()
        rows.append(np.bincount(use, minlength=64))
    colour = np.stack(rows).astype(np.float32)
    colour /= colour.sum(axis=1, keepdims=True)
    return layout, colour


def alike_matrix(layout, colour):
    dl = np.abs(layout[:, None, :] - layout[None, :, :]).mean(axis=2)
    dc = np.abs(colour[:, None, :] - colour[None, :, :]).sum(axis=2) / 2
    return (dl < LAYOUT_MAX) & (dc < COLOUR_MAX)


def measure(frames, step, gap=8.0):
    layout, colour = describe(frames)
    alike = alike_matrix(layout, colour)
    n = len(frames)
    back = max(1, int(round(gap / step)))

    # Greedy clustering: a sample joins the first earlier look it resembles.
    looks = []  # representative sample index per look
    label = np.zeros(n, dtype=np.int32)
    for i in range(n):
        for k, rep in enumerate(looks):
            if alike[i, rep]:
                label[i] = k
                break
        else:
            looks.append(i)
            label[i] = len(looks) - 1

    seen = np.array([i >= back and bool(alike[i, : i - back + 1].any()) for i in range(n)])
    run = best = 0
    for s in seen:
        run = 0 if s else run + 1
        best = max(best, run)
    minutes = n * step / 60.0
    return {
        "samples": n,
        "duration_s": round(n * step, 1),
        "distinct_looks": len(looks),
        "looks_per_minute": round(len(looks) / minutes, 1) if minutes else 0.0,
        "seen_before": round(float(seen.mean()), 3) if n else 0.0,
        "longest_new_run_s": round(best * step, 1),
        "labels": label.tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--step", type=float, default=0.5)
    ap.add_argument("--gap", type=float, default=8.0)
    ap.add_argument("--json")
    a = ap.parse_args()
    result = measure(read_frames(a.video, a.step), a.step, a.gap)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh)
    print(json.dumps({k: v for k, v in result.items() if k != "labels"}))


if __name__ == "__main__":
    main()
