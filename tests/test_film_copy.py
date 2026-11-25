"""The demo film: its shot list (experiments/sw_cut/showcase.json) against its copy (film_copy.md).

The words themselves are not pinned here. What is checked is that the two files agree and that
the list has the shape the film needs.
"""

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CUT = ROOT / "experiments" / "sw_cut"
KINETIC = "sc_kinetic_type"


@pytest.fixture(scope="module")
def film():
    return json.loads((CUT / "showcase.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def kt():
    sys.modules.setdefault("td", types.ModuleType("td"))
    g = {"__name__": "film_copy"}
    exec((ROOT / "experiments" / KINETIC / "build.py").read_text(encoding="utf-8"), g)
    return g


def _texts(x):
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        x = list(x.values())
    return [t for y in x for t in _texts(y)] if isinstance(x, list) else []


def _kinetic(film):
    return [s for s in film["shots"] if s[0] == KINETIC]


def test_every_shot_names_a_scene_and_a_take(film):
    assert film["shots"]
    for shot in film["shots"]:
        assert isinstance(shot[0], str) and isinstance(shot[1], int) and len(shot) in (2, 3)
        assert len(shot) == 2 or isinstance(shot[2], dict)
        assert (ROOT / "experiments" / shot[0] / "build.py").exists(), shot[0]


def test_no_scene_follows_itself(film):
    names = [s[0] for s in film["shots"]]
    assert all(a != b for a, b in zip(names, names[1:], strict=False))


def test_the_film_opens_and_closes_on_the_copy(film):
    assert film["shots"][0][0] == KINETIC and film["shots"][-1][0] == KINETIC


def test_every_take_of_the_kinetic_type_scene_appears_once(film, kt):
    takes = [s[1] for s in _kinetic(film)]
    assert sorted(takes) == list(range(len(kt["TAKES"])))


def test_kinetic_shots_bring_every_word_their_take_shows(film, kt):
    """A take left with any of the scene's own words would show them in the film (or an asset pack's)."""
    for _scene, take, controls in _kinetic(film):
        words = controls.get("Words")
        assert isinstance(words, dict) and not controls.get("Describe"), take
        name = kt["TAKES"][take]["name"]
        needed = set(kt["TAKE_WORDS"][name])
        assert needed <= set(words), (name, needed - set(words))
        merged = kt["merge_words"](kt["DEFAULTS"], json.dumps(words))
        for key in needed:
            assert merged[key] != kt["DEFAULTS"][key], (name, key)      # the value was of a kind the scene accepts


def test_the_film_shows_only_words_from_the_copy(film, kt):
    copy = " ".join((CUT / "film_copy.md").read_text(encoding="utf-8").split())
    chars = set(kt["CHARS"]) | {" "}
    for _scene, take, controls in _kinetic(film):
        for text in _texts(controls["Words"]):
            assert text in copy, f"not in film_copy.md: {text!r} (take {take})"
            assert set(text) <= chars, f"glyphs the atlases do not hold: {text!r}"


def test_typed_lines_are_short_enough_to_be_read_in_a_shot(film, kt):
    """The typewriter and the columns type four glyphs a beat; the shortest shot is two bars."""
    beats = 4 * film["cut"]["Minbars"]
    for _scene, take, controls in _kinetic(film):
        name = kt["TAKES"][take]["name"]
        words = controls["Words"]
        if name == "typewriter":
            assert len(words["TYPE_SENT"]) <= 8 + 4 * beats - 4
        if name == "swiss columns":
            assert len(words["COLUMNS"][0]) <= 4 * beats - 4
        if name == "flash cards":
            assert len(words["FLASH_CARDS"].split()) <= beats


def test_cut_settings_name_controls_of_the_cutter(film):
    build = (CUT / "build.py").read_text(encoding="utf-8")
    for key in film["cut"]:
        assert f'"{key}"' in build, key
