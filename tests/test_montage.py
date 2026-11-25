"""The cut-out montage's motion, checked without TouchDesigner."""

import importlib.util
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("layouts", ROOT / "experiments" / "im_montage" / "layouts.py")
layouts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layouts)

QUIET = {"beat_pos": 8.4, "bar_pos": 2.1}
LOUD = {"beat_pos": 8.4, "bar_pos": 2.1, "hit_low": 1.0, "hit_mid": 0.8, "hit_high": 0.7, "hits_low": 5, "energy": 0.9,
        "bass": 0.9, "drums": 0.9, "vocals": 0.6, "other": 0.7}


def _flat(out):
    return [c[k] for c in out["cards"] for k in ("x", "y", "z", "s", "rz")]


def test_every_take_gives_finite_cards_inside_the_camera_range():
    for take in range(len(layouts.TAKES)):
        for feed in (QUIET, LOUD, {}):
            for age in (0.0, 0.1, 3.0):
                out = layouts.frame(take, 0.3, age, feed)
                assert len(out["cards"]) == layouts.CARDS
                assert all(math.isfinite(v) for v in _flat(out))
                assert all(c["s"] >= 0 and -30 < c["z"] < out["cam"]["z"] + 1 for c in out["cards"])
                assert 0 <= out["ground"]["mode"] < len(layouts.GROUNDS) and 0 <= out["finish"] < len(layouts.FINISHES)


def test_at_least_six_takes_and_no_two_lay_the_cards_out_alike():
    assert len(layouts.TAKES) >= 6
    seen = [_flat(layouts.frame(t, 0.3, 3.0, LOUD)) for t in range(len(layouts.TAKES))]
    for a in range(len(seen)):
        for b in range(a + 1, len(seen)):
            assert sum(abs(x - y) for x, y in zip(seen[a], seen[b], strict=True)) > 5.0, (a, b)
    assert len({(t["ground"], t["palette"]) for t in layouts.TAKES}) == len(layouts.TAKES)


def test_every_take_moves_with_the_music():
    for take in range(len(layouts.TAKES)):
        quiet, loud = layouts.frame(take, 0.3, 3.0, QUIET), layouts.frame(take, 0.3, 3.0, LOUD)
        assert sum(abs(x - y) for x, y in zip(_flat(quiet), _flat(loud), strict=True)) > 0.5, take  # a kick changes the cards
        later = layouts.frame(take, 0.3, 3.0, {**QUIET, "beat_pos": 9.4, "bar_pos": 2.35})
        assert sum(abs(x - y) for x, y in zip(_flat(quiet), _flat(later), strict=True)) > 0.5, take  # so does a beat going by
        assert loud["cam"]["z"] < quiet["cam"]["z"]  # the camera steps in on a kick


def test_a_shot_arrives_and_the_seed_changes_the_pictures():
    start, settled = layouts.frame(0, 0.3, 0.0, QUIET), layouts.frame(0, 0.3, 3.0, QUIET)
    assert start["cards"][0]["s"] < 0.6 * settled["cards"][0]["s"]
    assert [c["pic"] for c in layouts.frame(0, 0.1, 3.0, QUIET)["cards"]] != [c["pic"] for c in settled["cards"]]


def _feed(t):
    beat = t * 2.1
    return {"beat_pos": beat, "bar_pos": beat / 4.0, "hit_low": math.exp(-6.0 * (beat % 1.0)), "hit_mid": 0.4, "hit_high": 0.3,
            "hits_low": int(beat), "energy": 0.6, "bass": 0.5, "drums": 0.6, "vocals": 0.3, "other": 0.4}


def _reel(count, takes=(0, 1, 2, 3, 4, 5, 6, 7), seconds=6.0, fps=30):
    """Every picture dealt over a reel of takes, in the order it first appeared, and the worst frame's repeats."""
    state, shown, before, repeats = layouts.new_deal(), [], {}, 0
    frame = 0
    for n, take in enumerate(takes):
        seed = round((0.37 + n * 0.137) % 1.0, 3)
        for k in range(int(seconds * fps)):
            out = layouts.frame(take, seed, k / fps, _feed(frame / fps))
            pics = [c["pic"] for c in out["cards"]]
            assert len(set(pics)) == len(pics), (take, "two cards ask for the same picture number")
            dealt = layouts.deal(state, take, pics, count)
            repeats = max(repeats, len(dealt) - len(set(dealt)))
            now = dict(zip([(take, p) for p in pics], dealt, strict=True))
            shown += [pic for key, pic in now.items() if key not in before]
            before = now
            frame += 1
    return shown, repeats


def test_no_subject_comes_back_until_every_one_has_been_shown():
    for count in (37, 19, 60):
        shown, repeats = _reel(count)
        if count >= 2 * layouts.CARDS:  # a set barely larger than the cards on screen cannot always avoid it
            assert repeats == 0, "the same subject twice in one frame"
        assert len(shown) > count
        for at in range(0, len(shown) - count + 1, count):
            assert sorted(shown[at:at + count]) == list(range(count)), (count, at)
        tail = shown[len(shown) - len(shown) % count:]
        assert len(set(tail)) == len(tail)


def test_a_set_smaller_than_the_cards_still_deals():
    shown, _ = _reel(5, takes=range(2), seconds=1.0)
    assert set(shown) == set(range(5))


def test_a_held_card_keeps_its_picture():
    state = layouts.new_deal()
    first = layouts.deal(state, 0, [0, 1, 2], 37)
    assert layouts.deal(state, 0, [2, 1, 0, 9], 37)[:3] == first[::-1]
