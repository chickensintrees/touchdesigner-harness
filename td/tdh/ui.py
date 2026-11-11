"""Controls: the knobs a person uses instead of reading the network.

An experiment's COMP carries custom parameters (text boxes, sliders, toggles,
menus, buttons). TouchDesigner draws them as a ready-made panel, so a network
with good controls needs no other interface: open the COMP's parameter window
beside its output and play it.

A control only counts if something inside the COMP actually reads it. A slider
that is wired to nothing is worse than no slider: it looks like it works.
`controls()` therefore reports, for every custom parameter, which operators
refer to it (in a parameter expression, a bind, or the text of a script DAT).

    tdh.controls('/project1/x')   # [{name, label, page, kind, value, used_by}]
    tdh.show('/project1/x')       # float the panel and the output as windows

Nothing here builds or rewires operators; show() only opens two windows.
"""

from __future__ import annotations

import re

from ._td import get_op, relpath, walk

MAX_USERS = 8  # how many referring operators to list per control


def _custom_pars(comp):
    pars = getattr(comp, "customPars", None)
    if pars is None:
        pars = [p for p in comp.pars() if getattr(p, "isCustom", False)]
    return list(pars)


def _kind(par):
    if getattr(par, "readOnly", False):
        return "readout"
    if getattr(par, "isPulse", False) or getattr(par, "isMomentary", False):
        return "button"
    return "control"


def _mode_name(par):
    mode = getattr(par, "mode", None)
    return getattr(mode, "name", None) or (str(mode).split(".")[-1] if mode is not None else "CONSTANT")


def _sources(node):
    """Every piece of text on this operator that could refer to a control."""
    for par in node.pars():
        mode = _mode_name(par)
        if mode == "EXPRESSION":
            yield par.expr or ""
        elif mode == "BIND":
            yield getattr(par, "bindExpr", "") or ""
    text = getattr(node, "text", None)
    kind = str(getattr(node, "type", "") or "")
    if isinstance(text, str) and (kind in ("text", "table", "script") or "exec" in kind):
        yield text


def _pattern(name):
    # par.Name, par['Name'], par["Name"]; \b keeps Speed from matching Speedup.
    n = re.escape(name)
    return re.compile(r"par\." + n + r"\b|par\[\s*['\"]" + n + r"['\"]\s*\]")


def controls(comp):
    """Every custom parameter on the COMP, and the operators inside that read it."""
    comp = get_op(comp)
    pars = _custom_pars(comp)
    patterns = {p.name: _pattern(p.name) for p in pars}
    users = {p.name: [] for p in pars}
    if pars:
        for node in walk(comp):
            if node is comp:
                continue
            texts = list(_sources(node))
            if not texts:
                continue
            for name, pat in patterns.items():
                if any(pat.search(t) for t in texts):
                    users[name].append(relpath(node, comp))
    out = []
    for p in pars:
        page = getattr(getattr(p, "page", None), "name", "") or ""
        try:
            value = p.eval()
        except Exception:  # noqa: BLE001 -- a control with a broken expression still gets listed
            value = None
        if not isinstance(value, (int, float, str, bool)) and value is not None:
            value = str(value)
        out.append({
            "name": p.name,
            "label": getattr(p, "label", p.name) or p.name,
            "page": page,
            "kind": _kind(p),
            "value": value,
            "used_by": users[p.name][:MAX_USERS],
            "users": len(users[p.name]),
        })
    return out


def summary(comp, minimum=3, allow_unused=()):
    """Is this COMP playable without reading its network? Used by the `controls` check."""
    found = controls(comp)
    live = [c for c in found if c["kind"] != "readout"]
    dead = [c["name"] for c in live if not c["users"] and c["name"] not in allow_unused]
    working = [c["name"] for c in live if c["users"] or c["name"] in allow_unused]
    ok = len(working) >= minimum and not dead
    detail = {"controls": working, "count": len(working), "min": minimum, "unused": dead}
    if len(working) < minimum:
        detail["hint"] = (
            "expose the values a person would want to change (text, amounts, colours, speeds) as custom "
            "parameters on the experiment COMP and read them inside with parent().par.Name"
        )
    elif dead:
        detail["hint"] = "these controls are read by nothing inside the COMP: wire them in or remove them"
    return ok, detail


def show(comp, output="out1"):
    """Open the COMP's controls and its output as two floating windows."""
    comp = get_op(comp)
    opened = []
    if hasattr(comp, "openParameters"):
        comp.openParameters()
        opened.append("controls")
    out = comp.op(output) if hasattr(comp, "op") else None
    if out is not None and hasattr(out, "openViewer"):
        out.openViewer(unique=False, borders=True)
        opened.append("output")
    return {"comp": comp.path, "opened": opened}
