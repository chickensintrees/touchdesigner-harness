# Installed by build.py as the module DAT local/modules/fit, used in expressions as mod.fit.
# Size and centre of an OBJ file, read from its "v" lines and remembered per file, so a stand-in
# model (TouchDesigner's teapot when there is no model library) can be centred and scaled to
# 1 unit like a library model. A POP's computeBounds() returned zeros for the teapot File In POP
# on 2026-11-11, which is why this reads the file.
import os

_seen = {}


def _bounds(path):
    try:
        key = (path, os.path.getmtime(path))
    except OSError:
        return (0.0, 0.0, 0.0, 1.0)
    if key not in _seen:
        lo = [1e30] * 3
        hi = [-1e30] * 3
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("v "):
                    parts = line.split()
                    for i in range(3):
                        v = float(parts[i + 1])
                        lo[i] = min(lo[i], v)
                        hi[i] = max(hi[i], v)
        if hi[0] < lo[0]:
            _seen[key] = (0.0, 0.0, 0.0, 1.0)
        else:
            size = max(max(hi[i] - lo[i] for i in range(3)), 1e-6)
            _seen[key] = tuple((lo[i] + hi[i]) * 0.5 for i in range(3)) + (1.0 / size,)
    return _seen[key]


def center(path, axis):
    """Centre of the file's bounding box on axis 0, 1 or 2."""
    return _bounds(path)[axis]


def scale(path):
    """The scale that makes the file's longest side 1 unit."""
    return _bounds(path)[3]
