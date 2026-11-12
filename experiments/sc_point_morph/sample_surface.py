# Script TOP callbacks: area-weighted surface sampling of one shape into a point atlas.
# The Script TOP is named bake_<shape>; it reads vp_<shape> (triangle corner positions),
# and when present vn_<shape> (corner normals), vt_<shape> (corner UVs), tex_<shape> (basecolor).
# Output: SIDE wide, 3*SIDE tall, 32-bit float. Rows 0..SIDE-1 position (alpha = point spacing),
# then colour, then normal.
# Point i has the same texel in every shape's atlas, so i has a target in each shape.
# Why not Sprinkle POP: see NOTES.md, log entry 02 (2026-11-10).
# With no model library in the assets folder each model slot bakes a stand-in instead
# (stand_in.py): see NOTES.md, "Assets" (2026-11-11).
import numpy as np



def _flat(top, n):
    a = np.asarray(top.numpyArray(), dtype=np.float32)
    return a.reshape(-1, a.shape[-1])[:n, :3]


def onCook(scriptOp):
    name = scriptOp.name[5:]
    par = scriptOp.parent()
    SIDE = int(par.fetch('side', 352))
    n = SIDE * SIDE
    is_word = name.startswith('word')
    paths = par.op('local/modules/paths').module
    stand = None
    if not is_word and not paths.have('models/%s/model.obj' % name):
        # no library: a teapot or a drawn solid, already centred with its longest side 1 unit
        slot = list(par.fetch('mosaic_models', [])).index(name)      # stand-ins go by slot, not by name
        stand = par.op('stand_in').module.mesh(slot, paths.model_file(name))
        tri, nv = stand[0], stand[0].shape[0] * 3
    else:
        src = par.op('tri_' + name)
        nv = src.numVerts()
        tri = _flat(par.op('vp_' + name), nv).reshape(-1, 3, 3)
    rng = np.random.default_rng(1000 + len(name) * 7 + nv)

    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    face = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(face, axis=1)
    cdf = np.cumsum(area, dtype=np.float64)
    cdf /= cdf[-1]
    idx = np.minimum(np.searchsorted(cdf, rng.random(n)), len(area) - 1)

    u = rng.random(n).astype(np.float32)
    v = rng.random(n).astype(np.float32)
    fold = (u + v) > 1.0
    u[fold] = 1.0 - u[fold]
    v[fold] = 1.0 - v[fold]
    w = 1.0 - u - v
    bary = np.stack([w, u, v], axis=1)[:, :, None]

    pos = (tri[idx] * bary).sum(axis=1)
    if stand is not None:
        stand_col = par.op('stand_in').module.colour(slot, pos)
    if is_word:
        # phrases come in at any size and line count: centre them and fit 2.4 wide by 1.05 tall
        lo, hi = pos.min(axis=0), pos.max(axis=0)
        k = float(min(2.4 / max(hi[0] - lo[0], 1e-6), 1.05 / max(hi[1] - lo[1], 1e-6)))
        pos = (pos - (lo + hi) * 0.5) * k
        area = area * k * k
    # stand every model on the floor (y = -0.5); a word hangs a little above it
    pos[:, 1] += -0.5 - pos[:, 1].min() + (0.22 if is_word else 0.0)

    vn = par.op('vn_' + name)
    if stand is not None:
        nrm = (stand[1][idx] * bary).sum(axis=1)
    elif vn is not None:
        nrm = (_flat(vn, nv).reshape(-1, 3, 3)[idx] * bary).sum(axis=1)
    else:
        nrm = face[idx]
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-8)

    vt = par.op('vt_' + name)
    tex = par.op('tex_' + name)
    if stand is not None:
        col = stand_col
    elif vt is not None and tex is not None:
        uv = (_flat(vt, nv).reshape(-1, 3, 3)[idx] * bary).sum(axis=1)
        img = np.asarray(tex.numpyArray(), dtype=np.float32)
        h, wd = img.shape[0], img.shape[1]
        x = np.clip((uv[:, 0] % 1.0) * wd, 0, wd - 1).astype(np.int32)
        y = np.clip((uv[:, 1] % 1.0) * h, 0, h - 1).astype(np.int32)
        col = img[y, x, :3].copy()
        # Texture atlases have black gutters between islands; a sample that lands on one shows as
        # a pepper speck. Where a sample is near black but its surroundings are not, take the
        # brightest of four neighbours 5 texels away. Real black areas stay black.
        lum = col.sum(axis=1)
        nb = np.stack([img[np.clip(y + dy, 0, h - 1), np.clip(x + dx, 0, wd - 1), :3]
                       for dx, dy in ((5, 0), (-5, 0), (0, 5), (0, -5))], axis=1)
        nlum = nb.sum(axis=2)
        fix = (lum < 0.12) & (nlum.max(axis=1) > 0.6)
        best = nb[np.arange(n), nlum.argmax(axis=1)]
        col[fix] = best[fix]
    else:
        col = np.ones((n, 3), dtype=np.float32)

    # Order the points by height (with some shuffle) so point i sits at a similar height in every
    # shape: the migration then flows in bands instead of every point crossing every other.
    rank = np.argsort(np.argsort(pos[:, 1])).astype(np.float32) / n
    order = np.argsort(rank + 0.22 * rng.random(n).astype(np.float32))

    atlas = np.zeros((3 * SIDE, SIDE, 4), dtype=np.float32)
    atlas[:, :, 3] = 1.0
    atlas[0:SIDE, :, :3] = pos[order].reshape(SIDE, SIDE, 3)
    # alpha of the position rows: mean spacing between neighbouring points on this shape,
    # so the shader can size points to just close the surface whatever the shape's area
    atlas[0:SIDE, :, 3] = float(np.sqrt(area.sum() / n))
    atlas[SIDE:2 * SIDE, :, :3] = col[order].reshape(SIDE, SIDE, 3)
    atlas[2 * SIDE:, :, :3] = nrm[order].reshape(SIDE, SIDE, 3)
    scriptOp.copyNumpyArray(atlas)
    return
