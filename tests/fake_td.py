"""A tiny stand-in for TouchDesigner's `td` module, enough to test tdh.

It mirrors only the attributes tdh reads. When TD's real API disagrees with
this fake, the fake is wrong: fix it and the code together.
"""

from __future__ import annotations

import enum
import types

import numpy as np


class ParMode(enum.Enum):
    CONSTANT = 0
    EXPRESSION = 1
    EXPORT = 2
    BIND = 3


class Par:
    def __init__(self, name, val, default=None, mode=ParMode.CONSTANT, expr="", custom=False, readOnly=False, isPulse=False):
        self.name, self.val, self.default = name, val, default
        self.mode, self.expr, self.bindExpr = mode, expr, ""
        self.isCustom, self.readOnly, self.isPulse, self.isMomentary = custom, readOnly, isPulse, False

    reported_default = None  # set False to mimic TD reporting isDefault False for a default value

    @property
    def isDefault(self):
        if self.reported_default is not None:
            return self.reported_default
        return self.mode is ParMode.CONSTANT and self.val == self.default

    def eval(self):
        return self.val


class _Pars:
    def __init__(self, pars):
        self._pars = {p.name: p for p in pars}

    def __getattr__(self, name):
        try:
            return self.__dict__["_pars"][name]
        except KeyError:
            return None


class Connector:
    def __init__(self, owner):
        self.owner = owner
        self.connections = []


class OP:
    family = "COMP"

    def __init__(self, registry, path, optype, pars=(), n_inputs=1, errors="", warnings="", x=0, y=0):
        self._registry = registry
        self.path, self.name = path, path.rsplit("/", 1)[-1] or "/"
        self.OPType, self.type = optype, optype.removesuffix(self.family)
        self._pars = list(pars)
        self.par = _Pars(self._pars)
        self._errors, self._warnings = errors, warnings
        self.nodeX, self.nodeY = x, y
        self.inputConnectors = [Connector(self) for _ in range(n_inputs)]
        self.outputConnectors = [Connector(self)]
        self.cpuCookTime, self.gpuCookTime = 0.5, 0.25
        self.totalCooks = 0
        registry[path] = self

    @property
    def children(self):
        prefix = self.path.rstrip("/") + "/"
        return [o for p, o in sorted(self._registry.items()) if p.startswith(prefix) and "/" not in p[len(prefix):]]

    def pars(self):
        return list(self._pars)

    def errors(self, recurse=False):
        return self._errors

    def warnings(self, recurse=False):
        return self._warnings

    def scriptErrors(self, recurse=False):
        return ""

    def save(self, filepath):
        with open(filepath, "wb") as f:
            f.write(b"fake tox " + self.path.encode())
        return filepath


class TOP(OP):
    family = "TOP"

    def __init__(self, *a, pixels=None, **kw):
        super().__init__(*a, **kw)
        self.pixels = pixels if pixels is not None else np.zeros((8, 8, 4), np.float32)

    @property
    def width(self):
        return self.pixels.shape[1]

    @property
    def height(self):
        return self.pixels.shape[0]

    def numpyArray(self, delayed=False, writable=False):
        self.totalCooks += 1  # real TD: reading pixels forces a cook
        return self.pixels


class Chan:
    def __init__(self, name, vals):
        self.name, self.vals = name, vals


class CHOP(OP):
    family = "CHOP"

    def __init__(self, *a, channels=None, **kw):
        super().__init__(*a, **kw)
        self._chans = [Chan(k, v) for k, v in (channels or {}).items()]

    def chans(self, *patterns):
        return list(self._chans)


class DAT(OP):
    family = "DAT"

    def __init__(self, *a, text="", **kw):
        super().__init__(*a, **kw)
        self.text = text


def wire(src, dst, index=0):
    dst.inputConnectors[index].connections.append(src.outputConnectors[0])


def make_module():
    registry: dict = {}
    mod = types.ModuleType("td")
    mod.ParMode = ParMode
    mod.op = registry.get
    mod.app = types.SimpleNamespace(version="2025.33230", build="33230", osName="macOS")
    mod.project = types.SimpleNamespace(name="test.toe", folder="/tmp")
    mod.absTime = types.SimpleNamespace(seconds=0.0)

    def tick(seconds=1.0, cooks=None):
        """Advance TD's clock; cooks maps op path -> frames it cooked meanwhile."""
        mod.absTime.seconds += seconds
        for path, n in (cooks or {}).items():
            registry[path].totalCooks += n

    mod.tick = tick
    mod._registry = registry
    return mod
