"""The repository ships generic words and shapes. A private pack's content stays in that pack.

Two checks:
  - no tracked file says "superworld" (the project the scenes were first made for),
    except the few places listed in ALLOWED;
  - when a private pack is present (assets.local.txt), none of the phrases in its
    scenes/<slug>/words.json files appears in a tracked text file.

Run for one experiment:
    python -m pytest -q tests/test_generic.py -k sc_example
"""

import json
import re
import subprocess
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(rb"s\x00?u\x00?p\x00?e\x00?r\x00?w\x00?o\x00?r\x00?l\x00?d", re.IGNORECASE)

# Files that may say the name, each for a stated reason.
ALLOWED = {
    "tests/test_generic.py": "this test",
    "tools/audiofeed/bake_feed.py": "the name of the score schema it reads",
    "tests/test_audiofeed.py": "the name of the score schema",
    "README.md": "the audio_particles example, published before the scene engine",
    "experiments/audio_particles/NOTES.md": "the audio_particles example, published before the scene engine",
    "tools/site/CONTENT.md": "describes the published film until the site is re-recorded on the generic pack",
    "tools/site/template.html": "describes the published film until the site is re-recorded on the generic pack",
}
TEXT = {".py", ".md", ".json", ".frag", ".vert", ".glsl", ".txt", ".html", ".js", ".css", ".sh", ".toml", ".yml", ".yaml", ".csv"}


def tracked():
    # tracked files and new files not yet added (ignored files are left out)
    out = subprocess.run(["git", "ls-files", "-z", "-c", "-o", "--exclude-standard"], cwd=ROOT, capture_output=True, check=True).stdout
    return [f for f in out.decode("utf-8").split("\0") if f]


def groups():
    found = {}
    for f in tracked():
        parts = f.split("/")
        key = parts[1] if parts[0] == "experiments" and len(parts) > 2 else parts[0]
        found.setdefault(key, []).append(f)
    return found


GROUPS = groups()


def private_pack():
    try:
        line = (ROOT / "assets.local.txt").read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    pack = Path(line)
    return pack if (pack / "scenes").is_dir() else None


def leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from leaves(v)


def squash(text):
    """Upper case, with every run of anything but letters and digits as one space."""
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def private_phrases(pack):
    """Distinctive phrases of the private pack: three words or more, ten characters or more."""
    found = set()
    for path in pack.glob("scenes/*/words.json"):
        for text in leaves(json.loads(path.read_text(encoding="utf-8"))):
            for line in re.split(r"[\n/]", text):
                phrase = squash(line)
                if len(phrase) >= 12 and len(phrase.split()) >= 3:
                    found.add(phrase)
    return found


@pytest.mark.parametrize("group", sorted(GROUPS), ids=str)
def test_no_file_names_the_first_project(group):
    hits = []
    for f in GROUPS[group]:
        if f in ALLOWED:
            continue
        path = ROOT / f
        if not path.is_file():
            continue
        data = path.read_bytes()
        for m in NAME.finditer(data):
            hits.append(f"{f}:{data.count(bytes([10]), 0, m.start()) + 1}")
            if len(hits) >= 12:
                break
    assert not hits, "these still name the first project (generic words live in the scene, the originals in a private pack):\n" + "\n".join(hits)


@pytest.mark.parametrize("group", sorted(GROUPS), ids=str)
def test_no_private_phrase_is_tracked(group):
    pack = private_pack()
    if pack is None:
        pytest.skip("no private pack with scenes/ on this machine")
    phrases = private_phrases(pack)
    hits = []
    for f in GROUPS[group]:
        path = ROOT / f
        if f in ALLOWED or path.suffix.lower() not in TEXT or not path.is_file():
            continue
        body = " " + squash(path.read_text(encoding="utf-8", errors="replace")) + " "
        for phrase in sorted(phrases):
            if " " + phrase + " " in body:
                hits.append(f"{f}  {phrase}")
                if len(hits) >= 12:
                    break
    assert not hits, "phrases of the private pack found in tracked files:\n" + "\n".join(hits)


def test_the_detectors_fire():
    assert NAME.search(b"SuperWorld!") and NAME.search("SUPERWORLD".encode("utf-16-le"))
    assert not NAME.search(b"a super world")
    assert squash("The pie -- is\tNOT for you.") == "THE PIE IS NOT FOR YOU"


def test_private_phrases_are_the_distinctive_ones(tmp_path):
    scene = tmp_path / "scenes" / "sc_a"
    scene.mkdir(parents=True)
    (scene / "words.json").write_text(json.dumps({"LINES": ["TELL YOUR ATOMS\nI SAID HI.", "OPEN", "DO NOT"], "MAP": {"a": ["A FORM IS EMERGING / IT NEEDS A NAME"]}}), encoding="utf-8")
    assert private_phrases(tmp_path) == {"TELL YOUR ATOMS", "A FORM IS EMERGING", "IT NEEDS A NAME"}


# ---- words() and scene_file() of the paths module ---------------------------


def _module(tmp_path):
    repo = tmp_path / "repo"
    (repo / "experiments" / "sc_a").mkdir(parents=True)
    (repo / "assets").mkdir()
    scene = types.SimpleNamespace(name="sc_a")
    scope = {
        "project": types.SimpleNamespace(folder=str(repo)),
        "app": types.SimpleNamespace(samplesFolder=str(tmp_path)),
        "me": types.SimpleNamespace(parent=lambda n: scene),
    }
    source = (ROOT / "experiments" / "sw_hub" / "paths_module.py").read_text(encoding="utf-8")
    exec(compile(source, "paths_module.py", "exec"), scope)
    return types.SimpleNamespace(**scope), repo


def test_words_are_the_scenes_own_without_a_pack_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, _ = _module(tmp_path)
    defaults = {"LINES": ["ONE", "TWO"], "TITLE": "T"}
    assert m.words(defaults) == defaults and m.words(defaults) is not defaults


def test_a_pack_replaces_only_names_the_scene_has(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, repo = _module(tmp_path)
    (repo / "assets" / "scenes" / "sc_a").mkdir(parents=True)
    (repo / "assets" / "scenes" / "sc_a" / "words.json").write_text(json.dumps({"LINES": ["MINE"], "OTHER": "x"}), encoding="utf-8")
    assert m.words({"LINES": ["ONE", "TWO"], "TITLE": "T"}) == {"LINES": ["MINE"], "TITLE": "T"}


def test_a_pack_cannot_change_the_kind_of_a_name(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, repo = _module(tmp_path)
    (repo / "assets" / "scenes" / "sc_a").mkdir(parents=True)
    (repo / "assets" / "scenes" / "sc_a" / "words.json").write_text(json.dumps({"LINES": "not a list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="LINES"):
        m.words({"LINES": ["ONE"]})


def test_scene_file_prefers_the_packs_copy(tmp_path, monkeypatch):
    monkeypatch.delenv("TDH_ASSETS", raising=False)
    m, repo = _module(tmp_path)
    assert m.scene_file("paths.npz") == repo.as_posix() + "/experiments/sc_a/paths.npz"
    (repo / "assets" / "scenes" / "sc_a").mkdir(parents=True)
    (repo / "assets" / "scenes" / "sc_a" / "paths.npz").write_text("x")
    assert m.scene_file("paths.npz") == repo.as_posix() + "/assets/scenes/sc_a/paths.npz"
