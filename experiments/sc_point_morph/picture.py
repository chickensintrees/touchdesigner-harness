# Script TOP callback: the atlas of the "picture sheet", the shape the cloud takes when the scene
# is given an Input picture. A flat 16:9 sheet of SIDE x SIDE points, 2.4 wide by 1.35 tall,
# hanging where the phrases hang. The vertex shader colours each point from the Input TOP at the
# point's place on the sheet and pushes it forward by brightness.
# Row r of the atlas is height r on the sheet, as in every other atlas (points sorted by height).
# see: experiments/sc_point_morph/NOTES.md (2026-11-11, "Input")
import numpy as np

W, H, LIFT = 2.4, 1.35, 0.22      # cloud_vertex.glsl repeats these three numbers (sheetUV)


def onCook(scriptOp):
    SIDE = int(scriptOp.parent().fetch('side', 352))
    rng = np.random.default_rng(77)
    jx = (rng.random((SIDE, SIDE), dtype=np.float32) - 0.5) * 0.7
    jy = (rng.random((SIDE, SIDE), dtype=np.float32) - 0.5) * 0.7
    cx, cy = np.meshgrid(np.arange(SIDE, dtype=np.float32), np.arange(SIDE, dtype=np.float32))
    u = (cx + 0.5 + jx) / SIDE
    v = (cy + 0.5 + jy) / SIDE
    atlas = np.zeros((3 * SIDE, SIDE, 4), dtype=np.float32)
    atlas[:, :, 3] = 1.0
    atlas[0:SIDE, :, 0] = (u - 0.5) * W
    atlas[0:SIDE, :, 1] = -0.5 + LIFT + v * H
    atlas[0:SIDE, :, 3] = float(np.sqrt(W * H / (SIDE * SIDE)))
    atlas[SIDE:2 * SIDE, :, :3] = 1.0
    atlas[2 * SIDE:, :, 2] = 1.0
    scriptOp.copyNumpyArray(atlas)
    return
