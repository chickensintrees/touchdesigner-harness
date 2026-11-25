"""Nothing in the repository may name a folder on somebody's machine.

Run for one experiment while converting it:
    python -m pytest -q tests/test_portable.py -k sc_example
"""

import importlib.util
import os
import re
import subprocess
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# A drive letter followed by Users, a Unix home, or Git Bash's /c/Users, in either slash,
# also when the backslash is itself escaped (as in JSON) or the text is UTF-16.
MACHINE_PATH = re.compile(rb"(?:[A-Za-z]\x00?:|/\x00?[a-z])(?:\x00?[\\/]){1,2}\x00?U\x00?s\x00?e\x00?r\x00?s\x00?(?:\x00?[\\/]){1,2}|/home/[a-z]|/Users/[A-Za-z]")
# Places that legitimately show such a path: docs explaining where TouchDesigner or
# an MCP server installs things on any machine, and this test.
ALLOWED = {"docs/SETUP.md", "docs/TRANSPORTS.md", "docs/KNOWN-ISSUES.md", "docs/REMOTE.md", "tests/test_portable.py"}


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [f for f in out.decode("utf-8").split("\0") if f]


def groups():
    """Tracked files grouped by experiment folder, or by top-level folder."""
    found = {}
    for f in tracked():
        parts = f.split("/")
        key = parts[1] if parts[0] == "experiments" and len(parts) > 2 else parts[0]
        found.setdefault(key, []).append(f)
    return found


GROUPS = groups()


@pytest.mark.parametrize("group", sorted(GROUPS), ids=str)
def test_no_machine_paths(group):
    hits = []
    for f in GROUPS[group]:
        if f in ALLOWED:
            continue
        path = ROOT / f
        if not path.is_file():
            continue
        data = path.read_bytes()
        for m in MACHINE_PATH.finditer(data):
            line = data.count(b"\n", 0, m.start()) + 1
            snippet = data[m.start(): m.start() + 60].replace(b"\x00", b"").decode("ascii", "replace")
            hits.append(f"{f}:{line}  {snippet.splitlines()[0] if snippet else ''}")
            if len(hits) >= 12:
                break
        if len(hits) >= 12:
            break
    assert not hits, "machine paths (use mod.paths / scene_lib helpers, or a repo-relative path):\n" + "\n".join(hits)


def test_the_detector_fires_on_every_spelling():
    for text in (b"C:/Users/pc/x", b"c:\\Users\\pc", b"C:\\\\Users\\\\pc", b"/c/Users/pc", b"/home/bill/x", b"/Users/bill/x",
                 "C:/Users/pc".encode("utf-16-le")):
        assert MACHINE_PATH.search(text), text
    for text in (b"users/guide", b"project.folder + '/assets'", b"https://github.com/users/x", b"C:/Program Files/Derivative"):
        assert not MACHINE_PATH.search(text), text


# ---- the paths module itself ----------------------------------------------------


def _module(tmp_path, with_assets=True, env=None, monkeypatch=None):
    repo = tmp_path / "repo"
    (repo / "experiments").mkdir(parents=True)
    samples = tmp_path / "samples"
    (samples / "Geo").mkdir(parents=True)
    (samples / "Geo" / "UtahTeapot.obj").write_text("teapot")
    if with_assets:
        (repo / "assets" / "models" / "phone").mkdir(parents=True)
        (repo / "assets" / "models" / "phone" / "model.obj").write_text("o")
        (repo / "assets" / "models" / "phone" / "basecolor.png").write_text("p")
        (repo / "assets" / "fonts").mkdir(parents=True)
        (repo / "assets" / "fonts" / "ChicagoFLF.ttf").write_text("f")
    scene = types.SimpleNamespace(name="sc_example")
    me = types.SimpleNamespace(parent=lambda n: scene)
    scope = {
        "project": types.SimpleNamespace(folder=str(repo)),
        "app": types.SimpleNamespace(samplesFolder=str(samples)),
        "me": me,
    }
    source = (ROOT / "experiments" / "sw_hub" / "paths_module.py").read_text(encoding="utf-8")
    exec(compile(source, "paths_module.py", "exec"), scope)
    return types.SimpleNamespace(**scope), repo, samples


def test_paths_resolve_inside_the_repo(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, repo, _ = _module(tmp_path)
    assert m.repo() == repo.as_posix()
    assert m.here("shaders/a.frag") == repo.as_posix() + "/experiments/sc_example/shaders/a.frag"
    assert m.model_file("phone") == repo.as_posix() + "/assets/models/phone/model.obj"
    assert m.model_texture("phone").endswith("/assets/models/phone/basecolor.png")
    assert m.font("chicago").endswith("/assets/fonts/ChicagoFLF.ttf")
    assert "\\" not in m.repo() + m.here("x") + m.model_file("phone")


def test_missing_assets_fall_back(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, _, samples = _module(tmp_path, with_assets=False)
    assert m.model_file("phone") == samples.as_posix() + "/Geo/UtahTeapot.obj"
    assert os.path.exists(m.model_file("phone"))
    assert m.model_texture("phone") == ""
    assert m.font("chicago") == "" and m.font("barlow") == ""
    assert m.asset("art/mark.png") == "" and not m.have("art/mark.png")


def test_assets_folder_can_be_moved_with_the_variable(tmp_path, monkeypatch):
    elsewhere = tmp_path / "my assets"
    (elsewhere / "fonts").mkdir(parents=True)
    (elsewhere / "fonts" / "ChicagoFLF.ttf").write_text("f")
    monkeypatch.setenv("TDH_ASSETS", str(elsewhere))
    m, _, _ = _module(tmp_path, with_assets=False)
    assert m.assets() == elsewhere.as_posix()
    assert m.font("chicago") == elsewhere.as_posix() + "/fonts/ChicagoFLF.ttf"


def test_a_components_own_assets_parameter_wins(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, repo, samples = _module(tmp_path)  # the repo HAS assets
    empty = tmp_path / "none"
    empty.mkdir()
    par = types.SimpleNamespace(Assets=types.SimpleNamespace(eval=lambda: str(empty)))
    m.me.parent = lambda n: types.SimpleNamespace(name="sc_example", par=par)
    assert m.assets() == empty.as_posix()
    assert m.model_file("phone") == samples.as_posix() + "/Geo/UtahTeapot.obj"
    assert m.font("chicago") == ""
    par.Assets = types.SimpleNamespace(eval=lambda: "")  # blank again: back to the repo's assets
    assert m.model_file("phone") == repo.as_posix() + "/assets/models/phone/model.obj"


def test_feed_baker_records_no_folder():
    spec = importlib.util.spec_from_file_location("bake_feed", ROOT / "tools" / "audiofeed" / "bake_feed.py")
    bake = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bake)
    score = {
        "source": {"duration_s": 1.0, "path": "C:/Users/someone/music/track one.wav"},
        "grid": {"start_s": 0.0, "step_s": 0.02, "count": 50},
        "streams": {"rms": {"values": [0.1] * 50}},
        "events": {},
        "tempo": {"bpm": 120},
    }
    _, _, meta = bake.bake(score)
    assert meta["source"] == "track one.wav"
