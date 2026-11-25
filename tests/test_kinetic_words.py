"""experiments/sc_kinetic_type/build.py: the Words control lays other words over the scene's own."""

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def kt():
    sys.modules.setdefault("td", types.ModuleType("td"))   # build.py imports td; nothing here calls it
    g = {"__name__": "kinetic_words"}
    exec((ROOT / "experiments" / "sc_kinetic_type" / "build.py").read_text(encoding="utf-8"), g)
    return g


def test_blank_or_broken_words_leave_the_scene_as_it_is(kt):
    base = kt["DEFAULTS"]
    for text in ("", "   ", "not json", "[1, 2]", json.dumps({"NO_SUCH_NAME": "X"}), json.dumps({"PHRASES": "not a list"}),
                 json.dumps({"TYPE_BACK": ["a list where a text belongs"]}), json.dumps({"ECHO": [["ONE"], ["TWO"]]})):
        assert kt["merge_words"](base, text) == base, text


def test_named_words_are_replaced_and_the_rest_kept(kt):
    base = kt["DEFAULTS"]
    out = kt["merge_words"](base, json.dumps({"TYPE_BACK": "LOOK", "EXPLODE_FOOT": "A FOOTER"}))
    assert out["TYPE_BACK"] == "LOOK" and out["EXPLODE_FOOT"] == "A FOOTER"
    assert out["PHRASES"] == base["PHRASES"] and out["ECHO"] == base["ECHO"]
    assert base["TYPE_BACK"] != "LOOK"                      # the scene's own words are not touched


def test_short_forms_fill_every_layout_variant(kt):
    base, nv = kt["DEFAULTS"], kt["NV"]
    out = kt["merge_words"](base, json.dumps({
        "FLASH_CARDS": "ONE LINE", "TYPE_SENT": ["FIRST.", "SECOND."], "ACCORDION_ROWS": ["A", "B", "C"],
        "COLUMNS": ["HEADLINE", "HEADER"], "ECHO": ["TWO", "LINES"], "PHRASES": ["P1", "P2", "P3"]}))
    assert out["FLASH_CARDS"] == ["ONE LINE"] * nv
    assert out["TYPE_SENT"] == ["FIRST.", "SECOND.", "FIRST.", "SECOND."][:nv]
    assert out["ACCORDION_ROWS"] == [["A", "B", "C"]] * nv
    assert out["COLUMNS"] == [["HEADLINE", "HEADER"]] * nv
    assert len(out["ECHO"]) == nv
    for row, was in zip(out["ECHO"], base["ECHO"], strict=True):
        assert row[0] == ["TWO", "LINES"] and row[1:] == was[1:]      # each variant keeps its own placing
    assert len(out["PHRASES"]) >= kt["MIN_PHRASES"] and set(out["PHRASES"]) == {"P1", "P2", "P3"}
    assert out["PHRASES"][:3] == ["P1", "P2", "P3"] and out["PHRASES_AS_WRITTEN"] is True


def test_given_phrases_are_used_in_the_order_written(kt):
    """The scene's own pool is shuffled per take; phrases handed in by the Words control are a list to be read."""
    given = [f"LINE {i}" for i in range(12)]
    words = kt["merge_words"](kt["DEFAULTS"], json.dumps({"PHRASES": given}))
    adv = [{c: 0.6 for c in kt["CHARS"] + " "} for _ in range(kt["NF"])]
    lay = kt["Lay"](adv, [0.7] * kt["NF"], 7, None, None, words)
    assert lay.pool() == (given, list(range(12)))
    own = kt["Lay"](adv, [0.7] * kt["NF"], 7, None, None, kt["DEFAULTS"])
    assert own.pool()[1] != list(range(len(kt["DEFAULTS"]["PHRASES"])))


def test_words_are_made_settable(kt):
    """Lower case becomes capitals; a glyph the atlases do not hold becomes a space, never an error."""
    out = kt["merge_words"](kt["DEFAULTS"], json.dumps({"TYPE_BACK": "look_here", "PHRASES": ["café [x]"]}))
    assert out["TYPE_BACK"] == "LOOK HERE"
    chars = set(kt["CHARS"]) | {" "}
    assert all(c in chars for p in out["PHRASES"] for c in p)


def test_every_take_can_be_laid_out_with_merged_words(kt):
    """The layout functions accept what merge_words returns (flat advances stand in for the atlases)."""
    words = kt["merge_words"](kt["DEFAULTS"], json.dumps({
        "FLASH_CARDS": "AN AGENT BUILDS.", "PHRASES": ["ONE FACT", "ANOTHER"], "ECHO": ["LOOK."], "ACCORDION_ROWS": ["BUILD.", "LOOK."],
        "COLUMNS": ["A HEADLINE THAT IS TYPED.", "HEAD"], "EXPLODE_SENT": "EVERY STEP IS SEEN.", "TYPE_SENT": "IT LOOKS."}))
    adv = [{c: 0.6 for c in kt["CHARS"] + " "} for _ in range(kt["NF"])]
    for i, take in enumerate(kt["TAKES"]):
        assert set(kt["TAKE_WORDS"][take["name"]]) <= set(kt["DEFAULTS"])
        for v in range(kt["NV"]):
            lay = kt["Lay"](adv, [0.7] * kt["NF"], 1000 + i * 17 + v, None, None, words)
            take["fn"](lay, v)
            assert 0 < len(lay.g) <= kt["MAXG"], (take["name"], v)


def test_a_take_overfilled_by_given_words_falls_back_to_the_scenes_own(kt):
    """Given words that put more glyphs in a take than there is room for do not stop the bake: that take
    keeps the scene's own words. The scene's own words still have to fit (an assert)."""
    adv = [{c: 0.6 for c in kt["CHARS"] + " "} for _ in range(kt["NF"])]
    cap = [0.7] * kt["NF"]
    own = kt["DEFAULTS"]
    ticker = next(t for t in kt["TAKES"] if t["name"] == "ticker wall")
    solid = kt["merge_words"](own, json.dumps({"PHRASES": ["I" * 60]}))        # no spaces: every cell is a glyph

    def count(words):
        lay = kt["Lay"](adv, cap, 5, None, None, words)
        ticker["fn"](lay, 3)
        return len(lay.g)

    n_own, n_solid = count(own), count(solid)
    assert n_solid > n_own
    room = kt["MAXG"]
    kt["MAXG"] = (n_own + n_solid) // 2                                        # room for the one, not the other
    try:
        assert len(kt["lay_take"](ticker, 3, 5, adv, cap, None, False, solid, own).g) == n_own
        assert len(kt["lay_take"](ticker, 3, 5, adv, cap, None, False, own, own).g) == n_own
        kt["MAXG"] = n_own - 1
        with pytest.raises(AssertionError):
            kt["lay_take"](ticker, 3, 5, adv, cap, None, False, own, own)
    finally:
        kt["MAXG"] = room
