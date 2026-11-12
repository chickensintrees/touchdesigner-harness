# The baked beam paths, as stored in paths.npz and as loaded into the scene.
# This file is two things: the callbacks of the `shapes` Script TOP inside TouchDesigner
# (onCook), and the reader/writer bake_paths.py imports in plain python (encode, decode).
#
# paths.npz holds every path as whole numbers so it stays small enough to commit:
#   q     int16 (rows, n, 3)   x, y, z in steps of scale/32767, each sample minus the one before it
#   pen   uint8 (rows, n/8)    the pen bit of each sample, packed
#   scale float                the largest coordinate (1.0)
# A step is 0.00003 units, about a fiftieth of a pixel at 1280 x 720.
# see: experiments/sc_vector_scope/NOTES.md (2026-11-11, Portability)
import numpy as np

SCALE = 1.0


def encode(a):
    """(rows, n, 4) float32 x, y, z, pen -> the arrays np.savez_compressed writes."""
    q = np.round(np.clip(a[..., :3], -SCALE, SCALE) / SCALE * 32767).astype(np.int16)
    return dict(q=np.diff(q, axis=1, prepend=np.int16(0)).astype(np.int16),
                pen=np.packbits(a[..., 3] > 0.5, axis=1), scale=np.float32(SCALE))


def decode(z):
    """The arrays of paths.npz -> (rows, n, 4) float32 x, y, z, pen."""
    q = np.cumsum(z['q'], axis=1, dtype=np.int16)
    rows, n, _ = q.shape
    a = np.empty((rows, n, 4), dtype=np.float32)
    a[..., :3] = q.astype(np.float32) * (float(z['scale']) / 32767.0)
    a[..., 3] = np.unpackbits(z['pen'], axis=1)[:, :n]
    return a


def onCook(scriptOp):
    # a 1024 x 4*ROWS float texture: xyz + pen
    a = decode(np.load(mod.paths.scene_file('paths.npz')))  # noqa: F821  `mod` is a TouchDesigner global
    rows, n, c = a.shape
    scriptOp.copyNumpyArray(np.ascontiguousarray(a.reshape(rows * (n // 1024), 1024, c)))
    return
