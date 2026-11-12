"""Deterministic text snapshot of a network, for git diffs and review.

A snapshot is NOT a restore format: the .toe stays the source of truth.
The snapshot exists so a commit shows *what changed* in the network --
operators added or removed, rewiring, parameter changes, DAT text -- as a
readable diff. Only non-default parameters are recorded.
"""

from __future__ import annotations

import json

from . import _td
from ._td import DEFAULT_EXCLUDE, family, get_op, relpath, resolve_path, walk

FORMAT = "tdh-snapshot/1"


def _mode_name(par):
    mode = getattr(par, "mode", None)
    return getattr(mode, "name", None) or (str(mode).split(".")[-1] if mode is not None else "CONSTANT")


def _is_default(par):
    """Default if TD says so, or if it is a constant whose value equals its
    default. Live TD reported noiseTOP.par.tx == 0 with default 0 but
    isDefault False, which put noise like 'tx: 0.0' into every snapshot."""
    if getattr(par, "isDefault", None) is True:
        return True
    if _mode_name(par) != "CONSTANT":
        return False
    default = getattr(par, "default", None)
    value = par.eval() if hasattr(par, "eval") else par.val
    if isinstance(value, (int, float)) and isinstance(default, (int, float)) and not isinstance(value, bool):
        return abs(float(value) - float(default)) <= 1e-9
    return value == default


def _plain(value):
    """JSON-safe value: OPs become their path, everything else str() if needed."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    path = getattr(value, "path", None)
    return path if isinstance(path, str) else str(value)


def par_record(par):
    mode = _mode_name(par)
    if mode == "EXPRESSION":
        return {"expr": par.expr}
    if mode == "BIND":
        return {"bind": getattr(par, "bindExpr", "")}
    if mode == "EXPORT":
        return {"export": _plain(par.val)}
    return _plain(par.val)


def _skip_par(par):
    return bool(getattr(par, "readOnly", False) or getattr(par, "isPulse", False) or getattr(par, "isMomentary", False))


def _inputs(node, root):
    conns = getattr(node, "inputConnectors", None)
    if conns:
        wired = [[relpath(c.owner, root) for c in (conn.connections or [])] for conn in conns]
        while wired and not wired[-1]:
            wired.pop()
        return wired
    return [[relpath(i, root)] for i in (getattr(node, "inputs", None) or []) if i is not None]


def op_record(node, root):
    rec = {
        "type": getattr(node, "OPType", None) or getattr(node, "type", None),
        "family": family(node),
        "pos": [getattr(node, "nodeX", 0), getattr(node, "nodeY", 0)],
    }
    inputs = _inputs(node, root)
    if inputs:
        rec["inputs"] = inputs
    pars = {}
    custom = []
    for par in node.pars():
        if getattr(par, "isCustom", False):
            custom.append(par.name)
        if _skip_par(par) or _is_default(par):
            continue
        pars[par.name] = par_record(par)
    if pars:
        rec["pars"] = dict(sorted(pars.items()))
    if custom:
        rec["custom_pars"] = sorted(custom)
    if rec["family"] == "DAT" and _authored_dat(node):
        file_par = getattr(getattr(node, "par", None), "file", None)
        synced = file_par is not None and str(file_par.eval() if hasattr(file_par, "eval") else file_par.val)
        if synced:
            rec["text_file"] = _repo_relative(synced)  # content lives in that file, already in git
        else:
            rec["text"] = str(getattr(node, "text", "")).splitlines()
    return rec


def _repo_relative(path):
    """A file inside the repo is recorded relative to it, so a snapshot never
    carries the folder of the machine that wrote it."""
    text = str(path).replace("\\", "/")
    root = _td.REPO_ROOT.as_posix().rstrip("/") + "/"
    if text.lower().startswith(root.lower()):
        return text[len(root):]
    return text


def _authored_dat(node):
    """DATs whose text a person (or agent) writes: text, table, script and the
    *execute callback DATs. Generated DATs (Info, Select, Web...) change every
    frame and would make every diff noisy, so their text is not recorded."""
    kind = str(getattr(node, "type", "") or "")
    return kind in ("text", "table", "script") or "exec" in kind


def build(root="/project1", exclude=DEFAULT_EXCLUDE):
    """Return the snapshot dict for root."""
    root = get_op(root)
    ops = {}
    for node in walk(root, exclude):
        if node is root:
            continue
        ops[relpath(node, root)] = op_record(node, root)
    return {"format": FORMAT, "root": root.path, "ops": dict(sorted(ops.items()))}


def dumps(snap):
    return json.dumps(snap, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


def snapshot(root="/project1", file="snapshot/network.json", exclude=DEFAULT_EXCLUDE):
    """Write a snapshot of root to file (relative to the harness repo root).
    Returns {'file', 'ops'}."""
    snap = build(root, exclude)
    out = resolve_path(file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps(snap), encoding="utf-8")
    return {"file": out.as_posix(), "ops": len(snap["ops"])}
