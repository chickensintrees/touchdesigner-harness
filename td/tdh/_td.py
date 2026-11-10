"""Thin layer over TouchDesigner's `td` module.

Everything that touches TD goes through here, so the rest of tdh can be
tested outside TouchDesigner with a fake `td` module (see tests/fake_td.py).
All functions must be called on TD's main thread (i.e. from an MCP server's
execute-python tool, a DAT callback, or the textport) -- never from a thread.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

# td/tdh/_td.py -> repo root is two levels above the package.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Names of harness / MCP-server components that should never be walked,
# snapshotted, or edited by experiments.
DEFAULT_EXCLUDE = ("TDMCP*", "Embody*", "Envoy*", "mcp_webserver*", "twozero*")


def td():
    import td as _td  # only importable inside TouchDesigner (or tests)

    return _td


def get_op(target):
    """Return an OP for a path string, or pass an OP straight through."""
    if not isinstance(target, str):
        return target
    found = td().op(target)
    if found is None:
        raise LookupError(f"no operator at {target!r}")
    return found


def children(node):
    return list(getattr(node, "children", None) or [])


def walk(root, exclude=DEFAULT_EXCLUDE):
    """Yield root and every descendant, depth-first, skipping excluded names."""
    root = get_op(root)
    stack = [root]
    while stack:
        node = stack.pop()
        if node is not root and any(fnmatch(node.name, pat) for pat in exclude):
            continue
        yield node
        stack.extend(reversed(children(node)))


def resolve_path(path) -> Path:
    """Resolve a file path; relative paths are relative to the repo root."""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def relpath(node, root) -> str:
    """Path of node relative to root ('.' for root itself)."""
    if node.path == root.path:
        return "."
    prefix = root.path.rstrip("/") + "/"
    return node.path.removeprefix(prefix)


def family(node) -> str:
    return str(getattr(node, "family", "") or "")
