"""Which track a new hub starts on (experiments/sw_hub/hub_module.py)."""

import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _track(pack, name):
    (pack / "music").mkdir(parents=True, exist_ok=True)
    (pack / "music" / (name + ".mp3")).write_text("a")
    (pack / "feeds" / name).mkdir(parents=True, exist_ok=True)
    (pack / "feeds" / name / "feed.json").write_text("{}")


def _module(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    repo = tmp_path / "repo"
    (repo / "assets").mkdir(parents=True)
    scope = {
        "project": types.SimpleNamespace(folder=str(repo)),
        "app": types.SimpleNamespace(samplesFolder=str(tmp_path / "samples")),
    }
    source = (ROOT / "experiments" / "sw_hub" / "hub_module.py").read_text(encoding="utf-8")
    exec(compile(source, "hub_module.py", "exec"), scope)
    return types.SimpleNamespace(**scope), repo


def test_no_tracks_means_the_sample(tmp_path, monkeypatch):
    m, _ = _module(tmp_path, monkeypatch)
    assert m.default_track() == m.SAMPLE


def test_the_pack_names_its_default(tmp_path, monkeypatch):
    m, repo = _module(tmp_path, monkeypatch)
    _track(repo / "assets", "drift")
    _track(repo / "assets", "drive")
    assert m.default_track() == "drift"  # first by name when the pack names none
    (repo / "assets" / "default_track.txt").write_text("drive\n")
    assert m.default_track() == "drive"
    (repo / "assets" / "default_track.txt").write_text("gone\n")
    assert m.default_track() == "drift"  # a name with no track is ignored


def test_your_own_pack_comes_first(tmp_path, monkeypatch):
    m, repo = _module(tmp_path, monkeypatch)
    _track(repo / "assets", "drive")
    mine = tmp_path / "mine"
    _track(mine, "zebra")
    (repo / "assets.local.txt").write_text(str(mine) + "\n")
    assert m.default_track() == "zebra"
