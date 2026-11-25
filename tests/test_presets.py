"""Every scene of the engine carries a gallery card, and the cutter knows about it."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCENES = sorted(p for p in (ROOT / "experiments").glob("sc_*") if p.is_dir())
LISTED = json.loads((ROOT / "experiments" / "sw_cut" / "scenes.json").read_text(encoding="utf-8"))


# A scene keeps at least six takes (experiments/sw_hub/SCENE_BRIEF.md) unless its owner's review removed
# takes he did not want kept; then the review wins. Scene: (takes left, date, reason).
FEWER_TAKES = {
    "sc_droste_crt": (3, "2026-11-20", "review: keep the spiral tunnel; the takes that show the desk set read as amateur 3D"),
    "sc_kifs_office": (2, "2026-11-20", "review: keep the 1-bit take and the cut; the others read as amateur 3D animation"),
    "sc_paper_storm": (3, "2026-11-20", "review: some shots look very amateur; only the full-frame paper formations are left"),
}


def test_there_are_scenes():
    assert len(SCENES) >= 16


def test_the_scenes_allowed_fewer_takes_exist_and_say_why():
    for name, (count, date, reason) in FEWER_TAKES.items():
        assert (ROOT / "experiments" / name).is_dir(), name
        assert 1 <= count < 6 and re.fullmatch(r"\d{4}-\d\d-\d\d", date) and reason.strip(), name


@pytest.mark.parametrize("scene", SCENES, ids=lambda p: p.name)
def test_scene_has_a_card(scene):
    card = json.loads((scene / "preset.json").read_text(encoding="utf-8"))
    assert card["title"].strip() and card["technique"].strip() and card["music"].strip()
    assert len(card["technique"].split()) <= 34
    if scene.name in FEWER_TAKES:
        assert len(card["takes"]) == FEWER_TAKES[scene.name][0], "update FEWER_TAKES when this scene's takes change"
    else:
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


def test_showcase_shot_list_names_real_takes_and_leaves_no_scene_out_by_accident():
    doc = json.loads((ROOT / "experiments" / "sw_cut" / "showcase.json").read_text(encoding="utf-8"))
    shots = [tuple(s[:2]) for s in doc["shots"]]      # a third item, when there is one, is the shot's controls
    for scene, take in shots:
        if scene in LISTED:
            assert 0 <= take < LISTED[scene]["takes"], (scene, take)
        else:                                         # a component that is not a scene: it must at least be buildable
            assert not scene.startswith("sc_") and (ROOT / "experiments" / scene / "build.py").exists(), scene
    assert len(set(shots)) == len(shots), "a take is listed twice"
    assert all(a[0] != b[0] for a, b in zip(shots, shots[1:], strict=False)), "the same scene twice in a row"
    left_out = set(LISTED) - {s for s, _ in shots}
    # voted down 2026-11-19: fluid ink, paper storm. Left out of the 2026-11-23 recut: light gobo (half built),
    # and shatter, droste and kifs, which were liked only in part.
    assert left_out == {"sc_fluid_ink", "sc_paper_storm", "sc_light_gobo", "sc_shatter", "sc_droste_crt", "sc_kifs_office"}, left_out
    kinetic = {t for s, t in shots if s == "sc_kinetic_type"}
    assert kinetic == set(range(LISTED["sc_kinetic_type"]["takes"])), "the anchor scene shows every take"
