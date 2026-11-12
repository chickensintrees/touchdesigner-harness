# Script TOP callbacks: a "catalogue" atlas in which point i belongs to cell (i mod CELLS)
# and takes its texel from that cell's model. Same layout as the atlases of sample_surface.py,
# so the cloud shader can morph to and from it like any other shape.
# The Script TOP is named bake_mosaicA / bake_mosaicB; B shifts every cell to another model.
import numpy as np


def onCook(scriptOp):
    par = scriptOp.parent()
    side = int(par.fetch('side', 352))
    cells = int(par.fetch('cells', 15))
    names = par.fetch('mosaic_models', [])
    shift = 0 if scriptOp.name.endswith('A') else int(par.fetch('mosaic_shift', 4))
    srcs = [np.asarray(par.op('bake_' + n).numpyArray(), dtype=np.float32) for n in names]
    out = np.zeros_like(srcs[0])
    ident = np.arange(side * side).reshape(side, side)       # texel (row, col) -> point id
    cell = np.tile(ident % cells, (3, 1))
    for c in range(cells):
        m = cell == c
        out[m] = srcs[(c + shift * (1 + c % 2)) % len(srcs)][m]
    # each small cloud has only 1/cells of the points, so its points sit further apart
    out[0:side, :, 3] *= float(np.sqrt(cells))
    scriptOp.copyNumpyArray(out)
    return
