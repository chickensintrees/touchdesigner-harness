"""The scenes must not all show the same few objects.

On 2026-11-20 the owner found the same sixteen models, and one rubber duck in
particular, in nearly every scene. Each scene now names its own objects from a
larger catalog; these tests keep the spread.
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = sorted(p.name for p in (ROOT / "assets" / "models").iterdir() if (p / "model.obj").exists())
SHEETS = {"star_chart", "blueprint", "ticket"}  # flat printed sheets, not objects
MAX_SCENES_PER_OBJECT = 2
RETIRED = {
    "rubber_duck",  # voted out by name
    # 2026-11-20: the owner's vote on the larger catalog. Every object he disliked
    # and the three that came out badly are retired from every scene.
    "arcade_cabinet", "bowling_set", "boxing_gloves", "cowboy_boot", "football_helmet",
    "handheld_game", "joystick", "nesting_doll", "pinball_machine", "portable_tv",
    "ray_gun", "rocket", "scarecrow", "tin_robot", "ventriloquist_dummy",
    "disco_ball", "gumball_machine", "sundae",
}


def _named():
    """{scene: the pack objects its build.py names}"""
    out = {}
    for build in sorted((ROOT / "experiments").glob("sc_*/build.py")):
        text = build.read_text(encoding="utf-8")
        out[build.parent.name] = {m for m in MODELS if m not in SHEETS and re.search(r"['\"]" + re.escape(m) + r"['\"]", text)}
    return out


def test_the_detector_sees_models_at_all():
    named = _named()
    assert sum(len(v) for v in named.values()) > 60, "no scene seems to name a model: the pattern is wrong"
    assert len(MODELS) > 60


def test_no_object_is_in_more_than_two_scenes():
    uses = Counter(m for models in _named().values() for m in models)
    crowded = {m: n for m, n in uses.items() if n > MAX_SCENES_PER_OBJECT}
    assert not crowded, f"shown in too many scenes: {crowded}"


def test_retired_objects_are_in_no_scene():
    for scene, models in _named().items():
        assert not (models & RETIRED), (scene, models & RETIRED)


def test_every_object_a_scene_names_is_in_the_pack_with_its_files():
    for scene, models in _named().items():
        for m in models:
            folder = ROOT / "assets" / "models" / m
            assert (folder / "basecolor.png").exists() and json.loads((folder / "info.json").read_text(encoding="utf-8")), (scene, m)
