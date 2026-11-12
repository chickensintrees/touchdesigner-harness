"""Bake a source-time audio score (schema superworld.audio.score/1) into a
channel feed TouchDesigner can look up by track time.

    python bake_feed.py <score.json> <out_dir>

Writes <out_dir>/feed.chan (one row per sample, one column per channel, no
header: the File In CHOP's plain format) and <out_dir>/feed.json (channel
names in column order, rate, duration, tempo, section starts).

Every channel is safe to interpolate linearly: positions are monotonic
(take `% 1` in TD for a phase), envelopes are continuous, counters only step up.
Standard library only, so it runs under any Python.
"""

from __future__ import annotations

import json
import math
import sys
from bisect import bisect_right
from pathlib import Path

RATE = 100.0  # samples per second of the baked feed
STEMS = ("rms", "bass", "drums", "vocals", "other")
FAMILIES = ("low", "mid", "high")
HIT_DECAY_S = 0.14  # envelope time constant after a hit
ENERGY_WINDOW_S = 2.0

CHANNELS = (
    ["t"]
    + list(STEMS)
    + ["energy", "pitch", "pitch_conf", "bass_pitch"]
    + ["beat_pos", "bar_pos", "section", "section_pos"]
    + ["hit_" + f for f in FAMILIES]
    + ["hits_" + f for f in FAMILIES]
    + ["onset", "onsets"]
)


def _percentile(values, q):
    data = sorted(v for v in values if v is not None)
    if not data:
        return 0.0
    return data[min(len(data) - 1, int(q * (len(data) - 1) + 0.5))]


def _sample(values, step, t):
    """Linear interpolation of a regular grid stream at time t; None reads as 0."""
    if not values:
        return 0.0
    x = t / step
    i = int(x)
    if i >= len(values) - 1:
        return float(values[-1] or 0.0)
    a = float(values[i] or 0.0)
    b = float(values[i + 1] or 0.0)
    return a + (b - a) * (x - i)


def _hold(values, step, t):
    """Nearest-earlier sample (for pitch, where interpolating across gaps lies)."""
    if not values:
        return 0.0
    i = min(len(values) - 1, max(0, int(t / step + 0.5)))
    return float(values[i] or 0.0)


def _position(times, t):
    """Monotonic position through an event list: index + fraction to the next.

    Before the first event it counts up from -1 using the first interval, and
    after the last it keeps counting with the last interval, so `% 1` always
    gives a usable phase.
    """
    if not times:
        return 0.0
    if len(times) == 1:
        return max(0.0, t - times[0])
    i = bisect_right(times, t) - 1
    if i < 0:
        span = times[1] - times[0]
        return (t - times[0]) / span if span > 0 else 0.0
    if i >= len(times) - 1:
        span = times[-1] - times[-2]
        return (len(times) - 1) + ((t - times[-1]) / span if span > 0 else 0.0)
    span = times[i + 1] - times[i]
    return i + ((t - times[i]) / span if span > 0 else 0.0)


def _envelope(events, t):
    """Sum of decaying hits at time t, and how many hits have happened by t."""
    total = 0.0
    count = 0
    for when, strength in events:
        if when > t:
            break
        count += 1
        age = t - when
        if age < HIT_DECAY_S * 8:
            total += strength * math.exp(-age / HIT_DECAY_S)
    return min(total, 1.5), count


def bake(score: dict) -> tuple[list[str], list[list[float]], dict]:
    grid = score["grid"]
    step = float(grid["step_s"])
    duration = float(score["source"]["duration_s"])
    streams = score["streams"]
    events = score["events"]
    n = int(duration * RATE) + 1

    norm = {}
    for name in STEMS:
        vals = (streams.get(name) or {}).get("values") or []
        norm[name] = _percentile(vals, 0.95) or 1.0

    pitch = streams.get("pitch") or {}
    bass_pitch = streams.get("bass_pitch") or {}
    beats = [float(e["t"]) for e in events.get("beats", [])]
    bars = [float(e["t"]) for e in events.get("downbeats", [])]
    sections = [(float(e["start"]), float(e["end"])) for e in events.get("sections", [])]
    section_starts = [s for s, _ in sections]
    hits = {f: [] for f in FAMILIES}
    for e in events.get("drum_hits", []):
        if e.get("family") in hits:
            hits[e["family"]].append((float(e["t"]), float(e.get("strength", 1.0))))
    onsets = [(float(e["t"]), float(e.get("strength", 1.0))) for e in events.get("mix_onsets", [])]

    rms_vals = (streams.get("rms") or {}).get("values") or []
    half = int(ENERGY_WINDOW_S / step / 2)
    prefix = [0.0]
    for v in rms_vals:
        prefix.append(prefix[-1] + float(v or 0.0))

    def energy(t):
        if not rms_vals:
            return 0.0
        i = min(len(rms_vals) - 1, int(t / step))
        lo, hi = max(0, i - half), min(len(rms_vals), i + half + 1)
        return (prefix[hi] - prefix[lo]) / (hi - lo) / norm["rms"]

    rows = []
    for k in range(n):
        t = k / RATE
        row = [t]
        for name in STEMS:
            vals = (streams.get(name) or {}).get("values") or []
            row.append(_sample(vals, step, t) / norm[name])
        row.append(energy(t))
        row.append(_hold(pitch.get("midi") or [], step, t))
        row.append(_hold(pitch.get("confidence") or [], step, t))
        row.append(_hold(bass_pitch.get("midi") or [], step, t))
        row.append(_position(beats, t))
        row.append(_position(bars, t))
        sec = max(0, bisect_right(section_starts, t) - 1) if sections else 0
        row.append(float(sec))
        if sections:
            start, end = sections[sec]
            row.append(min(1.0, max(0.0, (t - start) / (end - start))) if end > start else 0.0)
        else:
            row.append(0.0)
        counts = []
        for f in FAMILIES:
            env, count = _envelope(hits[f], t)
            row.append(env)
            counts.append(float(count))
        row.extend(counts)
        env, count = _envelope(onsets, t)
        row.append(env)
        row.append(float(count))
        rows.append(row)

    meta = {
        "schema": "tdh.audiofeed/1",
        "channels": CHANNELS,
        "rate": RATE,
        "samples": n,
        "duration_s": duration,
        "bpm": (score.get("tempo") or {}).get("bpm"),
        "beats": len(beats),
        "bars": len(bars),
        "section_starts": section_starts,
        # The file's name only: a feed must not record a folder on the machine that baked it.
        "source": Path(str(score["source"].get("path") or "")).name,
        "score_status": score.get("status"),
    }
    return CHANNELS, rows, meta


def write(score_path, out_dir):
    score = json.loads(Path(score_path).read_text(encoding="utf-8"))
    names, rows, meta = bake(score)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "feed.chan", "w", encoding="ascii", newline="\n") as fh:
        for row in rows:
            fh.write(" ".join(f"{v:.5f}" for v in row) + "\n")
    (out / "feed.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    m = write(sys.argv[1], sys.argv[2])
    print(json.dumps({k: m[k] for k in ("samples", "duration_s", "bpm", "beats", "bars")}))
