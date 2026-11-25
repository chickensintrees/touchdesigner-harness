"""Nothing plays out loud unless a person turned it up (AGENTS.md rule 17).

An Audio Device Out CHOP is created at full volume. On 2026-11-20 one left that
way in an old experiment played through the user's speakers for an hour of
unrelated work. These tests keep it from happening again.
"""

import json
from pathlib import Path

import fake_td
import tdh

ROOT = Path(__file__).resolve().parents[1]
P = fake_td.Par


def _speaker(td, name, volume=1.0, mode=fake_td.ParMode.CONSTANT, active=True):
    return fake_td.CHOP(td._registry, "/project1/" + name, "audiodeviceoutCHOP",
                        pars=[P("volume", volume, default=1.0, mode=mode, expr="parent().par.Volume"), P("active", active, default=True)])


def test_a_speaker_left_at_its_default_volume_is_a_fault(td):
    _speaker(td, "dropped_in")                                          # as TouchDesigner creates it
    _speaker(td, "typed_zero", volume=0.0)
    _speaker(td, "switched_off", active=False)
    _speaker(td, "turned_up_by_hand", volume=0.8, mode=fake_td.ParMode.EXPRESSION)
    _speaker(td, "control_at_zero", volume=0.0, mode=fake_td.ParMode.EXPRESSION)
    found = {s["path"].rsplit("/", 1)[-1]: s for s in tdh.speakers()}
    assert [k for k, s in found.items() if s["fault"]] == ["dropped_in"]
    assert found["turned_up_by_hand"]["loud"] and not found["turned_up_by_hand"]["fault"]
    assert tdh.info()["speakers_on"] == ["/project1/dropped_in"]


def test_mute_silences_the_fault_and_leaves_a_persons_volume_alone(td):
    a = _speaker(td, "dropped_in")
    b = _speaker(td, "turned_up_by_hand", volume=0.8, mode=fake_td.ParMode.EXPRESSION)
    assert tdh.mute() == {"muted": ["/project1/dropped_in"], "left_on": ["/project1/turned_up_by_hand"]}
    assert a.par.volume.eval() == 0 and b.par.volume.eval() == 0.8 and b.par.active.eval() is True
    assert tdh.mute() == {"muted": [], "left_on": ["/project1/turned_up_by_hand"]}
    assert tdh.mute(everything=True)["muted"] == ["/project1/turned_up_by_hand"]
    assert b.par.active.eval() is False and not any(s["loud"] for s in tdh.speakers())


def test_every_check_run_fails_while_a_speaker_is_a_fault(td):
    spec = {"root": "/project1", "checks": [{"type": "no_nan", "path": "out1"}]}
    assert tdh.check(spec, print_summary=False)["status"] == "pass"     # the detector is quiet on a silent project
    _speaker(td, "dropped_in")
    report = tdh.check(spec, print_summary=False)
    silent = [r for r in report["results"] if r["type"] == "silent"]
    assert report["status"] == "fail" and silent[0]["speakers"] == ["/project1/dropped_in"]
    tdh.mute()
    assert tdh.check(spec, print_summary=False)["status"] == "pass"


def _nodes(doc):
    if isinstance(doc, dict):
        if doc.get("type") == "audiodeviceoutCHOP":
            yield doc
        for v in doc.values():
            yield from _nodes(v)
    elif isinstance(doc, list):
        for v in doc:
            yield from _nodes(v)


def test_no_saved_experiment_has_a_speaker_without_a_volume_control():
    seen = 0
    for snap in sorted((ROOT / "experiments").glob("*/snapshot/network.json")):
        for node in _nodes(json.loads(snap.read_text(encoding="utf-8"))):
            seen += 1
            volume = node.get("pars", {}).get("volume")   # a snapshot leaves out a parameter at its default, and the default is full volume
            ok = volume == 0 or (isinstance(volume, dict) and ("expr" in volume or "bind" in volume)) or node.get("pars", {}).get("active") is False
            assert ok, f"{snap.parent.parent.name}: an Audio Device Out plays at a fixed volume ({volume!r}); drive it from a control that defaults to 0"
    assert seen >= 1  # the hub has one, so this test is reading the snapshots it thinks it is
