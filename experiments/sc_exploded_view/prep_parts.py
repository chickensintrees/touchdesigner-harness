# Offline (plain Python + numpy): take one model of the asset pack apart and write the parts file
# the scene explodes (takes 0, 2 and 7).
#
#     python prep_parts.py                      the committed file: the lander, 63 parts
#     python prep_parts.py amphora --parts 48   another model
#
# How a model is cut. Its surface is welded and split into connected shapes (an hourglass is posts,
# discs, glass and sand that never touch). Shapes smaller than --small triangles join the nearest
# larger one. Any shape with more than its share of triangles is cut again into chunks of
# neighbouring triangles (k-means on the triangle centres), so a model that is one closed skin
# still comes apart, as shards. Nothing is modelled here: every triangle is the model's own.
#
# The file format (also what a pack's own scenes/sc_exploded_view/meshes/*.obj must be):
#   v   the model's vertices, unchanged
#   vn  one per part, NOT a normal: (centre x, order + 1 + f, centre z), where order is the part's
#       place in the landing order (0 first), and f = 0.9 * (centre y - y_lo) / y_span carries the
#       centre's height. order + 1 = 0 marks a base that never flies (this cutter makes none).
#       The key data rides in the normal slot because a GLSL MAT on a POP draws nothing once the
#       shader touches Tex or a custom attribute (NOTES.md log 02); the drawing takes its normals
#       from screen-space derivatives instead.
#   f   a//k b//k c//k   with k the part
# and beside it a .json: keys (how many parts fly), centroids [x, z] and centroids3 [x, y, z] in
# landing order, y_lo, y_span, size, tris.
import argparse
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = Path(os.environ.get('TDH_ASSETS') or HERE.parents[1] / 'assets')


def read_obj(path):
    v, f = [], []
    for line in open(path, encoding='utf-8', errors='replace'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            v.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            idx = [int(c.split('/')[0]) - 1 for c in p[1:]]
            for i in range(1, len(idx) - 1):
                f.append([idx[0], idx[i], idx[i + 1]])
    return np.array(v), np.array(f)


def components(faces, n):
    """Label of each face: faces that share a vertex are one shape."""
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in faces:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    roots = np.array([find(a) for a in faces[:, 0]])
    _, lab = np.unique(roots, return_inverse=True)
    return lab


def kmeans(pts, k, rounds=25):
    """Chunks of neighbouring points; farthest-point start, so the result is the same every run."""
    cen = [pts[np.argmin(pts[:, 1])]]
    d = np.linalg.norm(pts - cen[0], axis=1)
    for _ in range(k - 1):
        cen.append(pts[np.argmax(d)])
        d = np.minimum(d, np.linalg.norm(pts - cen[-1], axis=1))
    cen = np.array(cen)
    lab = np.zeros(len(pts), int)
    for _ in range(rounds):
        lab = np.argmin(((pts[:, None, :] - cen[None, :, :]) ** 2).sum(2), axis=1)
        for j in range(k):
            if (lab == j).any():
                cen[j] = pts[lab == j].mean(0)
    return lab


def cut(v, faces, want, small):
    # weld identical positions, so a shape is what is really joined
    _, weld = np.unique(np.round(v, 5), axis=0, return_inverse=True)
    weld = weld.ravel()
    wf = weld[faces]
    fc = v[faces].mean(1)                                  # triangle centres
    area = 0.5 * np.linalg.norm(np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]]), axis=1)
    lab = components(wf, weld.max() + 1)
    count = np.bincount(lab)
    big = [k for k in range(len(count)) if count[k] >= small]
    centre = {k: fc[lab == k].mean(0) for k in big}
    for k in range(len(count)):                            # crumbs join the nearest real shape
        if count[k] < small:
            c = fc[lab == k].mean(0)
            lab[lab == k] = min(big, key=lambda b: np.linalg.norm(centre[b] - c))
    # every shape gets chunks in proportion to its surface, at least one
    total = area.sum()
    part = np.zeros(len(faces), int)
    n = 0
    for k in big:
        sel = np.where(lab == k)[0]
        share = int(round(want * area[sel].sum() / total))
        if share <= 1:
            part[sel] = n
            n += 1
            continue
        sub = kmeans(fc[sel], share)
        for j in np.unique(sub):
            part[sel[sub == j]] = n
            n += 1
    return tidy(part, wf), n


def tidy(part, wf, rounds=6):
    """Straighten the chunk borders: a triangle with two neighbours in another chunk joins that chunk.
    (k-means on triangle centres leaves a saw-tooth edge, one triangle deep.)"""
    edges = np.sort(np.concatenate([wf[:, [0, 1]], wf[:, [1, 2]], wf[:, [2, 0]]]), axis=1)
    face = np.tile(np.arange(len(wf)), 3)
    slot = np.repeat(np.arange(3), len(wf))
    order = np.lexsort((edges[:, 1], edges[:, 0]))
    e, f, sl = edges[order], face[order], slot[order]
    same = (e[1:] == e[:-1]).all(1)                       # consecutive rows share an edge
    nb = np.full((len(wf), 3), -1)
    i = np.where(same)[0]
    nb[f[i], sl[i]] = f[i + 1]
    nb[f[i + 1], sl[i + 1]] = f[i]
    for _ in range(rounds):
        lab = np.where(nb >= 0, part[np.maximum(nb, 0)], -1)
        for a, b in ((0, 1), (1, 2), (0, 2)):
            move = (lab[:, a] == lab[:, b]) & (lab[:, a] >= 0) & (lab[:, a] != part)
            part = np.where(move, lab[:, a], part)
    return part


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model', nargs='?', default='lander')
    ap.add_argument('--parts', type=int, default=60, help='about how many parts')
    ap.add_argument('--small', type=int, default=60, help='shapes with fewer triangles join a neighbour')
    ap.add_argument('--out', default='parts', help='file name under meshes/, without extension')
    a = ap.parse_args()
    v, faces = read_obj(ASSETS / 'models' / a.model / 'model.obj')
    part, n = cut(v, faces, a.parts, a.small)
    lo = np.zeros((n, 3))
    hi = np.zeros((n, 3))
    for k in range(n):
        pts = v[np.unique(faces[part == k])]
        lo[k], hi[k] = pts.min(0), pts.max(0)
    cent = (lo + hi) / 2
    # landing order: from the ground up, and round the object within each level
    level = np.floor((cent[:, 1] - v[:, 1].min()) / max(np.ptp(v[:, 1]), 1e-6) * 8.0)
    order = np.lexsort((np.arctan2(cent[:, 2], cent[:, 0]), level))
    rank = np.zeros(n, int)
    rank[order] = np.arange(n)
    y_lo = float(cent[:, 1].min())
    y_span = float(np.ptp(cent[:, 1])) or 1.0
    (HERE / 'meshes').mkdir(exist_ok=True)
    with open(HERE / 'meshes' / (a.out + '.obj'), 'w', encoding='utf-8', newline='\n') as o:
        o.write('# %s cut into %d parts; see prep_parts.py\n' % (a.model, n))
        for p in v:
            o.write('v %.5f %.5f %.5f\n' % tuple(p))
        for k in range(n):
            o.write('vn %.5f %.6f %.5f\n' % (cent[k, 0], rank[k] + 1 + 0.9 * (cent[k, 1] - y_lo) / y_span, cent[k, 2]))
        for f, k in zip(faces, part):
            o.write('f %d//%d %d//%d %d//%d\n' % (f[0] + 1, k + 1, f[1] + 1, k + 1, f[2] + 1, k + 1))
    info = {
        'source': a.model, 'keys': n, 'tris': int(len(faces)),
        'size': np.round(np.ptp(v, axis=0), 4).tolist(),
        'bounds': [np.round(v.min(0), 4).tolist(), np.round(v.max(0), 4).tolist()],
        'y_lo': round(y_lo, 5), 'y_span': round(y_span, 5),
        'tris_per_part': [int(x) for x in np.bincount(part)[order]],
        'centroids': [[round(float(cent[k, 0]), 4), round(float(cent[k, 2]), 4)] for k in order],
        'centroids3': [[round(float(x), 4) for x in cent[k]] for k in order],
    }
    with open(HERE / 'meshes' / (a.out + '.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(info, fh, indent=1)
    print({k: x for k, x in info.items() if not k.startswith('centroids')})


if __name__ == '__main__':
    main()
