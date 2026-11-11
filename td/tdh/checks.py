"""Declarative checks: the definition of done for an experiment.

An experiment's checks.json lists assertions; run() evaluates them inside TD
and returns a report. Overall status is 'fail' if any check fails or errors,
'pending' if a check needs a second run (moving, cook_budget), otherwise 'pass'.

checks.json:
{
  "root": "/project1",
  "checks": [
    {"type": "no_errors"},
    {"type": "not_black", "path": "out1", "min_mean": 0.01},
    {"type": "no_nan", "path": "out1"},
    {"type": "moving", "path": "out1", "min_delta": 0.002},
    {"type": "chop_range", "path": "level", "channels": "*", "min": 0, "max": 1},
    {"type": "resolution", "path": "out1", "max": [1280, 1280]},
    {"type": "cook_budget", "max_ms": 8},
    {"type": "controls", "min": 3}
  ]
}
Paths are relative to root unless they start with '/'.
"""

from __future__ import annotations

import json
from fnmatch import fnmatch

from . import probe
from . import ui as _ui
from ._td import get_op, resolve_path

CHECK_TYPES = ("no_errors", "not_black", "no_nan", "moving", "chop_range", "resolution", "cook_budget", "controls")


def _abs(root, path):
    if not path or path == ".":
        return root
    return path if path.startswith("/") else root.rstrip("/") + "/" + path


def _no_errors(c, path):
    found = probe.errors(path, warnings=c.get("include_warnings", False))
    return (not found), {"count": len(found), "errors": found[:20]}


def _not_black(c, path):
    s = probe.stats(path)
    return s["mean"] >= c.get("min_mean", 0.01), {"mean": s["mean"], "max": s["max"]}


def _no_nan(c, path):
    s = probe.stats(path)
    return s["nan_count"] == 0, {"nan_count": s["nan_count"]}


def _moving(c, path):
    m = probe.motion(path)
    if m["status"] == "pending":
        return None, {"hint": m.get("hint", "first sample stored; run the checks again in about a second")}
    if m["status"] == "stalled":
        return False, {"delta": m["delta"], "cooks": m.get("cooks"), "hint": "TOP cooked at most once between samples (only our own read); add a cook driver, and sample about 1 s apart"}
    return m["delta"] >= c.get("min_delta", 0.002), {k: v for k, v in m.items() if k != "status"}


def _chop_range(c, path):
    chop = get_op(path)
    pattern = c.get("channels", "*")
    lo, hi = c.get("min", float("-inf")), c.get("max", float("inf"))
    bad, seen = [], 0
    for chan in chop.chans():
        if not fnmatch(chan.name, pattern):
            continue
        seen += 1
        vals = list(chan.vals)
        if vals and (min(vals) < lo or max(vals) > hi):
            bad.append({"channel": chan.name, "min": min(vals), "max": max(vals)})
    if not seen:
        return False, {"hint": f"no channels match {pattern!r}"}
    return not bad, {"channels": seen, "out_of_range": bad}


def _resolution(c, path):
    node = get_op(path)
    w, h = int(node.width), int(node.height)
    ok = True
    if "width" in c:
        ok &= w == c["width"]
    if "height" in c:
        ok &= h == c["height"]
    if "max" in c:
        ok &= w <= c["max"][0] and h <= c["max"][1]
    return ok, {"width": w, "height": h}


def _cook_budget(c, path):
    """Per-frame cost of the ops that are actually cooking (tdh.cook_sample).
    The first run only records cook counters, so it is 'pending'. Ops that
    cooked once and went idle (a static Ramp's 43 ms creation cook, seen
    live) are not counted."""
    s = probe.cook_sample(path)
    if s["status"] == "pending":
        return None, {"hint": "first sample recorded; run the checks again in about a second"}
    detail = {"cook_ms": round(s["cook_ms"], 3), "active_ops": s["active_ops"], "idle_ops": s["idle_ops"]}
    return s["cook_ms"] <= c["max_ms"], detail


def _has_controls(c, path):
    """The COMP can be played from its own parameter panel: at least `min` custom
    parameters, each read by something inside it (tdh.controls)."""
    return _ui.summary(path, minimum=int(c.get("min", 3)), allow_unused=tuple(c.get("allow_unused", ())))


_RUNNERS = {
    "no_errors": _no_errors,
    "not_black": _not_black,
    "no_nan": _no_nan,
    "moving": _moving,
    "chop_range": _chop_range,
    "resolution": _resolution,
    "cook_budget": _cook_budget,
    "controls": _has_controls,
}


def load(spec):
    if isinstance(spec, dict):
        return spec
    return json.loads(resolve_path(spec).read_text(encoding="utf-8"))


def validate(spec):
    """Structural problems in a checks spec (usable without TD)."""
    problems = []
    if not isinstance(spec.get("checks"), list):
        return ["'checks' must be a list"]
    for i, c in enumerate(spec["checks"]):
        t = c.get("type")
        if t not in CHECK_TYPES:
            problems.append(f"checks[{i}]: unknown type {t!r}")
        if t == "cook_budget" and "max_ms" not in c:
            problems.append(f"checks[{i}]: cook_budget needs max_ms")
        if t in ("not_black", "no_nan", "moving", "chop_range", "resolution") and not c.get("path"):
            problems.append(f"checks[{i}]: {t} needs a path")
    return problems


def run(spec):
    """Evaluate a checks spec (dict, or path to checks.json). Returns a report."""
    spec = load(spec)
    problems = validate(spec)
    if problems:
        return {"status": "fail", "results": [], "problems": problems}
    root = spec.get("root", "/project1")
    results = []
    for c in spec["checks"]:
        path = _abs(root, c.get("path"))
        entry = {"type": c["type"], "path": path}
        try:
            ok, detail = _RUNNERS[c["type"]](c, path)
            entry["status"] = "pending" if ok is None else ("pass" if ok else "fail")
            entry.update(detail)
        except Exception as exc:  # noqa: BLE001 -- report any failure as a check result; never raise on TD main thread
            entry["status"] = "error"
            entry["error"] = f"{type(exc).__name__}: {exc}"
        results.append(entry)
    statuses = {r["status"] for r in results}
    if statuses & {"fail", "error"}:
        status = "fail"
    elif "pending" in statuses:
        status = "pending"
    else:
        status = "pass"
    return {"status": status, "results": results}


def summary(report):
    """One line per check, for printing."""
    lines = [f"tdh check: {report['status'].upper()}"]
    lines += [f"  problem: {p}" for p in report.get("problems", [])]
    for r in report["results"]:
        extra = {k: v for k, v in r.items() if k not in ("type", "path", "status", "errors")}
        lines.append(f"  [{r['status']}] {r['type']} {r['path']} {json.dumps(extra, default=str)}")
        for e in r.get("errors", [])[:5]:
            lines.append(f"      {e['kind']}: {e['path']}: {e['message']}")
    return "\n".join(lines)
