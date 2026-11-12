"""The cutter's decisions, checked without TouchDesigner."""

import importlib.util
from collections import Counter
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "cutlogic", Path(__file__).parent.parent / "experiments" / "sw_cut" / "cutlogic.py"
)
cutlogic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cutlogic)

SCENES = [("quiet_a", 0.0, 0.5), ("quiet_b", 0.0, 0.5), ("any_a", 0.0, 9.0), ("loud_a", 0.6, 9.0), ("loud_b", 0.6, 9.0)]
MANY = [(f"s{i:02d}", 0.0, 9.0) for i in range(18)]
LOOKS = {
    "treatments": ["mirror", "kaleido", "rgb", "poster"],
    "transitions": ["flash", "whip", "blocks"],
    "layer_modes": ["mask", "difference"],
}
NAMES = ["t", "energy", "section", "section_pos", "bar_pos", "beat_pos"]
BAR_S, BEAT_S, FRAME_S = 2.0, 0.5, 1 / 60


def _feed(duration=60.0, section_s=8.0, energy=lambda t: 0.3):
    rows = []
    for k in range(int(duration * 100) + 1):
        t = k / 100
        rows.append([t, energy(t), float(int(t // section_s)), (t % section_s) / section_s, t / BAR_S, t / BEAT_S])
    return rows


def _wobble(t):
    """Energy dithering around the loud threshold several times a bar."""
    return 0.75 + 0.05 * ((t * 7.3) % 1 - 0.5)


def _gaps(shots):
    return [b[0] - a[0] for a, b in zip(shots, shots[1:], strict=False)]


def test_first_frame_shows_a_scene():
    state = cutlogic.new_state()
    feed = {"energy": 0.3, "section": 0, "section_pos": 0.0, "bar_i": 0, "bar": 0.0, "beat_i": 0}
    assert cutlogic.step(state, feed, SCENES)
    assert state["scene"] in [n for n, _, _ in SCENES]


def test_quiet_track_cuts_once_per_section_on_the_next_beat():
    shots, _ = cutlogic.simulate(_feed(), NAMES, SCENES)
    assert [round(s[0], 1) for s in shots] == [0.0, 8.5, 16.5, 24.5, 32.5, 40.5, 48.5, 56.5]


def test_loud_passage_cuts_every_two_bars():
    shots, _ = cutlogic.simulate(_feed(energy=lambda t: 0.9), NAMES, SCENES)
    assert {round(g, 1) for g in _gaps(shots[1:])} == {4.0}


def test_cuts_land_on_beat_lines():
    for energy in (lambda t: 0.3, lambda t: 0.9, _wobble):
        shots, _ = cutlogic.simulate(_feed(energy=energy), NAMES, SCENES)
        late = [s[0] for s in shots[1:] if (s[0] % BEAT_S) > FRAME_S + 1e-6]
        assert late == []


def test_energy_wobble_cannot_make_a_short_shot():
    shots, cold = cutlogic.simulate(_feed(duration=120, energy=_wobble), NAMES, SCENES)
    assert min(_gaps(shots)) >= BAR_S - 1e-6  # min_bars is 1
    assert cold == []


def test_scene_fits_the_energy():
    quiet, _ = cutlogic.simulate(_feed(energy=lambda t: 0.3), NAMES, SCENES)
    loud, _ = cutlogic.simulate(_feed(energy=lambda t: 0.9), NAMES, SCENES)
    assert {s[1] for s in quiet} <= {"quiet_a", "quiet_b", "any_a"}
    assert {s[1] for s in loud} <= {"loud_a", "loud_b", "any_a"}


def test_never_repeats_within_two_cuts():
    for energy in (0.3, 0.9):
        shots, _ = cutlogic.simulate(_feed(duration=200, energy=lambda t, e=energy: e), NAMES, SCENES)
        seq = [s[1] for s in shots]
        assert all(seq[i] != seq[i - 1] and seq[i] != seq[i - 2] for i in range(2, len(seq)))


def test_every_cut_was_warmed_up():
    for energy in (lambda t: 0.3, lambda t: 0.9, _wobble):
        _, cold = cutlogic.simulate(_feed(energy=energy), NAMES, SCENES)
        assert cold == []


def test_same_track_gives_same_cuts():
    assert cutlogic.simulate(_feed(), NAMES, SCENES, LOOKS) == cutlogic.simulate(_feed(), NAMES, SCENES, LOOKS)


def test_min_bars_holds_a_shot():
    rows = _feed(section_s=1.0)  # a section change every half bar
    shots, _ = cutlogic.simulate(rows, NAMES, SCENES, {"min_bars": 2})
    assert min(_gaps(shots)) >= 2 * BAR_S - 1e-6


def test_single_scene_never_crashes():
    shots, _ = cutlogic.simulate(_feed(), NAMES, [("only", 0.0, 9.0)])
    assert {s[1] for s in shots} == {"only"}


# --- variety -----------------------------------------------------------------


def test_every_scene_is_used_before_any_returns():
    shots, _ = cutlogic.simulate(_feed(duration=400, energy=lambda t: 0.9), NAMES, MANY)
    seq = [s[1] for s in shots]
    assert len(seq) >= 2 * len(MANY)
    assert sorted(seq[: len(MANY)]) == sorted(n for n, _, _ in MANY)
    # ...and afterwards a scene only comes back once nearly all the others have been on
    for i in range(len(MANY), len(seq)):
        assert seq[i] not in seq[i - (len(MANY) - 3) : i], (i, seq[i])


def test_takes_count_up_per_scene():
    shots, _ = cutlogic.simulate(_feed(duration=400, energy=lambda t: 0.9), NAMES, SCENES)
    seen = Counter()
    for _, scene, plan in shots:
        assert plan["take"] == seen[scene]
        seen[scene] += 1
    assert max(seen.values()) >= 5


def test_shots_get_varied_looks():
    shots, _ = cutlogic.simulate(_feed(duration=400, energy=lambda t: 0.9), NAMES, MANY, LOOKS)
    plans = [p for _, _, p in shots]
    treats = Counter(p["treat"] for p in plans)
    trans = Counter(p["trans"] for p in plans)
    assert set(treats) == set(LOOKS["treatments"]) | {""}
    assert set(trans) == set(LOOKS["transitions"]) | {"cut"}
    assert 0.3 < treats[""] / len(plans) < 0.8  # most shots are clean, a good share are not
    assert any(p["layer"] for p in plans)
    assert all(p["layer"] != s for _, s, p in shots)


def test_a_look_is_never_used_twice_running():
    shots, _ = cutlogic.simulate(_feed(duration=400, energy=lambda t: 0.9), NAMES, MANY, LOOKS)
    plans = [p for _, _, p in shots]
    for a, b in zip(plans, plans[1:], strict=False):
        assert not (a["treat"] and a["treat"] == b["treat"])
        assert not (a["trans"] != "cut" and a["trans"] == b["trans"])


def test_the_warmed_scene_already_knows_its_plan():
    state = cutlogic.new_state()
    rows = _feed()
    announced = None
    for k in range(0, len(rows), 2):
        t, energy, section, section_pos, bar_pos, beat_pos = rows[k]
        feed = {"energy": energy, "section": section, "section_pos": section_pos,
                "bar_i": int(bar_pos), "bar": bar_pos % 1, "beat_i": int(beat_pos)}  # fmt: skip
        was = (state["next"], state["next_plan"])
        if cutlogic.step(state, feed, SCENES, LOOKS) and was[0]:
            announced = was
            assert state["scene"] == was[0] and state["shot"] == was[1]
    assert announced is not None


def test_cutting_carries_on_after_the_track_loops():
    shots, _ = cutlogic.simulate(_feed(), NAMES, SCENES, loops=3)
    per_loop = Counter(int(s[0] // 60.0) for s in shots)
    assert per_loop[0] >= 7 and per_loop[1] >= 7 and per_loop[2] >= 7


# ---- quiet passages: a long section is not one long shot ----------------------


def test_quiet_sections_are_split_every_bars_quiet_bars():
    # 24 s sections of 2 s bars: with bars_quiet 4 a shot is at most 8 s, plus the beat it waits for
    rows = _feed(duration=96.0, section_s=24.0)
    shots, cold = cutlogic.simulate(rows, NAMES, MANY, {"bars_quiet": 4})
    gaps = _gaps(shots)
    assert max(gaps) <= 8.5 + 1e-6, gaps
    assert min(gaps) >= 2.0 - 1e-6, gaps  # never shorter than the shortest shot (one bar)
    assert not cold


def test_bars_quiet_zero_keeps_one_shot_per_section():
    rows = _feed(duration=96.0, section_s=24.0)
    shots, _ = cutlogic.simulate(rows, NAMES, MANY, {"bars_quiet": 0})
    assert len(shots) == 4 and max(_gaps(shots)) >= 23.9


def test_no_quiet_cut_just_before_a_section_ends():
    # 18 s sections: the bar grid would cut at 16 s, two seconds before the section's own cut
    rows = _feed(duration=72.0, section_s=18.0)
    shots, _ = cutlogic.simulate(rows, NAMES, MANY, {"bars_quiet": 4})
    in_section = sorted({round(s[0] % 18.0, 1) for s in shots})
    assert all(t <= 0.75 * 18.0 + 0.5 for t in in_section), in_section


def test_bars_quiet_keeps_the_loud_grid_and_adds_a_cut_where_the_music_turns_loud():
    loud = _feed(energy=lambda t: 0.9)
    a, _ = cutlogic.simulate(loud, NAMES, SCENES, {"bars_quiet": 0})
    b, _ = cutlogic.simulate(loud, NAMES, SCENES, {"bars_quiet": 4})
    # loudness is decided at the first bar line, so the one extra cut is on the beat after it
    assert {s[0] for s in b} - {s[0] for s in a} == {2.5}
    assert {s[0] for s in a} <= {s[0] for s in b}
