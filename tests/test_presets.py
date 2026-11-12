"""Every scene of the engine carries a gallery card, and the cutter knows about it."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCENES = sorted(p for p in (ROOT / "experiments").glob("sc_*") if p.is_dir())
LISTED = json.loads((ROOT / "experiments" / "sw_cut" / "scenes.json").read_text(encoding="utf-8"))


def test_there_are_scenes():
    assert len(SCENES) >= 18


@pytest.mark.parametrize("scene", SCENES, ids=lambda p: p.name)
def test_scene_has_a_card(scene):
    card = json.loads((scene / "preset.json").read_text(encoding="utf-8"))
    assert card["title"].strip() and card["technique"].strip() and card["music"].strip()
    assert len(card["technique"].split()) <= 34
    assert len(card["takes"]) >= 6, "a scene must not look the same every time it returns"
    names = [t["name"].strip() for t in card["takes"]]
    assert all(names) and len(set(names)) == len(names)
    assert all(t["description"].strip() for t in card["takes"])


@pytest.mark.parametrize("scene", SCENES, ids=lambda p: p.name)
def test_card_is_plain_ascii_punctuation(scene):
    text = (scene / "preset.json").read_text(encoding="utf-8")
    assert not re.search("[—–‘’“”]", text)


@pytest.mark.parametrize("scene", SCENES, ids=lambda p: p.name)
def test_cutter_lists_the_scene_with_the_right_take_count(scene):
    card = json.loads((scene / "preset.json").read_text(encoding="utf-8"))
    assert scene.name in LISTED, "add the scene to experiments/sw_cut/scenes.json"
    entry = LISTED[scene.name]
    assert entry["takes"] == len(card["takes"])
    assert 0.0 <= entry["energy_min"] < entry["energy_max"]


@pytest.mark.parametrize("scene", SCENES, ids=lambda p: p.name)
def test_scene_can_be_rebuilt_and_restored(scene):
    assert (scene / "build.py").exists()
    assert (scene / (scene.name + ".tox")).exists()
    assert (scene / "captures" / "hero.png").exists()


def test_cutter_lists_no_missing_scene():
    assert set(LISTED) == {p.name for p in SCENES}
