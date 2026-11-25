# Stand-in shapes for when the model library is not in the assets folder.
# sample_surface.py calls mesh() and colour() for a model slot whose model.obj is missing, so the
# scene still has nine different things to morph between: two of them TouchDesigner's bundled
# teapot (the file mod.paths.model_file returns), the rest solids drawn here with numpy.
# Every mesh comes back centred on the origin with its longest side 1 unit, like a library model.
# see: experiments/sc_point_morph/NOTES.md (2026-11-11, "Assets")
import numpy as np

# one row per model slot, in the order of build.py's MODELS: (kind, first colour, second colour,
# how the two colours stripe it). By slot, not by name, because the names belong to the pack.
# Colours are sRGB from the ident palette, chosen against the sun colour of the slot (build.py TINTS).
IVORY, RED, YELLOW, BLUE, GREEN, PINK = '#EEE4CC', '#DC563D', '#DCB53D', '#287E9B', '#99AB54', '#B85779'
SLOTS = [
    ('teapot', YELLOW, IVORY, 'y'),
    ('tower', RED, IVORY, 'y'),
    ('ring', PINK, IVORY, 'angle'),
    ('ball', BLUE, IVORY, 'y'),
    ('spring', IVORY, BLUE, 'y'),
    ('gem', GREEN, IVORY, 'y'),
    ('knot', GREEN, YELLOW, 'angle'),
    ('cone', PINK, IVORY, 'y'),
    ('teapot', BLUE, IVORY, 'y'),
]
SPARE = ('teapot', YELLOW, IVORY, 'y')
BANDS = 7


def _rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)], dtype=np.float32)


def _quads(P, N):
    """Grids of points and normals (rows x cols x 3) -> triangle corners and corner normals."""
    def corners(G):
        a, b, c, d = G[:-1, :-1], G[1:, :-1], G[1:, 1:], G[:-1, 1:]
        return np.concatenate([np.stack([a, b, c], axis=2).reshape(-1, 3, 3),
                               np.stack([a, c, d], axis=2).reshape(-1, 3, 3)])
    return corners(P), corners(N)


def _flat_faces(tri):
    """Triangles with one normal each (facing away from the origin)."""
    tri = np.asarray(tri, dtype=np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    n *= np.sign((n * tri.mean(axis=1)).sum(axis=1, keepdims=True) + 1e-9)
    return tri, np.repeat(n[:, None, :], 3, axis=1)


def _tube(curve, radius, ref, nu=360, nv=24):
    """A round tube along curve(u), u in 0..1. ref is a direction the curve is never parallel to."""
    u = np.linspace(0.0, 1.0, nu + 1)
    c = curve(u)
    t = curve(u + 1e-4) - curve(u - 1e-4)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = np.cross(t, np.asarray(ref, dtype=np.float64))
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    b = np.cross(t, n)
    v = np.linspace(0.0, 2.0 * np.pi, nv + 1)
    out = np.cos(v)[None, :, None] * n[:, None, :] + np.sin(v)[None, :, None] * b[:, None, :]
    return _quads(c[:, None, :] + radius * out, out)


def _ball():
    th = np.linspace(0.0, np.pi, 49)[:, None]
    ph = np.linspace(0.0, 2.0 * np.pi, 97)[None, :]
    d = np.stack([np.sin(th) * np.cos(ph), np.cos(th) * np.ones_like(ph), np.sin(th) * np.sin(ph)], axis=2)
    return _quads(d * 0.5, d)


def _ring():
    return _tube(lambda u: np.stack([np.cos(2 * np.pi * u), 0 * u, np.sin(2 * np.pi * u)], axis=1), 0.36, (0, 1, 0))


def _spring():
    turns = 4.5
    return _tube(lambda u: np.stack([np.cos(2 * np.pi * turns * u), 3.2 * (u - 0.5), np.sin(2 * np.pi * turns * u)], axis=1),
                 0.26, (0, 1, 0), nu=540, nv=16)


def _knot():
    # a trefoil standing upright, facing the camera; its tangent is never along z
    def curve(u):
        a = 2 * np.pi * u
        return np.stack([np.sin(a) + 2 * np.sin(2 * a), np.cos(a) - 2 * np.cos(2 * a), -np.sin(3 * a)], axis=1)
    return _tube(curve, 0.42, (0, 0, 1), nu=420, nv=20)


def _cone():
    r, h = 0.36, 1.0
    v = np.linspace(0.0, 1.0, 33)[:, None]
    ph = np.linspace(0.0, 2.0 * np.pi, 97)[None, :]
    side = np.stack([(1 - v) * r * np.cos(ph), (v - 0.5) * h * np.ones_like(ph), (1 - v) * r * np.sin(ph)], axis=2)
    sn = np.stack([h * np.cos(ph), r * np.ones_like(ph), h * np.sin(ph)], axis=2) / np.hypot(h, r) * np.ones_like(v)[:, :, None]
    base = np.stack([v * r * np.cos(ph), -0.5 * h * np.ones_like(v * ph), v * r * np.sin(ph)], axis=2)
    bn = np.zeros_like(base)
    bn[:, :, 1] = -1.0
    t1, n1 = _quads(side, sn)
    t2, n2 = _quads(base, bn)
    return np.concatenate([t1, t2]), np.concatenate([n1, n2])


def _tower():
    x, y, z = 0.27, 0.5, 0.27
    c = np.array([[sx * x, sy * y, sz * z] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    tri = [[c[q[0]], c[q[1]], c[q[2]]] for q in faces] + [[c[q[0]], c[q[2]], c[q[3]]] for q in faces]
    return _flat_faces(tri)


def _gem():
    # an eight-sided double pyramid
    k = 8
    a = np.arange(k) * 2 * np.pi / k
    rim = np.stack([0.34 * np.cos(a), 0.12 * np.ones(k), 0.34 * np.sin(a)], axis=1)
    top, bottom = np.array([0.0, 0.5, 0.0]), np.array([0.0, -0.5, 0.0])
    tri = []
    for i in range(k):
        j = (i + 1) % k
        tri += [[rim[i], rim[j], top], [rim[i], rim[j], bottom]]
    return _flat_faces(tri)


def _teapot(path):
    """Read an OBJ (the bundled teapot) into triangle corners and corner normals."""
    v, vn, tri, nrm = [], [], [], []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == 'v':
                v.append([float(x) for x in p[1:4]])
            elif p[0] == 'vn':
                vn.append([float(x) for x in p[1:4]])
            elif p[0] == 'f':
                ref = [w.split('/') for w in p[1:]]
                pi = [int(r[0]) for r in ref]
                ni = [int(r[2]) if len(r) > 2 and r[2] else 0 for r in ref]
                for k in range(1, len(pi) - 1):
                    tri.append([pi[0], pi[k], pi[k + 1]])
                    nrm.append([ni[0], ni[k], ni[k + 1]])
    v = np.asarray(v, dtype=np.float32)
    tri = np.asarray(tri, dtype=np.int64)
    tri = np.where(tri < 0, tri + len(v), tri - 1)
    corners = v[tri]
    nrm = np.asarray(nrm, dtype=np.int64)
    if len(vn) and (nrm != 0).all():
        vn = np.asarray(vn, dtype=np.float32)
        return corners, vn[np.where(nrm < 0, nrm + len(vn), nrm - 1)]
    return _flat_faces(corners)


def mesh(slot, obj_path):
    """Triangle corners (T, 3, 3) and corner normals (T, 3, 3) of the stand-in for a model slot."""
    kind = (SLOTS[slot] if 0 <= slot < len(SLOTS) else SPARE)[0]
    made = None
    if kind == 'teapot':
        try:
            made = _teapot(obj_path)
        except Exception:  # noqa: BLE001  no readable teapot either: a ball is still a shape
            made = None
    if made is None:
        made = {'tower': _tower, 'ring': _ring, 'spring': _spring, 'gem': _gem, 'knot': _knot,
                'cone': _cone}.get(kind, _ball)()
    tri = np.asarray(made[0], dtype=np.float32)
    nrm = np.asarray(made[1], dtype=np.float32)
    lo, hi = tri.reshape(-1, 3).min(axis=0), tri.reshape(-1, 3).max(axis=0)
    tri = (tri - (lo + hi) * 0.5) / float((hi - lo).max())
    return tri, nrm


def colour(slot, pos):
    """Two flat colours in bands, so the print and two-ink takes have something to separate."""
    row = SLOTS[slot] if 0 <= slot < len(SLOTS) else SPARE
    if row[3] == 'angle':
        k = np.arctan2(pos[:, 2] if np.ptp(pos[:, 2]) > np.ptp(pos[:, 1]) else pos[:, 1], pos[:, 0]) / (2 * np.pi) * 12
    else:
        k = (pos[:, 1] - pos[:, 1].min()) / max(float(np.ptp(pos[:, 1])), 1e-6) * BANDS
    first = (np.floor(k).astype(np.int64) % 2) == 0
    return np.where(first[:, None], _rgb(row[1])[None, :], _rgb(row[2])[None, :]).astype(np.float32)
