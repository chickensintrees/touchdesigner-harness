# Fracture bake for sc_shatter. Pure numpy, so it runs both in system Python (preferred: it does
# not block TouchDesigner) and inside TouchDesigner (build.py falls back to that when a cache
# file is missing).
#
#   python bake.py all            bake every subject whose source is available
#   python bake.py bust amphora   bake the named subjects
#   python bake.py --noassets --teapot <TouchDesigner>/Samples/Geo/UtahTeapot.obj all
#                                 bake the stand-ins used when there is no assets folder, into
#                                 cache/noassets/ (every model is the teapot; the text meshes are
#                                 the ones build.py's dump_texts() wrote there in the default face)
#   --assets DIR                  use another assets folder (default: TDH_ASSETS, the folder named in
#                                 <repo>/assets.local.txt, or <repo>/assets). The subjects are the ones
#                                 that folder's pack asks for (see load_words)
#
# Models come from <assets>/models/<slug>/model.obj. This file never names a folder: in the shell
# it finds the repository from its own location, inside TouchDesigner build.py passes the paths.
#
# Input: a triangle soup (positions, optional normals and uvs).
# Output: cache/<subject>.npy, float32, shape (3*H + 8, 1280, 4): the atlas the GLSL MAT reads.
#   rows 0..H-1      per triangle corner: position xyz, fine cell id
#   rows H..2H-1     normal xyz, micro cell id
#   rows 2H..3H-1    uv, kind (0 outer skin, 1 inner skin, 2 fracture wall), height of the triangle's centre
#   rows 3H..3H+3    micro cell table: pivot xyz, fine id
#   row  3H+4        fine cell table: pivot xyz, coarse id
#   row  3H+5        fine cell table: mean normal xyz, radius
#   row  3H+6        coarse cell table: pivot xyz, radius
#   row  3H+7        meta: [0] corners, micro, fine, coarse counts; [1] bbox min, has uv;
#                    [2] bbox max, thickness; [3] surface centroid
# Three consecutive corners are one triangle. Coarse cells are unions of fine cells, fine cells
# unions of micro cells, so the walls built on fine boundaries also close coarse pieces.
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else None
NOASSETS = 'noassets'  # sub-folder of cache/ for the stand-ins baked when a model or the font is missing
FALLBACK_MAXEDGE = 0.03  # the teapot is 3,000 triangles: subdivide it so the fracture lines can be fine
# Longest side of the stand-in teapot, in units. The library models are 1 unit on their longest
# side and mostly tall; the teapot is squat (0.47 high at 1 unit long), so alone in a frame it is
# baked larger. Subjects marked instanced (drawn in rows and grids) keep the library size.
FALLBACK_SIZE = 1.45
W = 1280
TABLE_ROWS = 8
MICRO_ROWS = 4
SLABS = 10.0          # slab planes per unit along y, cut into every atlas (shader level 3)

# The subjects that belong to a pack (the models and the phrases) are rows of WORDS in build.py,
# which a pack may replace (its scenes/sc_shatter/words.json); subjects() below turns them into the
# table the bake reads. SUBJECTS here holds only the ones that are the same on every pack.
# kind model: slug, optional decimate grid (cells per unit) and maxedge (subdivide longer edges),
#   optional scale (the model is baked this many times its own size) and yaw (degrees about the
#   vertical, applied before the bake), instanced (drawn by the dozen: its stand-in stays small).
#   shell: the model is a thin double wall, an outer sheet and an inner one a hair inside it (the
#   pack's generated models are); only the outer sheet is kept (see _outer_skin).
# kind text: text, width in units (bake scales it), depth is set on the Text POP by build.py.
# cells = (micro, fine, coarse). thick = shell thickness in units (0 = no inner skin / walls).
SUBJECTS = {
    # Describe mode (build.py TAKES 'describe'): the same two text takes, with words that say what
    # the viewer is looking at. Every statement is checked against the take's numbers in build.py.
    'x_chips':  dict(kind='text', text='ONE MESH CUT\nINTO CHIPS.', width=3.6, cells=(2600, 400, 16), thick=0.03, maxedge=0.03),
    'x_flock':  dict(kind='text', text='CHIPS FLOCK,\nTHEN LOCK IN.', width=3.7, cells=(2600, 400, 16), thick=0.03, maxedge=0.03),
    'x_bars':   dict(kind='text', text='WHOLE AGAIN\nEVERY 2 BARS.', width=3.7, cells=(2600, 400, 16), thick=0.03, maxedge=0.03),
    'x_math':   dict(kind='text', text='NO SIMULATION.\nONE FORMULA.', width=3.8, cells=(2600, 400, 16), thick=0.03, maxedge=0.03),
    'x_blocks': dict(kind='text', text='CUT INTO\nBLOCKS', width=2.6, cells=(2600, 320, 14), thick=0.03, maxedge=0.03),
    'x_fall':   dict(kind='text', text='FALL.\nUN-FALL.', width=2.6, cells=(2600, 320, 12), thick=0.03, maxedge=0.03),
    'x_rev':    dict(kind='text', text='SHATTER\nIN REVERSE', width=2.8, cells=(2600, 400, 16), thick=0.03, maxedge=0.03),
    # Input (build.py TAKES 'input'): a 16:9 slab whose two faces carry the picture named by the
    # scene's Input parameter. width in units; faceup lays it on the floor for the top-down takes.
    'panel':   dict(kind='panel', width=1.5, depth=0.05, cells=(2400, 260, 12), thick=0.02, maxedge=0.026),
    'panel_f': dict(kind='panel', width=3.0, depth=0.07, cells=(2400, 260, 12), thick=0.028, maxedge=0.052, faceup=True),
    'panel_s': dict(kind='panel', width=1.2, depth=0.05, cells=(260, 40, 6), thick=0.03, maxedge=0.085, inner=False, faceup=True),
    'panel_m': dict(kind='panel', width=0.74, depth=0.04, cells=(700, 110, 9), thick=0.016, maxedge=0.034),
}
MAX_TRIS = 176000   # the big soup in build.py draws 176000 triangles; the atlas tops out at 1280 rows


def load_obj(path):
    """Triangle soup from a library OBJ: (nt,3,3) positions, normals, (nt,3,2) uvs."""
    v, vt, vn, f = [], [], [], []
    with open(path, 'r') as fh:
        for line in fh:
            if line.startswith('v '):
                v.append(line.split()[1:4])
            elif line.startswith('vt '):
                vt.append(line.split()[1:3])
            elif line.startswith('vn '):
                vn.append(line.split()[1:4])
            elif line.startswith('f '):
                c = [p.split('/') for p in line.split()[1:]]
                for k in range(1, len(c) - 1):
                    f.append(c[0] + c[k] + c[k + 1])
    v = np.asarray(v, dtype=np.float32)
    vt = np.asarray(vt, dtype=np.float32)
    vn = np.asarray(vn, dtype=np.float32)
    f = np.asarray(f, dtype=np.int64).reshape(-1, 3, 3) - 1
    return v[f[:, :, 0]], vn[f[:, :, 2]], vt[f[:, :, 1]]


def make_panel(width, depth):
    """A 16:9 slab standing in the xy plane, as a triangle soup with normals and uvs. Both faces
    carry the whole picture the right way round for whoever looks at them; the four thin sides
    repeat the picture's border."""
    w, h, d = width * 0.5, width * 9.0 / 16.0, depth * 0.5

    def quad(p, n, t):
        p, t = np.asarray(p, dtype=np.float32), np.asarray(t, dtype=np.float32)
        nn = np.repeat(np.asarray([n], dtype=np.float32), 3, axis=0)
        return [(p[[0, 1, 2]], nn, t[[0, 1, 2]]), (p[[0, 2, 3]], nn, t[[0, 2, 3]])]
    q = []
    q += quad([(-w, 0, d), (w, 0, d), (w, h, d), (-w, h, d)], (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    q += quad([(w, 0, -d), (-w, 0, -d), (-w, h, -d), (w, h, -d)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    q += quad([(w, 0, d), (w, 0, -d), (w, h, -d), (w, h, d)], (1, 0, 0), [(1, 0), (1, 0), (1, 1), (1, 1)])
    q += quad([(-w, 0, -d), (-w, 0, d), (-w, h, d), (-w, h, -d)], (-1, 0, 0), [(0, 0), (0, 0), (0, 1), (0, 1)])
    q += quad([(-w, h, d), (w, h, d), (w, h, -d), (-w, h, -d)], (0, 1, 0), [(0, 1), (1, 1), (1, 1), (0, 1)])
    q += quad([(-w, 0, -d), (w, 0, -d), (w, 0, d), (-w, 0, d)], (0, -1, 0), [(0, 0), (1, 0), (1, 0), (0, 0)])
    return (np.stack([x[0] for x in q]), np.stack([x[1] for x in q]), np.stack([x[2] for x in q]))


def _unit(a):
    return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)


def _face(tri):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = 0.5 * np.linalg.norm(n, axis=1)
    return _unit(n), area


def _nearest(pts, seeds):
    """Index of the nearest seed for every point (chunked, no scipy needed)."""
    out = np.empty(len(pts), dtype=np.int64)
    s2 = (seeds * seeds).sum(1)[None, :]
    step = max(1, int(6e6 // max(len(seeds), 1)))
    for i in range(0, len(pts), step):
        p = pts[i:i + step]
        d = (p * p).sum(1)[:, None] + s2 - 2.0 * p @ seeds.T
        out[i:i + step] = d.argmin(1)
    return out


def _wmean(vals, ids, wts, n):
    den = np.bincount(ids, weights=wts, minlength=n)
    out = np.stack([np.bincount(ids, weights=wts * vals[:, k], minlength=n) for k in range(vals.shape[1])], axis=1)
    return (out / np.maximum(den, 1e-12)[:, None]).astype(np.float32), den


def _decimate(tri, nrm, uv, cells_per_unit):
    """Vertex clustering: every vertex moves to the mean of its grid cell; collapsed triangles go."""
    V = tri.reshape(-1, 3)
    key = np.floor(V * cells_per_unit).astype(np.int64) + 4096
    k = (key[:, 0] << 26) | (key[:, 1] << 13) | key[:, 2]
    uniq, inv = np.unique(k, return_inverse=True)
    n = len(uniq)
    ones = np.ones(len(V))
    rep, _ = _wmean(V, inv, ones, n)
    repn, _ = _wmean(nrm.reshape(-1, 3), inv, ones, n)
    vid = inv.reshape(-1, 3)
    good = (vid[:, 0] != vid[:, 1]) & (vid[:, 1] != vid[:, 2]) & (vid[:, 0] != vid[:, 2])
    vid = vid[good]
    srt = np.sort(vid, axis=1)
    _, first = np.unique(srt, axis=0, return_index=True)
    first.sort()
    vid = vid[first]
    return rep[vid], _unit(repn[vid]), uv[good][first]


def _subdivide(att, maxedge, maxtris):
    """Longest-edge bisection until no edge is longer than maxedge. att: (nt,3,C), xyz first."""
    for _ in range(40):
        P = att[:, :, :3]
        e = np.stack([np.linalg.norm(P[:, (k + 1) % 3] - P[:, k], axis=1) for k in range(3)], axis=1)
        k = e.argmax(1)
        m = e.max(1) > maxedge
        if not m.any() or len(att) + m.sum() > maxtris:
            break
        a = att[m]
        kk = k[m]
        idx = np.arange(len(a))
        v0 = a[idx, kk]
        v1 = a[idx, (kk + 1) % 3]
        v2 = a[idx, (kk + 2) % 3]
        mid = 0.5 * (v0 + v1)
        c1 = np.stack([v0, mid, v2], axis=1)
        c2 = np.stack([mid, v1, v2], axis=1)
        att = np.concatenate([att[~m], c1, c2], axis=0)
    return att


def _outer_skin(tri, nrm, thick, n=128):
    """For a model built as a thin double wall (an outer sheet and, a hair inside it, a second
    sheet facing the hollow): True for the triangles to keep as the skin. The lining is the skin
    moved inward by `thick`, so a sheet that faces a hollow puts its lining outside the object.

    "Outside" is counted in steps of a flood fill of a voxel grid (n cells on the longest side)
    from the bounding box inward: the fewer steps to the air in front of a triangle, the more
    exposed it is. Two rules, each for a triangle that has another one back to back with it:
    - within a hair (the double wall): keep the one whose front is nearer the open air; where both
      sides are about as near (rods and rings thinner than a few cells) keep the one that bulges
      toward its own normals;
    - within reach of the lining (a thin wall, like the inside of a vase seen through its mouth):
      drop the one that is clearly the deeper of the two.
    Everything else is kept."""
    BIG = 1 << 30
    P = tri.reshape(-1, 3)
    lo, hi = P.min(0), P.max(0)
    h = float((hi - lo).max()) / n
    dims = np.ceil((hi - lo) / h).astype(int) + 5
    org = lo - 2.0 * h

    def vox(p):
        return np.clip(np.floor((p - org) / h).astype(np.int64), 0, dims - 1)
    fine = _subdivide(tri.copy(), h * 0.7, 4000000)
    occ = np.zeros(dims, dtype=bool)
    for pts in (fine.reshape(-1, 3), fine.mean(1), 0.5 * (fine + np.roll(fine, 1, axis=1)).reshape(-1, 3)):
        v = vox(pts)
        occ[v[:, 0], v[:, 1], v[:, 2]] = True
    free = ~occ
    ext = np.zeros(dims, dtype=bool)
    ext[0], ext[-1], ext[:, 0], ext[:, -1], ext[:, :, 0], ext[:, :, -1] = True, True, True, True, True, True
    steps = np.full(dims, BIG, dtype=np.int64)
    steps[ext] = 0
    for it in range(1, 4 * int(dims.sum())):
        g = ext.copy()
        g[1:] |= ext[:-1]
        g[:-1] |= ext[1:]
        g[:, 1:] |= ext[:, :-1]
        g[:, :-1] |= ext[:, 1:]
        g[:, :, 1:] |= ext[:, :, :-1]
        g[:, :, :-1] |= ext[:, :, 1:]
        g &= free
        new = g & ~ext
        if not new.any():
            break
        steps[new] = it
        ext = g
    fn, area = _face(tri)
    cen = tri.mean(1)

    def air(sign, reach):
        """Fewest flood steps to the air within `reach` cells of that side of each triangle (10**6: none)."""
        out = np.full(len(tri), BIG, dtype=np.int64)
        for d in np.arange(1.0, reach + 0.01, 0.65):
            v = vox(cen + sign * fn * (d * h))
            out = np.minimum(out, steps[v[:, 0], v[:, 1], v[:, 2]])
        return np.minimum(out, 10 ** 6)

    axis = np.abs(fn).argmax(1)
    facing = 2 * axis + (fn[np.arange(len(fn)), axis] < 0)        # 0..5: +x -x +y -y +z -z

    def partner(size):
        """True where a triangle facing the other way (by the main axis of its normal) lies within
        about `size` of a point a little behind this one."""
        def keys(p, face):
            c = np.floor((p - lo) / size).astype(np.int64) + 8
            return ((c[:, 0] * 8192 + c[:, 1]) * 8192 + c[:, 2]) * 8 + face
        have = np.unique(keys(cen, facing))
        q = cen - fn * (0.5 * size)
        found = np.zeros(len(tri), dtype=bool)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    found |= np.isin(keys(q + np.array([dx, dy, dz]) * size, facing ^ 1), have)
        return found
    # do the normals at the corners spread apart (the sheet bulges toward its normal) or close in?
    bulge = sum(((nrm[:, (k + 1) % 3] - nrm[:, k]) * (tri[:, (k + 1) % 3] - tri[:, k])).sum(1) for k in range(3))
    front, back = air(1.0, 3.0), air(-1.0, 3.0)
    keep = np.where(np.abs(front - back) <= 4, bulge >= 0.0, front < back) | ~partner(0.004)
    reach = thick / h + 2.0
    keep &= ~(partner(max(thick, 0.012)) & (air(1.0, reach) > air(-1.0, reach) + 4))
    return keep


def bake(tri, nrm, uv, cfg, seed=7):
    """Returns (atlas float32, info dict)."""
    rng = np.random.default_rng(seed)
    tri = np.asarray(tri, dtype=np.float32)
    has_uv = uv is not None
    has_n = nrm is not None
    if not has_uv:
        uv = np.zeros(tri.shape[:2] + (2,), dtype=np.float32)
    if not has_n:
        nrm = np.repeat(_face(tri)[0][:, None, :], 3, axis=1)

    if cfg.get('shell'):
        keep = _outer_skin(tri, nrm, float(cfg.get('thick', 0.02)))
        tri, nrm, uv = tri[keep], nrm[keep], uv[keep]
    if cfg.get('yaw'):
        # turn the model about the vertical so its best side faces the camera
        ca, sa = np.cos(np.radians(cfg['yaw'])), np.sin(np.radians(cfg['yaw']))
        tri = np.stack([ca * tri[..., 0] + sa * tri[..., 2], tri[..., 1], ca * tri[..., 2] - sa * tri[..., 0]], axis=-1).astype(np.float32)
        nrm = np.stack([ca * nrm[..., 0] + sa * nrm[..., 2], nrm[..., 1], ca * nrm[..., 2] - sa * nrm[..., 0]], axis=-1).astype(np.float32)
    if cfg.get('scale'):
        tri = tri * np.float32(cfg['scale'])
    if cfg.get('faceup'):
        # lay a wall-hung object on its back: +z becomes +y
        tri = np.stack([tri[..., 0], tri[..., 2], -tri[..., 1]], axis=-1)
        nrm = np.stack([nrm[..., 0], nrm[..., 2], -nrm[..., 1]], axis=-1)
    # stand on the floor, centred in x and z
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    if 'width' in cfg and cfg['kind'] == 'text':
        s = cfg['width'] / max(hi[0] - lo[0], 1e-6)
        tri = tri * s
        lo, hi = lo * s, hi * s
    tri = tri - np.array([(lo[0] + hi[0]) * 0.5, lo[1], (lo[2] + hi[2]) * 0.5], dtype=np.float32)

    if cfg.get('decimate'):
        # coarsen the grid until the skin fits the triangle budget (inner skin and walls triple it)
        cap = cfg.get('cap') or (31000 if (cfg.get('thick', 0) > 0 and cfg.get('inner', True)) else 70000)
        g = float(cfg['decimate'])
        src = (tri, nrm, uv)
        for _ in range(12):
            tri, nrm, uv = _decimate(src[0], src[1], src[2], g)
            if len(tri) <= cap:
                break
            g *= 0.88
    _, area = _face(tri)
    keep = area > 1e-10
    tri, nrm, uv = tri[keep], nrm[keep], uv[keep]
    if cfg.get('maxedge'):
        inner_mult = 2 if (cfg.get('thick', 0) > 0 and cfg.get('inner', True)) else 1
        att = _subdivide(np.concatenate([tri, nrm, uv], axis=2), cfg['maxedge'], 29000 if inner_mult == 2 else 70000)
        tri, nrm, uv = att[:, :, :3], _unit(att[:, :, 3:6]), att[:, :, 6:8]
    K0, K1, K2 = cfg['cells']

    def weld(t):
        V = t.reshape(-1, 3)
        q = np.round(V * 20000.0).astype(np.int64) + (1 << 20)
        key = (q[:, 0] << 42) | (q[:, 1] << 21) | q[:, 2]
        uniq, first, inv = np.unique(key, return_index=True, return_inverse=True)
        return V[first], inv.reshape(len(t), 3)

    # ---- fine cells: true Voronoi regions, with the triangles cut along the cell borders so
    # the fracture lines are straight instead of following the mesh's own edges ----
    _, area = _face(tri)
    K1 = min(K1, len(tri), W)
    seeds1 = tri.mean(1)[rng.choice(len(tri), K1, replace=False, p=area / area.sum())]
    def split(tri, nrm, uv, lab, tfun):
        """Cut every triangle whose corners carry exactly two labels. tfun(pa, pb, la, lb) gives
        the cut position 0..1 along pa->pb, where la is the odd corner's label."""
        l0, l1, l2 = lab[:, 0], lab[:, 1], lab[:, 2]
        same = (l0 == l1) & (l1 == l2)
        three = (l0 != l1) & (l1 != l2) & (l0 != l2)
        two = ~same & ~three
        if not two.any():
            return tri, nrm, uv
        att = np.concatenate([tri, nrm, uv], axis=2)
        a2 = att[two]
        lb = lab[two]
        odd = np.where(lb[:, 0] == lb[:, 1], 2, np.where(lb[:, 1] == lb[:, 2], 0, 1))
        idx = np.arange(len(a2))
        p0, p1, p2 = a2[idx, odd], a2[idx, (odd + 1) % 3], a2[idx, (odd + 2) % 3]
        la, lo_ = lb[idx, odd], lb[idx, (odd + 1) % 3]
        t1 = np.clip(tfun(p0, p1, la, lo_), 0.03, 0.97)[:, None]
        t2 = np.clip(tfun(p0, p2, la, lo_), 0.03, 0.97)[:, None]
        m1, m2 = p0 + (p1 - p0) * t1, p0 + (p2 - p0) * t2
        att = np.concatenate([att[~two], np.stack([p0, m1, m2], axis=1), np.stack([m1, p1, p2], axis=1),
                              np.stack([m1, p2, m2], axis=1)], axis=0)
        tri, nrm, uv = att[:, :, :3], _unit(att[:, :, 3:6]), att[:, :, 6:8]
        keep = _face(tri)[1] > 1e-11
        return tri[keep], nrm[keep], uv[keep]

    # slab planes first (the shader's slab mode slices along y, SLABS per unit): clean cuts there too
    def t_slab(pa, pb, la, lb):
        yb = np.maximum(la, lb) / SLABS
        den = pb[:, 1] - pa[:, 1]
        return (yb - pa[:, 1]) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    slab_lab = np.floor(tri[:, :, 1] * SLABS + 1e-6).astype(np.int64)
    tri, nrm, uv = split(tri, nrm, uv, slab_lab, t_slab)

    # one pass: cut corners land on the border, a second pass would shave slivers
    def t_voro(pa, pb, la, lb):
        d = seeds1[lb] - seeds1[la]
        mid = 0.5 * (seeds1[lb] + seeds1[la])
        den = ((pb[:, :3] - pa[:, :3]) * d).sum(1)
        return ((mid - pa[:, :3]) * d).sum(1) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    vpos, vid = weld(tri)
    tri, nrm, uv = split(tri, nrm, uv, _nearest(vpos, seeds1)[vid], t_voro)
    fn, area = _face(tri)
    if not has_n:
        nrm = np.repeat(fn[:, None, :], 3, axis=1)
    nt = len(tri)
    vpos, vid = weld(tri)
    nvert = len(vpos)
    inv = vid.reshape(-1)
    # inset direction per welded vertex: area-weighted face normals
    fw = np.repeat(fn * area[:, None], 3, axis=0)
    vnorm = _unit(np.stack([np.bincount(inv, weights=fw[:, k], minlength=nvert) for k in range(3)], axis=1)).astype(np.float32)

    cen = tri.mean(1)
    fine = _nearest(cen, seeds1)
    # micro cells nest inside the fine cells
    K0 = min(K0, nt, MICRO_ROWS * W)
    seeds0 = cen[rng.choice(nt, K0, replace=False, p=area / area.sum())]
    pair = fine * np.int64(K0) + _nearest(cen, seeds0)
    upair, micro = np.unique(pair, return_inverse=True)
    if len(upair) > MICRO_ROWS * W:
        micro = micro % (MICRO_ROWS * W)
        upair = upair[:MICRO_ROWS * W]
    K0 = len(upair)
    mp, marea = _wmean(cen, micro, area, K0)
    fine_of_micro = np.zeros(K0, dtype=np.int64)
    fine_of_micro[micro] = fine
    fp, farea = _wmean(cen, fine, area, K1)
    emptyf = farea <= 0
    fp[emptyf] = seeds1[emptyf]
    fnorm, _ = _wmean(fn, fine, area, K1)
    fnorm = _unit(fnorm)
    # coarse seeds by farthest point sampling, so the big pieces are evenly sized
    K2 = min(K2, K1, W)
    pick = [int(rng.integers(K1))]
    d = np.linalg.norm(fp - fp[pick[0]], axis=1)
    for _ in range(K2 - 1):
        j = int(d.argmax())
        pick.append(j)
        d = np.minimum(d, np.linalg.norm(fp - fp[j], axis=1))
    coarse_of_fine = _nearest(fp, fp[pick])
    coarse = coarse_of_fine[fine]
    cp, carea = _wmean(cen, coarse, area, K2)

    thick = float(cfg.get('thick', 0.0))
    P = [tri]
    N = [nrm]
    UV = [uv]
    KIND = [np.zeros(nt, dtype=np.float32)]
    SRC = [np.arange(nt)]
    nwall = 0
    if thick > 0:
        inset = tri - vnorm[vid] * thick
        if cfg.get('inner', True):
            P.append(inset[:, ::-1])
            N.append(-nrm[:, ::-1])
            UV.append(uv[:, ::-1])
            KIND.append(np.ones(nt, dtype=np.float32))
            SRC.append(np.arange(nt))
        # walls on fine-cell boundaries
        ea = vid.reshape(-1)                                # corner k of triangle t
        eb = np.roll(vid, -1, axis=1).reshape(-1)           # next corner
        et = np.repeat(np.arange(nt), 3)
        ek = np.tile(np.arange(3), nt)
        ekey = np.minimum(ea, eb) * np.int64(nvert) + np.maximum(ea, eb)
        order = np.argsort(ekey, kind='stable')
        sk = ekey[order]
        same_next = np.zeros(len(sk), dtype=bool)
        same_next[:-1] = sk[1:] == sk[:-1]
        same_prev = np.zeros(len(sk), dtype=bool)
        same_prev[1:] = same_next[:-1]
        cell_s = fine[et[order]]
        differs = np.zeros(len(sk), dtype=bool)
        differs[:-1] |= same_next[:-1] & (cell_s[1:] != cell_s[:-1])
        differs[1:] |= same_prev[1:] & (cell_s[1:] != cell_s[:-1])
        if cfg.get('open_walls', False):
            differs |= ~(same_next | same_prev)
        he = order[differs]
        t, k = et[he], ek[he]
        k1 = (k + 1) % 3
        a, b = tri[t, k], tri[t, k1]
        a2, b2 = inset[t, k], inset[t, k1]
        wn = _unit(np.cross(b - a, fn[t]))
        w1 = np.stack([a, a2, b], axis=1)
        w2 = np.stack([b, a2, b2], axis=1)
        wnn = np.repeat(wn[:, None, :], 3, axis=1)
        wuv = np.stack([uv[t, k], uv[t, k], uv[t, k1]], axis=1)
        for w in (w1, w2):
            P.append(w)
            N.append(wnn)
            UV.append(wuv)
            KIND.append(np.full(len(t), 2.0, dtype=np.float32))
            SRC.append(t)
        nwall = 2 * len(t)

    P = np.concatenate(P)
    N = np.concatenate(N)
    UV = np.concatenate(UV)
    KIND = np.concatenate(KIND)
    SRC = np.concatenate(SRC)
    ntot = len(P)
    if ntot > MAX_TRIS:
        raise ValueError('too many triangles: %d (skin %d, wall %d)' % (ntot, nt, nwall))
    nv = ntot * 3
    H = int(np.ceil(nv / W))
    atlas = np.zeros((3 * H + TABLE_ROWS, W, 4), dtype=np.float32)
    rnd = rng.random(nt).astype(np.float32)[SRC]

    def layer(i):
        return atlas[i * H:(i + 1) * H].reshape(-1, 4)[:nv]
    L0, L1, L2 = layer(0), layer(1), layer(2)
    L0[:, :3] = P.reshape(-1, 3)
    L0[:, 3] = np.repeat(fine[SRC], 3)
    L1[:, :3] = N.reshape(-1, 3)
    L1[:, 3] = np.repeat(micro[SRC], 3)
    L2[:, :2] = UV.reshape(-1, 2)
    L2[:, 2] = np.repeat(KIND, 3)
    L2[:, 3] = np.repeat(cen[SRC, 1], 3)     # height of the source triangle's centre: the slab it belongs to
    B = 3 * H
    mt = atlas[B:B + MICRO_ROWS].reshape(-1, 4)
    mt[:K0, :3] = mp
    mt[:K0, 3] = fine_of_micro
    atlas[B + 4, :K1, :3] = fp
    atlas[B + 4, :K1, 3] = coarse_of_fine
    atlas[B + 5, :K1, :3] = fnorm
    atlas[B + 5, :K1, 3] = np.sqrt(farea)
    atlas[B + 6, :K2, :3] = cp
    atlas[B + 6, :K2, 3] = np.sqrt(carea)
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    atlas[B + 7, 0] = (nv, K0, K1, K2)
    atlas[B + 7, 1] = (lo[0], lo[1], lo[2], 1.0 if has_uv else 0.0)
    atlas[B + 7, 2] = (hi[0], hi[1], hi[2], thick)
    atlas[B + 7, 3, :3] = (cen * area[:, None]).sum(0) / area.sum()
    info = dict(tris_skin=int(nt), tris_wall=int(nwall), tris_total=int(ntot), rows=int(atlas.shape[0]),
                cells=(int(K0), int(K1), int(K2)), size=[round(float(x), 3) for x in (hi - lo)])
    return atlas, info


def subjects(words):
    """The whole subject table: the pack's models and phrases (WORDS in build.py, or a pack's own
    words.json) in that order, then the ones every pack shares (SUBJECTS)."""
    out = {}
    for name, row in words['MODELS'].items():
        out[name] = dict({k: v for k, v in row.items() if k != 'standin'}, kind='model')
    for name, row in words['PHRASES'].items():
        out[name] = dict(row, kind='text')
    out.update(SUBJECTS)
    return out


def default_assets():
    """The assets folder for a shell run: the TDH_ASSETS variable, the folder named in
    <repo>/assets.local.txt, or <repo>/assets (this file is <repo>/experiments/sc_shatter/bake.py)."""
    repo = os.path.dirname(os.path.dirname(HERE))
    local = ''
    try:
        with open(os.path.join(repo, 'assets.local.txt'), encoding='utf-8') as fh:
            local = fh.readline().strip()
    except OSError:
        pass
    return os.environ.get('TDH_ASSETS') or (local if local and os.path.isdir(local) else '') or os.path.join(repo, 'assets')


def load_words(assets):
    """For a shell run: WORDS as written in build.py (read as text: build.py needs TouchDesigner),
    with the names that <assets>/scenes/sc_shatter/words.json replaces, as mod.paths.words does."""
    import ast
    import json
    tree = ast.parse(open(os.path.join(HERE, 'build.py'), encoding='utf-8').read())
    words = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'WORDS':
            words = ast.literal_eval(node.value)
    path = os.path.join(assets, 'scenes', os.path.basename(HERE), 'words.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            for key, value in json.load(fh).items():
                if key in words and type(value) is type(words[key]):
                    words[key] = value
    return words


def signature(cfg, model_path=None, font_path=''):
    """What an atlas was baked from, as text. It is written beside the atlas (<name>.sig) and
    compared before the atlas is reused, so a pack that gives a subject another model, phrase or
    setting gets a new bake instead of the old atlas."""
    import json
    if cfg['kind'] == 'model':
        src = [os.path.basename(os.path.dirname(model_path)), os.path.getsize(model_path)]
    elif cfg['kind'] == 'text':
        src = [os.path.basename(font_path or '')]
    else:
        src = []
    return json.dumps({'cfg': cfg, 'src': src}, sort_keys=True)


def is_current(name, cache_dir, sig):
    """True when cache_dir holds this subject's atlas and it was baked from `sig`."""
    try:
        with open(os.path.join(cache_dir, name + '.sig'), encoding='utf-8') as fh:
            return fh.read() == sig and os.path.exists(os.path.join(cache_dir, name + '.npy'))
    except OSError:
        return False


def bake_subject(name, cfg, cache_dir, model_path=None, fallback=False, font_path=''):
    """Bake one subject (cfg: its row of subjects()) into cache_dir/<name>.npy, with <name>.sig.

    model_path: the OBJ of a 'model' subject (default: the library model in default_assets()).
    fallback: model_path is a stand-in (TouchDesigner's teapot), not the library model: it is
    scaled to suit the takes (FALLBACK_SIZE) and subdivided, since the take
    settings were tuned for meshes of that size and density.
    font_path: the face a 'text' subject was set in ('' = the default face); only recorded."""
    asked = cfg
    if cfg['kind'] == 'model':
        if model_path is None:
            model_path = os.path.join(default_assets(), 'models', cfg['slug'], 'model.obj')
        if not os.path.exists(model_path):
            return None, 'no model file (no assets folder?): build.py bakes the teapot stand-in instead'
        tri, nrm, uv = load_obj(model_path)
        if fallback:
            flat = tri.reshape(-1, 3)
            size = 1.0 if cfg.get('instanced') else FALLBACK_SIZE
            tri = tri * (size / max(float((flat.max(0) - flat.min(0)).max()), 1e-6))
            cfg = {k: v for k, v in cfg.items() if k not in ('scale', 'yaw')}    # tuned for the model, not the teapot
            if not cfg.get('maxedge') and not cfg.get('decimate'):
                cfg = dict(cfg, maxedge=FALLBACK_MAXEDGE)
    elif cfg['kind'] == 'panel':
        tri, nrm, uv = make_panel(cfg['width'], cfg['depth'])
    else:
        raw = os.path.join(cache_dir, 'raw_' + name + '.npy')
        if not os.path.exists(raw):
            return None, 'no raw text mesh yet (build.py dumps it from the Text POP)'
        tri, nrm, uv = np.load(raw).reshape(-1, 3, 3), None, None
    for attempt in range(5):
        try:
            atlas, info = bake(tri, nrm, uv, cfg, seed=7 + sum(map(ord, name)))
            break
        except ValueError:
            # a stand-in (another machine's default face, the teapot) can pass the triangle budget
            # the real subjects were tuned to fit: bake it coarser instead of failing the build
            if not fallback or attempt == 4:
                raise
            cfg = dict(cfg, maxedge=cfg.get('maxedge', FALLBACK_MAXEDGE) * 1.4)
    np.save(os.path.join(cache_dir, name + '.npy'), atlas)
    with open(os.path.join(cache_dir, name + '.sig'), 'w', encoding='utf-8') as fh:
        fh.write(signature(asked, model_path, font_path))
    return atlas, info


if __name__ == '__main__':
    import time
    args = sys.argv[1:]
    noassets = '--noassets' in args
    teapot = assets = None
    names = []
    while args:
        a = args.pop(0)
        if a == '--teapot':
            teapot = args.pop(0)
        elif a == '--assets':
            assets = args.pop(0)
        elif a != '--noassets':
            names.append(a)
    if noassets and not teapot:
        sys.exit('--noassets needs --teapot <path of UtahTeapot.obj in the Samples/Geo folder of TouchDesigner>')
    cache = os.path.join(HERE, 'cache')
    os.makedirs(os.path.join(cache, NOASSETS), exist_ok=True)
    assets = assets or default_assets()
    table = subjects(load_words(assets))
    font = os.path.join(assets, 'fonts', 'ArchivoBlack-Regular.ttf')
    font = font if os.path.exists(font) else ''
    if names == ['all'] or not names:
        names = list(table)
    for n in names:
        t0 = time.time()
        cfg = table[n]
        kind = cfg['kind']
        if kind == 'panel':
            a, info = bake_subject(n, cfg, cache)       # no asset in it: one bake serves both
        elif noassets:
            a, info = bake_subject(n, cfg, os.path.join(cache, NOASSETS), teapot, fallback=True)
        elif kind == 'model':
            a, info = bake_subject(n, cfg, cache, os.path.join(assets, 'models', cfg['slug'], 'model.obj'))
        else:
            a, info = bake_subject(n, cfg, cache, font_path=font)
        print(n, info, '%.2fs' % (time.time() - t0))
