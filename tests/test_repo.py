"""Repo-level safeguards that run without TouchDesigner."""

import json
import re
from pathlib import Path

import pytest

from tdh import checks

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_skill_frontmatter(skill):
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md must start with --- frontmatter ---"
    fields = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    assert fields.get("name", "").strip() == skill.parent.name
    assert len(fields.get("description", "").strip()) > 20


def test_skills_exist():
    assert {p.parent.name for p in SKILLS} >= {"td-connect", "td-sketch", "td-verify", "td-snapshot"}


@pytest.mark.parametrize("spec", sorted(ROOT.glob("experiments/*/checks.json")), ids=lambda p: p.parent.name)
def test_checks_json_valid(spec):
    data = json.loads(spec.read_text(encoding="utf-8"))
    assert checks.validate(data) == []
    assert data.get("root", "").startswith("/project1/")


@pytest.mark.parametrize("snap", sorted(ROOT.glob("experiments/*/snapshot/network.json")), ids=lambda p: p.parts[-3])
def test_snapshots_well_formed(snap):
    data = json.loads(snap.read_text(encoding="utf-8"))
    assert data["format"] == "tdh-snapshot/1"
    assert list(data["ops"]) == sorted(data["ops"]), "ops must be sorted for stable diffs"


def test_mcp_json():
    cfg = json.loads((ROOT / ".mcp.json").read_text())
    assert cfg["mcpServers"]["tdmcp"]["url"].startswith("http://127.0.0.1:")


def test_no_toe_committed_with_server_inside():
    # lab.toe holds the MCP server component and must stay local.
    assert "/lab.toe" in (ROOT / ".gitignore").read_text()


def test_mcp_name_does_not_clash_with_touchdesigner_mcp():
    # touchdesigner-mcp's own installer registers "touchdesigner" at user scope;
    # reusing that name in the project file makes `claude mcp list` report a conflict.
    cfg = json.loads((ROOT / ".mcp.json").read_text())
    assert "touchdesigner" not in cfg["mcpServers"]


SLUG = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@pytest.mark.parametrize("folder", sorted(p for p in (ROOT / "experiments").iterdir() if p.is_dir()), ids=lambda p: p.name)
def test_experiment_folder_is_a_legal_td_name(folder):
    # The slug is also the COMP name; TD rejects '-' ("Illegal node name specified").
    assert SLUG.match(folder.name), f"{folder.name!r}: use snake_case (letters, digits, _)"
