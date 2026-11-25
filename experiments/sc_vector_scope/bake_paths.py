# Offline baker for sc_vector_scope: turns words and library models into beam paths.
# Run OUTSIDE TouchDesigner (plain python with numpy, matplotlib):
#     python experiments/sc_vector_scope/bake_paths.py
# Writes paths.npz (ROWS x N x 4: x, y, z, pen, packed by load_paths.py) and paths.json (row index
# by name), plus captures/bake_preview.png. The scene's Script TOP loads paths.npz with load_paths.py.
# Both files are committed, so the scene itself never needs the fonts or the models. This baker does:
# it reads <assets>/fonts and <assets>/models (<repo>/assets, or the folder in TDH_ASSETS).
# What it bakes is DEFAULTS in build.py (WORDS, BLOCKS, GLYPHS, FORM, MODELS). When the assets folder
# holds scenes/sc_vector_scope/words.json, those words and models are baked instead and the two files
# are written beside that words.json, not here: a pack's own paths never land in this folder.
# `python bake_paths.py --describe` re-bakes only the Describe-mode rows (words from TAKES in build.py)
# and leaves the picture rows untouched.
# Each row is ONE continuous beam path sampled at equal time steps: the beam dwells on
# corners (repeated samples = bright dots) and crosses gaps in two samples (pen 0 = faint).
# see: experiments/sc_vector_scope/NOTES.md (2026-11-10; Packs 2026-11-11)
import importlib.util
import json
import os
import sys
import types

import numpy as np

from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = os.path.basename(HERE)
REPO = Path(__file__).resolve().parents[2]                  # <repo>/experiments/<slug>/bake_paths.py
ASSETS = Path(os.environ.get('TDH_ASSETS') or REPO / 'assets')
sys.path.insert(0, HERE)
import load_paths  # noqa: E402  the packed format of paths.npz
N = 4096

# The engine's own lookup (a file, else the stand-in the pack's aliases.json names for it), pointed
# at ASSETS: assets.local.txt is deliberately not followed here, so a plain run bakes the shipped pack.
PATHS = {'project': types.SimpleNamespace(folder=REPO.as_posix()), 'app': None, 'me': None}
exec(compile((REPO / 'experiments' / 'sw_hub' / 'paths_module.py').read_text(encoding='utf-8'), 'paths_module.py', 'exec'), PATHS)
PATHS['assets'] = lambda: ASSETS.as_posix()
asset = PATHS['asset']
CHICAGO = PATHS['font']('chicago')
BARLOW = PATHS['font']('barlow')


def scene_build():
    """build.py of this folder as a plain module (it holds DEFAULTS and TAKES)."""
    spec = importlib.util.spec_from_file_location('vs_build', os.path.join(HERE, 'build.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUILD = scene_build()
W = PATHS['words'](BUILD.DEFAULTS, SLUG)                    # the pack's words.json, when it has one
OUT = os.path.dirname(asset('scenes/%s/words.json' % SLUG)) or HERE


def model_obj(slug):
    return asset('models/%s/model.obj' % slug)


# ---------------------------------------------------------------- polylines -> timed path
def sample_path(strokes, n=N, corner_dwell=1.6, jump_cost=2.0, closed_hint=None):
    """strokes: list of (k,3) arrays, drawn in order with a blanked jump between them.

    Returns (n,4): position and pen. Time along the path = length/speed + a dwell at each
    corner in proportion to its turn; n samples are taken at equal time steps.
    """
    pts, pen, cost = [], [], []          # per vertex: position, pen for the segment arriving, time arriving
    total_len = sum(np.linalg.norm(np.diff(s, axis=0), axis=1).sum() for s in strokes)
    nseg = sum(len(s) - 1 for s in strokes)
    # choose speed so that drawing takes most of the samples
    for si, s in enumerate(strokes):
        s = np.asarray(s, dtype=np.float64)
        for i, p in enumerate(s):
            if i == 0:
                pts.append(p); pen.append(0.0); cost.append(('jump', 0.0))
            else:
                d = np.linalg.norm(p - s[i - 1])
                pts.append(p); pen.append(1.0); cost.append(('draw', d))
            # corner dwell: a zero-length pen-down segment
            turn = 0.0
            if 0 < i < len(s) - 1:
                a = s[i] - s[i - 1]
                b = s[i + 1] - s[i]
                na, nb = np.linalg.norm(a), np.linalg.norm(b)
                if na > 1e-9 and nb > 1e-9:
                    turn = np.arccos(np.clip(np.dot(a, b) / (na * nb), -1, 1))
            elif i == 0 or i == len(s) - 1:
                turn = np.pi * 0.6
            if turn > 0.35:
                pts.append(p); pen.append(1.0); cost.append(('dwell', turn / np.pi))
    pts = np.array(pts)
    pen = np.array(pen)
    njump = sum(1 for c in cost if c[0] == 'jump')
    dwell_total = sum(c[1] for c in cost if c[0] == 'dwell') * corner_dwell
    budget = n - njump * jump_cost
    # dwell may take at most 30% of the samples
    dwell_scale = min(1.0, 0.30 * budget / max(dwell_total, 1e-9))
    draw_budget = budget - dwell_total * dwell_scale
    speed = total_len / max(draw_budget, 1.0)
    t = np.zeros(len(pts))
    acc = 0.0
    for i, (kind, v) in enumerate(cost):
        if kind == 'jump':
            acc += jump_cost if i > 0 else 0.0
        elif kind == 'draw':
            acc += v / speed
        else:
            acc += v * corner_dwell * dwell_scale
        t[i] = acc
    # close the loop: time to fly back to the start
    period = acc + jump_cost
    ts = (np.arange(n) + 0.5) / n * period
    idx = np.searchsorted(t, ts, side='right')          # first vertex with t > ts
    idx = np.clip(idx, 1, len(pts))
    out = np.zeros((n, 4), dtype=np.float32)
    for k in range(n):
        j = idx[k]
        if j >= len(pts):                                   # flying home
            a, b = pts[-1], pts[0]
            f = (ts[k] - t[-1]) / jump_cost
            out[k, :3] = a + (b - a) * f
            out[k, 3] = 0.0
            continue
        t0, t1 = t[j - 1], t[j]
        f = 0.0 if t1 - t0 < 1e-12 else (ts[k] - t0) / (t1 - t0)
        out[k, :3] = pts[j - 1] + (pts[j] - pts[j - 1]) * f
        out[k, 3] = pen[j]
    return out


def order_strokes(strokes):
    """Greedy nearest-neighbour order (and direction for open strokes) to shorten the jumps."""
    strokes = [np.asarray(s, dtype=np.float64) for s in strokes if len(s) >= 2]
    if not strokes:
        return strokes
    left = list(range(len(strokes)))
    # start at the leftmost-topmost stroke
    start = min(left, key=lambda i: (strokes[i][0][0] - strokes[i][0][1]))
    order = [strokes[start]]
    left.remove(start)
    while left:
        end = order[-1][-1]
        best, bd, flip = None, 1e18, False
        for i in left:
            d0 = np.linalg.norm(strokes[i][0] - end)
            if d0 < bd:
                best, bd, flip = i, d0, False
        order.append(strokes[best])
        left.remove(best)
    return order


def fit(strokes, half_w=1.0, half_h=0.5):
    allp = np.concatenate(strokes)
    lo, hi = allp.min(0), allp.max(0)
    c = (lo + hi) / 2
    size = np.maximum(hi - lo, 1e-9)
    s = min(2 * half_w / size[0], 2 * half_h / size[1])
    return [(st - c) * s for st in strokes]


# ---------------------------------------------------------------- text
def text_strokes(text, font, line_gap=1.25):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    fp = FontProperties(fname=font)
    strokes = []
    lines = text.split('\n')
    widths = []
    per_line = []
    for li, line in enumerate(lines):
        tp = TextPath((0, 0), line, size=1.0, prop=fp)
        polys = tp.to_polygons(closed_only=False)
        polys = [np.asarray(p) for p in polys if len(p) >= 3]
        if polys:
            allp = np.concatenate(polys)
            w = allp[:, 0].max() - allp[:, 0].min()
            x0 = allp[:, 0].min()
        else:
            w, x0 = 0, 0
        widths.append(w)
        per_line.append((polys, x0))
    for li, (polys, x0) in enumerate(per_line):
        for p in polys:
            q = np.zeros((len(p), 3))
            q[:, 0] = p[:, 0] - x0                      # left aligned, like a terminal
            q[:, 1] = p[:, 1] - li * line_gap
            # drop repeated points
            keep = np.ones(len(q), bool)
            keep[1:] = np.linalg.norm(np.diff(q, axis=0), axis=1) > 1e-5
            q = q[keep]
            if np.linalg.norm(q[0] - q[-1]) > 1e-5:
                q = np.vstack([q, q[:1]])
            strokes.append(q)
    return strokes


def form_strokes():
    """A printed card as a vector drawing: frame, title bar, ruled lines, tick boxes, a stamp circle."""
    s = []

    def rect(x0, y0, x1, y1):
        s.append(np.array([[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0], [x0, y0, 0]], float))

    def line(x0, y0, x1, y1):
        s.append(np.array([[x0, y0, 0], [x1, y1, 0]], float))
    rect(0, 0, 0.77, 1.0)
    rect(0.05, 0.86, 0.72, 0.95)
    for i in range(6):
        y = 0.78 - i * 0.075
        line(0.05, y, 0.45 if i % 2 else 0.72, y)
    for i in range(4):
        y = 0.30 - i * 0.065
        rect(0.05, y - 0.02, 0.09, y + 0.02)
        line(0.12, y - 0.02, 0.40, y - 0.02)
    # a tick in the second box
    s.append(np.array([[0.055, 0.235, 0], [0.068, 0.22, 0], [0.095, 0.26, 0]], float))
    th = np.linspace(0, 2 * np.pi, 33)
    s.append(np.stack([0.58 + 0.1 * np.cos(th), 0.2 + 0.1 * np.sin(th), th * 0], 1))
    s.append(np.stack([0.58 + 0.075 * np.cos(th), 0.2 + 0.075 * np.sin(th), th * 0], 1))
    line(0.50, 0.2, 0.66, 0.2)
    return s


# ---------------------------------------------------------------- models
def load_obj(path):
    vs, fs = [], []
    with open(path, encoding='utf-8', errors='ignore') as f:
        for ln in f:
            if ln.startswith('v '):
                vs.append([float(x) for x in ln.split()[1:4]])
            elif ln.startswith('f '):
                ids = [int(tok.split('/')[0]) - 1 for tok in ln.split()[1:]]
                for k in range(1, len(ids) - 1):
                    fs.append([ids[0], ids[k], ids[k + 1]])
    return np.array(vs), np.array(fs)


def model_strokes(slug, cells, angle_deg, max_edges=520):
    v, f = load_obj(model_obj(slug))
    lo, hi = v.min(0), v.max(0)
    size = (hi - lo).max()
    while True:
        # vertex clustering: every vertex snaps to the mean of its grid cell
        q = np.floor((v - lo) / size * cells * 0.9999).astype(np.int64)
        key = q[:, 0] + q[:, 1] * 1024 + q[:, 2] * 1024 * 1024
        uniq, inv = np.unique(key, return_inverse=True)
        cv = np.zeros((len(uniq), 3))
        cnt = np.zeros(len(uniq))
        np.add.at(cv, inv, v)
        np.add.at(cnt, inv, 1)
        cv /= cnt[:, None]
        tf = inv[f]
        ok = (tf[:, 0] != tf[:, 1]) & (tf[:, 1] != tf[:, 2]) & (tf[:, 0] != tf[:, 2])
        tf = tf[ok]
        tf = np.unique(np.sort(tf, axis=1), axis=0)         # winding is lost; use unsigned normals
        nrm = np.cross(cv[tf[:, 1]] - cv[tf[:, 0]], cv[tf[:, 2]] - cv[tf[:, 0]])
        ln = np.linalg.norm(nrm, axis=1)
        tf, nrm = tf[ln > 1e-12], nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
        edges = {}
        for ti, t in enumerate(tf):
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2])):
                edges.setdefault((min(a, b), max(a, b)), []).append(ti)
        keep = []
        cosang = np.cos(np.radians(angle_deg))
        for (a, b), ts in edges.items():
            if len(ts) == 1:
                keep.append((a, b))
            elif len(ts) == 2:
                if abs(np.dot(nrm[ts[0]], nrm[ts[1]])) < cosang:
                    keep.append((a, b))
            else:
                keep.append((a, b))
        if len(keep) <= max_edges or cells <= 6:
            break
        if angle_deg < 50:
            angle_deg += 4
        else:
            cells -= 1
    # chain edges into strokes: walk straight on where possible, jump when stuck
    adj = {}
    for a, b in keep:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    strokes = []
    cur = min(adj, key=lambda i: cv[i][1])                  # start at the bottom
    prev_dir = None
    stroke = [cur]
    remaining = sum(len(x) for x in adj.values()) // 2
    while remaining > 0:
        nb = adj.get(cur, ())
        if nb:
            if prev_dir is None:
                nxt = next(iter(nb))
            else:
                def straight(j):
                    d = cv[j] - cv[cur]
                    return -np.dot(d / (np.linalg.norm(d) + 1e-12), prev_dir)
                nxt = min(nb, key=straight)
            adj[cur].discard(nxt)
            adj[nxt].discard(cur)
            remaining -= 1
            d = cv[nxt] - cv[cur]
            prev_dir = d / (np.linalg.norm(d) + 1e-12)
            stroke.append(nxt)
            cur = nxt
        else:
            if len(stroke) > 1:
                strokes.append(cv[stroke])
            cand = [i for i, s in adj.items() if s]
            cand_p = cv[cand]
            cur = cand[int(np.argmin(np.linalg.norm(cand_p - cv[cur], axis=1)))]
            stroke = [cur]
            prev_dir = None
    if len(stroke) > 1:
        strokes.append(cv[stroke])
    c = (lo + hi) / 2
    strokes = [(s - c) / size for s in strokes]            # longest side 1, centred
    return strokes, len(keep), cells, angle_deg


def rdp(pts, tol):
    """Ramer-Douglas-Peucker on an open polyline."""
    if len(pts) < 3:
        return pts
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        n = np.linalg.norm(ab)
        seg = pts[i + 1:j] - a
        if n < 1e-12:
            d = np.linalg.norm(seg, axis=1)
        else:
            d = np.linalg.norm(np.cross(seg, ab / n), axis=1)
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return pts[keep]


def slice_strokes(slug, levels=13, extra=((0, 0.5), (2, 0.5)), tol=0.006, min_len=0.12, axis=1):
    """Contour lines: cut the mesh with planes (levels across Y, plus single X and Z profile cuts).

    The generated library meshes are lumpy 30-60k triangle scans; their feature edges are noise,
    but their cross-sections are clean closed curves, like a turned object on a lathe drawing.
    """
    v, f = load_obj(model_obj(slug))
    # weld split vertices by position
    key = np.round(v * 20000).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    v = v[first]
    f = inv[f]
    lo, hi = v.min(0), v.max(0)
    size = (hi - lo).max()
    c = (lo + hi) / 2
    planes = [(axis, lo[axis] + (hi[axis] - lo[axis]) * (i + 0.5) / levels) for i in range(levels)]
    planes += [(ax, lo[ax] + (hi[ax] - lo[ax]) * t) for ax, t in extra]
    strokes = []
    for ax, h in planes:
        d = v[:, ax] - h
        d[d == 0] = 1e-9
        s = d[f] > 0
        cross = s.any(1) & ~s.all(1)
        segs = {}
        pos = {}
        for tri, sg in zip(f[cross], s[cross]):
            ends = []
            for a, b in ((0, 1), (1, 2), (2, 0)):
                if sg[a] != sg[b]:
                    i, j = int(tri[a]), int(tri[b])
                    k = (min(i, j), max(i, j))
                    if k not in pos:
                        t = d[i] / (d[i] - d[j])
                        pos[k] = v[i] + (v[j] - v[i]) * t
                    ends.append(k)
            if len(ends) == 2 and ends[0] != ends[1]:
                segs.setdefault(ends[0], []).append(ends[1])
                segs.setdefault(ends[1], []).append(ends[0])
        used = set()
        for start in list(segs):
            if start in used:
                continue
            # walk both ways from start
            chain = [start]
            used.add(start)
            for direction in (0, 1):
                cur = start
                while True:
                    nxt = [n for n in segs[cur] if n not in used]
                    if not nxt:
                        break
                    cur = nxt[0]
                    used.add(cur)
                    if direction == 0:
                        chain.append(cur)
                    else:
                        chain.insert(0, cur)
            pts = np.array([pos[k] for k in chain])
            closed = chain[0] in segs[chain[-1]] and len(chain) > 2
            if closed:
                pts = np.vstack([pts, pts[:1]])
            pts = (pts - c) / size
            if np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() < min_len:
                continue
            strokes.append(rdp(pts, tol))
    # order: bottom to top, nearest start within a level
    return strokes


# ---------------------------------------------------------------- Describe mode
def describe_groups():
    """The Describe-mode words, read from TAKES in build.py (the one place they are written).

    Returns [(group name, font, (half_w, half_h), [strings])]. A take's words become group
    'd_<take>'; the macro take's giant letters become 'd_<take>_glyph'.
    """
    out = []
    for t in BUILD.TAKES:
        d = t.get('describe')
        if not d:
            continue
        if d.get('glyphs'):
            out.append(('d_%s_glyph' % t['name'], BARLOW, (0.6, 0.6), list(d['glyphs'])))
        if d.get('words'):
            out.append(('d_%s' % t['name'], CHICAGO, (1.0, 0.5), list(d['words'])))
    return out


def add_describe(add):
    for group, font, (hw, hh), words in describe_groups():
        for w in words:
            add(group, w.replace('\n', ' / '), order_strokes(fit(text_strokes(w, font), hw, hh)))


def describe_only():
    """Re-bake only the Describe rows on top of the existing picture rows (which stay byte for byte)."""
    meta = json.load(open(os.path.join(OUT, 'paths.json'), encoding='utf-8'))
    arr = load_paths.decode(np.load(os.path.join(OUT, 'paths.npz')))
    picture = min(v[0] for k, v in meta['groups'].items() if k.startswith('d_')) if any(
        k.startswith('d_') for k in meta['groups']) else meta['rows']
    rows = [arr[i] for i in range(picture)]
    names = meta['names'][:picture]
    groups = {k: v for k, v in meta['groups'].items() if not k.startswith('d_')}

    def add(group, name, strokes, **kw):
        groups.setdefault(group, []).append(len(rows))
        names.append(name)
        rows.append(sample_path(strokes, **kw))
    add_describe(add)
    out = np.stack(rows).astype(np.float32)
    packed = load_paths.encode(out)
    assert np.array_equal(load_paths.decode(packed)[:picture], arr[:picture])     # the picture rows did not move
    np.savez_compressed(os.path.join(OUT, 'paths.npz'), **packed)
    meta.update(rows=len(rows), names=names, groups=groups)
    with open(os.path.join(OUT, 'paths.json'), 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump(meta, f, indent=1)
    print('picture rows kept', picture, 'total', out.shape, {k: (v[0], len(v)) for k, v in groups.items() if k.startswith('d_')})
    preview(rows[picture:], names[picture:], 'bake_preview_describe.png')


def preview(rows, names, fname, cols=7):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    nr = (len(rows) + cols - 1) // cols
    fig, axs = plt.subplots(nr, cols, figsize=(cols * 3, nr * 2.2), facecolor='black', squeeze=False)
    for ax in axs.flat:
        ax.set_facecolor('black'); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal')
    for i, r in enumerate(rows):
        ax = axs.flat[i]
        x, y = r[:, 0], r[:, 1]
        seg = np.stack([np.stack([x[:-1], y[:-1]], 1), np.stack([x[1:], y[1:]], 1)], 1)
        ax.add_collection(LineCollection(seg[r[1:, 3] > 0.5], colors='#66ff88', linewidths=0.5, alpha=0.8))
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(-0.65, 0.65)
        ax.set_title('%d %s' % (i, names[i][:30]), color='w', fontsize=7)
    fig.savefig(os.path.join(HERE, 'captures', fname), dpi=70, facecolor='black')


# ---------------------------------------------------------------- main
def main():
    need = {'fonts (chicago)': CHICAGO, 'fonts (barlow)': BARLOW}
    if '--describe' not in sys.argv:
        need.update(('models/' + m[0], model_obj(m[0])) for m in W['MODELS'])
    missing = [k for k, f in need.items() if not f]
    if missing:
        print('bake_paths.py needs the fonts and models of the assets folder (%s); missing: %s. '
              'The scene does not: paths.npz and paths.json are committed.'
              % (ASSETS.as_posix(), ', '.join(missing[:4])))
        return 1
    print('assets', ASSETS.as_posix(), '-> writing', OUT.replace(chr(92), '/'), flush=True)
    if '--describe' in sys.argv:
        return describe_only()
    rows, names, groups = [], [], {}

    def add(group, name, strokes, **kw):
        groups.setdefault(group, []).append(len(rows))
        names.append(name)
        rows.append(sample_path(strokes, **kw))

    for w in W['WORDS']:
        add('word', w, order_strokes(fit(text_strokes(w, CHICAGO))))
    for b in W['BLOCKS']:
        add('block', b.replace('\n', ' / '), order_strokes(fit(text_strokes(b, CHICAGO), 1.0, 0.5)))
    for g in W['GLYPHS']:
        add('glyph', g, order_strokes(fit(text_strokes(g, BARLOW), 0.6, 0.6)))
    add('form', W['FORM'], fit(form_strokes(), 0.6, 0.6))
    info = {}
    # generated (scanned-looking) meshes are drawn as contour slices; modelled ones keep their feature edges
    for slug, method, *args in W['MODELS']:
        if method == 'slices':
            st = slice_strokes(slug, **(args[0] if args else {}))
            info[slug] = {'method': 'slices', 'strokes': len(st), 'points': int(sum(len(x) for x in st))}
            add('model', slug, st, corner_dwell=0.35)
        else:
            cells, ang = args
            st, ne, c2, a2 = model_strokes(slug, cells, ang)
            info[slug] = {'method': 'edges', 'edges': ne, 'strokes': len(st), 'cells': c2, 'angle': a2}
            add('model', slug, st, corner_dwell=0.5)
        print(slug, info[slug], flush=True)
    add_describe(add)
    arr = np.stack(rows).astype(np.float32)
    assert {g: [names[i] for i in groups[g]] for g in BUILD.baked_names(W)} == BUILD.baked_names(W)   # what build.py will check
    np.savez_compressed(os.path.join(OUT, 'paths.npz'), **load_paths.encode(arr))
    meta = {'n': N, 'rows': len(rows), 'names': names, 'groups': groups, 'models': info}
    with open(os.path.join(OUT, 'paths.json'), 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump(meta, f, indent=1)
    print('rows', arr.shape, {k: (v[0], len(v)) for k, v in groups.items()})

    # preview: every row, points alpha-blended so dwell shows as dark dots
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cols = 7
    nr = (len(rows) + cols - 1) // cols
    fig, axs = plt.subplots(nr, cols, figsize=(cols * 3, nr * 2.2), facecolor='black')
    for ax in axs.flat:
        ax.set_facecolor('black'); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal')
    for i, r in enumerate(rows):
        ax = axs.flat[i]
        ang = 0.5
        x = r[:, 0] * np.cos(ang) + r[:, 2] * np.sin(ang)
        y = r[:, 1] + 0.25 * (-r[:, 0] * np.sin(ang) + r[:, 2] * np.cos(ang))
        seg = np.stack([np.stack([x[:-1], y[:-1]], 1), np.stack([x[1:], y[1:]], 1)], 1)
        from matplotlib.collections import LineCollection
        ax.add_collection(LineCollection(seg[r[1:, 3] > 0.5], colors='#66ff88', linewidths=0.5, alpha=0.8))
        ax.add_collection(LineCollection(seg[r[1:, 3] <= 0.5], colors='#335533', linewidths=0.3, alpha=0.6))
        ax.scatter(x, y, s=0.6, c='white', alpha=0.15, linewidths=0)
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(-0.65, 0.65)
        ax.set_title('%d %s' % (i, names[i][:22]), color='w', fontsize=7)
    os.makedirs(os.path.join(HERE, 'captures'), exist_ok=True)
    fig.savefig(os.path.join(HERE, 'captures', 'bake_preview.png'), dpi=70, facecolor='black')


if __name__ == '__main__':
    sys.exit(main())
