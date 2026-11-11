"""bake_feed turns an audio score into channels that survive linear interpolation."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "bake_feed", Path(__file__).parent.parent / "tools" / "audiofeed" / "bake_feed.py"
)
bake_feed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bake_feed)


def _score():
    n = 500  # 10 s at the score's 50 Hz grid
    ramp = [i / n for i in range(n)]
    return {
        "source": {"duration_s": 10.0, "path": "x.wav"},
        "grid": {"start_s": 0.0, "step_s": 0.02, "count": n},
        "streams": {
            "rms": {"values": ramp},
            "bass": {"values": ramp},
            "drums": {"values": None},
            "vocals": {"values": ramp},
            "other": {"values": ramp},
            "pitch": {"midi": [None] * 250 + [60.0] * 250, "confidence": [0.0] * 250 + [0.9] * 250},
        },
        "events": {
            "beats": [{"t": 1.0 + 0.5 * i} for i in range(16)],
            "downbeats": [{"t": 1.0 + 2.0 * i} for i in range(4)],
            "sections": [{"start": 0.0, "end": 4.0}, {"start": 4.0, "end": 10.0}],
            "drum_hits": [{"t": 2.0, "strength": 1.0, "family": "low"}, {"t": 3.0, "strength": 0.5, "family": "high"}],
            "mix_onsets": [{"t": 2.0, "strength": 1.0}],
        },
        "tempo": {"bpm": 120.0},
    }


def _col(names, rows, name):
    i = names.index(name)
    return [r[i] for r in rows]


def test_shape_and_names():
    names, rows, meta = bake_feed.bake(_score())
    assert names == meta["channels"]
    assert len(rows) == meta["samples"] == 1001
    assert all(len(r) == len(names) for r in rows)
    assert _col(names, rows, "t")[100] == 1.0


def test_positions_never_go_backwards():
    names, rows, _ = bake_feed.bake(_score())
    for name in ("beat_pos", "bar_pos", "hits_low", "hits_high", "onsets", "section"):
        col = _col(names, rows, name)
        assert all(b >= a for a, b in zip(col, col[1:], strict=False)), name


def test_beat_pos_lands_on_beats():
    names, rows, _ = bake_feed.bake(_score())
    beat = _col(names, rows, "beat_pos")
    assert abs(beat[100] - 0.0) < 1e-6  # first beat at 1.0 s
    assert abs(beat[150] - 1.0) < 1e-6  # second at 1.5 s
    assert abs(beat[125] - 0.5) < 1e-6
    assert beat[0] < 0  # counts up to the first beat


def test_hit_envelope_and_counter():
    names, rows, _ = bake_feed.bake(_score())
    env, count = _col(names, rows, "hit_low"), _col(names, rows, "hits_low")
    assert env[199] == 0.0 and count[199] == 0.0
    assert env[200] == 1.0 and count[200] == 1.0
    assert 0.0 < env[220] < env[200]
    assert _col(names, rows, "hit_high")[300] == 0.5


def test_missing_stem_and_unvoiced_pitch_read_zero():
    names, rows, _ = bake_feed.bake(_score())
    assert max(_col(names, rows, "drums")) == 0.0
    pitch = _col(names, rows, "pitch")
    assert pitch[100] == 0.0 and pitch[900] == 60.0


def test_stems_are_normalised_to_their_own_loudness():
    names, rows, _ = bake_feed.bake(_score())
    assert 0.95 < max(_col(names, rows, "rms")) < 1.1


def test_section_pos_runs_zero_to_one():
    names, rows, _ = bake_feed.bake(_score())
    sec, pos = _col(names, rows, "section"), _col(names, rows, "section_pos")
    assert sec[399] == 0.0 and sec[400] == 1.0
    assert pos[400] == 0.0 and abs(pos[200] - 0.5) < 1e-6


def test_write_round_trip(tmp_path):
    import json

    src = tmp_path / "score.json"
    src.write_text(json.dumps(_score()), encoding="utf-8")
    meta = bake_feed.write(src, tmp_path / "out")
    lines = (tmp_path / "out" / "feed.chan").read_text().splitlines()
    assert len(lines) == meta["samples"]
    assert len(lines[0].split()) == len(meta["channels"])
