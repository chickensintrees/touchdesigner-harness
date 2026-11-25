"""The agent-led install: the one line, the named failures, the safety rules, and the skill that finishes it."""

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]

LINE = "Set up touchdesigner-harness with me by following https://billmoore.ai/touchdesigner/install.md"
CLONE_URL = "https://github.com/chickensintrees/touchdesigner-harness.git"
# SHA-256 of touchdesigner-mcp-td.zip from release v2.2.0 (three downloads on 2026-11-12 agreed).
ZIP_SHA256 = "67a10b7abba05c2b55912625ad40dcd3d2420e1c8a8d64ca644c473dabf38ec0"

INSTALL = ROOT / "docs" / "INSTALL.md"
SKILL = ROOT / ".claude" / "skills" / "td-setup" / "SKILL.md"
README = ROOT / "README.md"

# Files in the repository that must quote the line in a fenced code block of its own.
FENCED = [INSTALL, README]
# The site's files exist only in the private copy; the public copy has no tools/site.
PAGE = ROOT / "tools" / "site" / "template.html"
BOOTSTRAP = ROOT / "tools" / "site" / "install.md"
GUIDES = [INSTALL, SKILL, BOOTSTRAP]

# Each failure the walk-through must handle by name (compared without case).
FAILURES = [
    "touchdesigner is not installed",
    "node.js is too old",
    "clone folder already exists",
    "port 9981 does not answer",
    "no module named 'mcp'",
    "not restarted",
]
TABLE_HEADING = "## Failures, by name"

# The only hosts a guide may send the agent or the person to.
HOSTS = {"github.com", "derivative.ca", "nodejs.org", "git-scm.com", "billmoore.ai", "127.0.0.1"}


def read(path):
    return path.read_text(encoding="utf-8")


def existing(paths):
    return [p for p in paths if p.exists()]


def in_bold(phrase, text):
    # A failure is handled where its name is the bold lead of a paragraph, not where it is only mentioned.
    return re.search(r"[*][*][^*\n]*" + re.escape(phrase) + r"[^*\n]*[*][*]", text) is not None


def assert_no_variant_of_the_line(text):
    for row in text.splitlines():
        if "Set up touchdesigner-harness" in row:
            assert LINE in row, f"a variant of the one line: {row.strip()!r}"


@pytest.mark.parametrize("path", FENCED, ids=lambda p: p.name)
def test_one_line_is_fenced_and_identical(path):
    text = read(path)
    assert "```\n" + LINE + "\n```" in text
    assert_no_variant_of_the_line(text)


def test_one_line_on_the_page():
    if not PAGE.exists():
        pytest.skip("the site is not in this copy")
    text = read(PAGE)
    assert LINE in text
    assert_no_variant_of_the_line(text)


def test_bootstrap_clones_and_hands_over():
    # The bootstrap is the target of the line, so it need not quote it.
    if not BOOTSTRAP.exists():
        pytest.skip("the site is not in this copy")
    text = read(BOOTSTRAP)
    assert_no_variant_of_the_line(text)
    assert CLONE_URL in text
    assert "docs/INSTALL.md" in text


@pytest.mark.parametrize("failure", FAILURES)
def test_named_failures_are_handled_in_the_steps(failure):
    # The table at the end repeats every name, so it must not count as the handling.
    steps, table = read(INSTALL).lower().split(TABLE_HEADING.lower())
    assert in_bold(failure, steps)
    row = next((r for r in table.splitlines() if failure in r), None)
    assert row, f"the table does not name: {failure}"
    assert "step" in row


@pytest.mark.parametrize("failure", FAILURES)
def test_named_failures_are_in_the_skill(failure):
    assert in_bold(failure, read(SKILL).lower())


def test_skill_front_matter_names_td_setup():
    m = re.match(r"^---\n(.*?)\n---\n", read(SKILL), re.DOTALL)
    assert m, "SKILL.md must start with --- front matter ---"
    fields = dict(row.split(":", 1) for row in m.group(1).splitlines() if ":" in row)
    assert fields.get("name", "").strip() == "td-setup"


def test_server_version_is_pinned():
    # A plain install resolved to 2.0.0 on the test machine; server and component must match.
    text = read(INSTALL)
    assert "claude mcp add -s user touchdesigner -- npx -y touchdesigner-mcp-server@2.2.0" in text
    assert "releases/download/v2.2.0/touchdesigner-mcp-td.zip" in text
    assert ZIP_SHA256 in text
    for path in existing([*GUIDES, README, PAGE]):
        assert "@latest" not in read(path), path.name
        assert "releases/latest" not in read(path), path.name


def test_ask_first_rules_are_stated():
    install, skill = read(INSTALL).lower(), read(SKILL).lower()
    assert "ask before anything that changes the machine outside the clone" in install
    assert "ask before anything that changes the machine outside the clone" in skill
    assert "never ask for a password" in install
    assert "never ask for passwords" in skill
    for text in (install, skill):
        assert "show file" in text
        assert "not been tested end to end" in text


def test_registering_the_server_waits_for_a_yes():
    step4 = read(INSTALL).split("## Step 4")[1].split("## Step 5")[0]
    assert "wait for a yes" in step4
    assert "claude mcp remove touchdesigner -s user" in step4
    assert "every folder" in step4
    assert "run Python inside" in step4


def test_lab_project_starts_empty():
    step5a = read(INSTALL).split("### 5a.")[1].split("### 5b.")[0]
    assert step5a.index("**New**") < step5a.index("**Save As...**")


@pytest.mark.parametrize("path", GUIDES, ids=lambda p: p.name)
def test_guides_stay_on_known_hosts_and_run_nothing_piped(path):
    if not path.exists():
        pytest.skip(f"{path.name} is not in this copy")
    text = read(path)
    for url in re.findall(r"https?://[^\s)\"'`>]+", text):
        host = urlparse(url).hostname or ""
        assert host.removeprefix("www.") in HOSTS, url
    # Table rows start with a bar and have a "bash/zsh" column; they are not commands.
    prose = "\n".join(r for r in text.splitlines() if not r.startswith("|"))
    assert not re.search(r"\|\s*(sh|bash|iex|Invoke-Expression)\b", prose)
    assert "dangerously-skip-permissions" not in text
    assert "bypassPermissions" not in text


@pytest.mark.parametrize("path", [INSTALL, SKILL], ids=lambda p: p.name)
def test_project_save_is_only_ever_forbidden(path):
    rows = [r for r in read(path).splitlines() if "project.save()" in r]
    assert rows
    for row in rows:
        assert "never" in row.lower() or "not" in row.lower(), row


def test_guides_point_at_each_other():
    assert "td-setup" in read(INSTALL)
    assert "docs/INSTALL.md" in read(SKILL)
    assert "td-connect" in read(SKILL)
    assert "td-setup" in read(ROOT / ".claude" / "skills" / "td-connect" / "SKILL.md")
    assert "INSTALL.md" in read(ROOT / "docs" / "SETUP.md").split("## 1.")[0]
    assert "td-setup" in read(ROOT / "AGENTS.md").split("## Quick reference")[1]


def test_downloaded_component_is_ignored():
    # INSTALL.md step 3 leaves another project's component and its zip inside the clone.
    ignored = read(ROOT / ".gitignore").splitlines()
    assert "/touchdesigner-mcp-td/" in ignored
    assert "/touchdesigner-mcp-td.zip" in ignored
