"""tdh -- TouchDesigner harness toolkit.

Runs inside TouchDesigner, on the main thread, through whatever execute-python
tool your MCP server exposes (TDMCP `execute_code`, touchdesigner-mcp
`execute_python_script`, Embody `execute_python`) or from the textport.

Load it (see .claude/skills/td-connect):

    import sys
    p = r'<absolute path to this repo>/td'
    if p not in sys.path: sys.path.insert(0, p)
    import tdh; tdh.reload()

Then:

    tdh.info()                                   # build, project, repo path
    tdh.errors('/project1')                      # [{path, kind, message}]
    tdh.stats('/project1/out1')                  # pixel stats of a TOP
    tdh.capture('/project1/out1', 'experiments/x/captures/now.png')
    tdh.check('experiments/x/checks.json')       # definition of done
    tdh.snapshot('/project1/x', 'experiments/x/snapshot/network.json')
    tdh.save_tox('/project1/x', 'experiments/x/x.tox')

Every function returns plain JSON-able data. Nothing here creates, deletes or
rewires operators (save_tox only writes a file): building is the MCP server's job; tdh observes and records.
"""

from __future__ import annotations

import importlib

from . import _td, imaging, probe, snapshots
from . import checks as _checks

__version__ = "0.1.0"

errors = probe.errors
stats = probe.stats
motion = probe.motion
total_cooks = probe.total_cooks
cook_ms = probe.cook_ms
cook_sample = probe.cook_sample
info = probe.info
capture = imaging.capture


def check(spec, print_summary=True):
    """Run a checks.json (or dict). Prints a summary and returns the report."""
    report = _checks.run(spec)
    if print_summary:
        print(_checks.summary(report))
    return report


def snapshot(root="/project1", file="snapshot/network.json", exclude=_td.DEFAULT_EXCLUDE):
    return snapshots.snapshot(root, file, exclude)


def save_tox(comp, file):
    """Save a COMP as a .tox (relative paths resolve against the repo root).
    This is how an experiment is persisted to git; see the td-snapshot skill."""
    node = _td.get_op(comp)
    out = _td.resolve_path(file)
    out.parent.mkdir(parents=True, exist_ok=True)
    node.save(str(out))
    return {"file": out.as_posix(), "comp": node.path}


def reload():
    """Pick up edits to tdh without restarting TouchDesigner.
    Note: re-binds the module, so motion() history is cleared."""
    import tdh

    for mod in (_td, probe, imaging, _checks, snapshots):
        importlib.reload(mod)
    return importlib.reload(tdh)
