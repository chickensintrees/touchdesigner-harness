# sc_exploded_view: everything that decides what a sheet looks like, once per frame.
# Loaded as a module from the Text DAT 'logic' (and exec'd by build.py for PPU).
# What the sheets say and which models they draw is not here: build.py holds the defaults, a pack may
# replace them, and setup() reads the result from the Text DAT 'words'. see: NOTES.md "Words and models"
# frame(comp) returns the frame's state: 'u' (scalars for uniforms and parameters), 'views'
# (one transform per view, applied by shaders/part_vertex.glsl), 'lines' (annotation geometry
# for shaders/draw.frag) and 'labels' (lettering for the Text TOPs).
# see: experiments/sc_exploded_view/NOTES.md
import math
import json

W, H = 1280.0, 720.0
PPU = 360.0            # pixels per world unit: the ortho camera shows 2 units of height
MAXV = 12              # views (must match the arrays in part_vertex.glsl)
MAXL = 40              # annotation segments (must match draw.frag)
TRI_BUDGET = 2400000    # triangles drawn per frame, all instances together

# Filled by setup() from the Text DAT 'words' (build.py DEFAULTS, or the pack's words.json).
MODELS = []            # rows: name, size in units (x, y, z), triangles, drawing title, catalogue number
PLAIN = []             # the plain name of each model, for Describe
MI = {}                # model name -> row
PHRASES = []
STAMPS = []
POOLS = {}
INPUT_POOLS = {}
CAP_INSIDE = []        # models that are thin shells: see shaders/part_pixel.glsl
TITLE = {}
LAB = {}               # drafting labels
PL = {}                # lettering of the three parts takes
PT = {}                # how the three parts takes frame the parts object, and its file
PARTS = ['parts']      # the name of the parts object's row in MODELS
KEYC = []              # centre of each flying part, in landing order: (x, y, z)
PINFO = {'count': 1, 'ylo': 0.0, 'yspan': 0.0, 'sx': 1.0, 's2': 1.0, 'plane': 0.0}
NKEYS = 1

# Describe mode (the scene's Describe toggle): every word on the sheet says what the viewer is looking
# at. One entry per take, in the order the take uses them; %-fields are filled with live values.
# The lines that name the parts object (takes 0, 2, 7: 'typed', 'leader', 'lines', 'head') come from the
# words as well (PARTS_WORDS) and are merged in by setup().
# Mirrored by hand into preset.json ("words"). Checked against captures describe_take_*.png, 2026-11-11.
STAMPS_D = ['SNARE', 'SNARE HIT', 'ON THE SNARE']
TITLE_D = ['EXPLODED VIEW   LINE ART TRACED FROM A 3D MODEL', 'MODEL: %s', '%d TRIANGLES',
           'SONG SECTION %02d OF 43', 'BAR %03d', 'BEAT %d']
WORDS = {
    'take_iso_keys': {'dim': 'SPREAD X %.2f'},
    'take_three_view': {
        'views': ['FRONT VIEW', 'TOP VIEW', 'SIDE VIEW'],
        'head': 'EXPLODED VIEW: SLICED IN %d, THE KICK SETS THE GAP',
        'note': 'A SHADER CAPS AND HATCHES THE CUT FACES',
        'dims': ['BASS %.2f', 'H %.2f', 'EXPLODE %.2f']},
    'take_macro_keys': {},
    'take_contour_scan': {
        'lines': ['NO OUTLINES.', 'ONLY THE RINGS WHERE', 'PLANES CUT THE SURFACE.'],
        'label': 'CUTTING PLANES, COUNT SET BY THE KICK', 'scan': 'PLANE %03d'},
    'take_parts_sheet': {
        'cell': 'ONE MODEL, 12 ANGLES',
        'foot': 'CELLS OPEN AND CLOSE WITH THE BEAT.  PINK = OPEN.  THE SLICES ARE CUT IN THE SHADER, NOT IN THE MODEL.'},
    'take_section_sweep': {
        'big': 'SECTION CUT', 'sub': 'EACH KICK MOVES THE CUT PLANE.  NOW AT %02d%% OF THE LENGTH',
        'leader': 'HATCHED CUT FACE'},
    'take_rosette': {
        'lines': ['WHEEL STEP %02d OF 12', 'ONE CLICK PER BEAT', 'THE KICK WIDENS THE WHEEL', '12 COPIES OF ONE %s']},
    'take_plan_typed': {'count': 'NOTE ONSETS %05d'},
    'take_slab_strip': {
        'head': '%s CUT INTO %d SLABS.  THE KICK SETS THE SPACING.', 'bar': 'BAR %03d', 'dim': 'EXPLODE %.2f'},
    'take_bill_of_materials': {
        'label': 'BASS LEVEL X 100, LIVE',
        'rows': ['RENDER: NORMAL, DEPTH, PART ID', 'SHADER: A JUMP IN ANY IS A LINE',
                 'NO LIGHTS: ONLY EDGES AND HATCHING', 'SLABS ARE CUT IN THE SHADER',
                 'CUT FACES GET CAPPED AND HATCHED', 'KICK: SETS THE GAP, NOW %.2f',
                 'BEAT: THICKENS THE OUTLINE', 'NEW SONG SECTION: NEW MODEL'],
        'leader': 'SLAB %02d'},
}

# paper rgb, paper style, ink rgb, second ink rgb
PAL = {
    'blueprint': ((0.06, 0.25, 0.50), 1, (0.90, 0.95, 1.00), (1.00, 0.80, 0.30)),
    'cream': ((0.93, 0.89, 0.78), 0, (0.10, 0.17, 0.23), (0.86, 0.30, 0.20)),
    'black': ((0.012, 0.012, 0.014), 3, (1.00, 0.62, 0.14), (1.00, 0.86, 0.52)),
    'red': ((0.66, 0.17, 0.14), 0, (0.96, 0.91, 0.80), (0.07, 0.05, 0.05)),
    'green': ((0.86, 0.89, 0.78), 2, (0.15, 0.22, 0.16), (0.72, 0.30, 0.45)),
    'pink': ((0.95, 0.78, 0.80), 4, (0.12, 0.14, 0.30), (0.80, 0.22, 0.24)),
    'grey': ((0.49, 0.49, 0.47), 0, (0.97, 0.96, 0.92), (0.99, 0.82, 0.30)),
    'crt': ((0.03, 0.07, 0.06), 3, (0.55, 1.00, 0.70), (0.85, 1.00, 0.90)),
    'yellow': ((0.86, 0.70, 0.22), 0, (0.06, 0.05, 0.05), (0.70, 0.13, 0.10)),
    'navy': ((0.075, 0.13, 0.19), 3, (0.93, 0.50, 0.64), (0.92, 0.76, 0.28)),
}

_loaded = {'key': None}


def setup(comp):
    """Take the words and models from the Text DAT 'words' and the parts file's facts from its .json
    (the pack's copy when it has one). Runs when the DAT is new or its text has changed."""
    wd = json.loads(comp.op('words').text)
    MODELS[:] = [(m[0], tuple(m[1]), int(m[2]), m[3], m[4]) for m in wd['MODELS']]
    PLAIN[:] = [m[5] for m in wd['MODELS']]
    MI.clear()
    MI.update({m[0]: i for i, m in enumerate(MODELS)})
    PHRASES[:] = wd['PHRASES']
    CAP_INSIDE[:] = wd['CAP_INSIDE']
    STAMPS[:] = wd['STAMPS']
    for mine, theirs in ((POOLS, wd['POOLS']), (INPUT_POOLS, wd['INPUT_POOLS']), (TITLE, wd['TITLE']),
                         (LAB, wd['LABELS']), (PL, wd['PARTS_LABELS']), (PT, wd['PARTS'])):
        mine.clear()
        mine.update(theirs)
    for take, words in wd['PARTS_WORDS'].items():
        WORDS[take].update(words)
    PARTS[0] = PT['name']
    info = json.load(open(comp.op('local/modules/paths').module.scene_file(PT['info']), encoding='utf-8'))
    bed = PT.get('bed', {})       # a flat bed of parts (a keyboard) gives its heights here, not per part
    if 'centroids3' in info:
        KEYC[:] = [tuple(c) for c in info['centroids3']]
    else:
        KEYC[:] = [(c[0], bed.get('top', 0.0), c[1]) for c in info['centroids']]
    size = info.get('size') or info['base_size']
    upright = 'y_lo' in info
    PINFO.update(count=len(KEYC), ylo=info.get('y_lo', bed.get('y', 0.0)), yspan=info.get('y_span', 0.0),
                 sx=size[0], s2=size[1] if upright else size[2], plane=1.0 if upright else 0.0)
    _standin['id'] = None
    _cache['S'] = None


_cache = {'frame': -1, 'S': None}
_standin = {'id': None}
_st = {'E': 0.5, 'target': 0.5, 't': -1.0, 'hits': None, 'stamp_t': -9.0, 'mids': None, 'stamp_i': 0}


def use_standins(tab):
    """With no model library every part but the parts object is TouchDesigner's teapot (build.py fits it
    to one unit and lists its size in the table 'model_info'). Take the sizes from there and call the
    part what it is, so the drawing's labels and the Describe words stay true. see: NOTES.md "Assets" """
    _standin['id'] = tab.id
    for r in range(1, tab.numRows):
        i = int(tab[r, 'index'])
        size = tuple(float(tab[r, k]) for k in ('sx', 'sy', 'sz'))
        MODELS[i] = (MODELS[i][0], size, int(tab[r, 'tris']), 'TEAPOT, UTAH', MODELS[i][4])
        PLAIN[i] = 'TEAPOT'


def input_path(comp):
    """The TOP named by the scene's Input parameter, or '' when it is blank, missing, not a TOP, or
    inside this scene (reading our own output would be a cook loop)."""
    par = getattr(comp.par, 'Input', None)
    name = par.eval().strip() if par is not None else ''
    if not name:
        return ''
    o = op(name)
    if o is None or not o.isTOP or o.path.startswith(comp.path + '/'):
        return ''
    return o.path


def hash1(n):
    return math.modf(math.sin(n * 12.9898 + 4.1) * 43758.5453)[0] % 1.0


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rot(p, e):
    """Same as rotM in part_vertex.glsl: roll (z), then yaw (y), then pitch (x)."""
    x, y, z = p
    c, s = math.cos(e[2]), math.sin(e[2])
    x, y = c * x - s * y, s * x + c * y
    c, s = math.cos(e[1]), math.sin(e[1])
    x, z = c * x + s * z, -s * x + c * z
    c, s = math.cos(e[0]), math.sin(e[0])
    y, z = c * y - s * z, s * y + c * z
    return (x, y, z)


_zoom = [1.0]          # set once per frame from the energy: loud passages push every view in a little


def view(pitch, yaw, roll, scale, ox, oy, E, cur):
    return {'e': (pitch, yaw, roll), 's': scale * _zoom[0], 'o': (ox, oy), 'E': E, 'cur': cur}


def proj(v, p):
    """Object-space point to pixels (ortho camera)."""
    w = rot((p[0] * v['s'], p[1] * v['s'], p[2] * v['s']), v['e'])
    return (W / 2 + (w[0] + v['o'][0]) * PPU, H / 2 + (w[1] + v['o'][1]) * PPU)


def tw(text, size, f=0.43):
    """Estimated width in pixels: f is about 0.43 for Barlow Condensed, 0.62 for Chicago."""
    return len(text) * size * f


class Sheet:
    """Collects annotation geometry and lettering for one frame."""

    def __init__(self):
        self.lines = []
        self.labels = []

    def seg(self, a, b, kind=1, ink=0, w=0.8):
        if len(self.lines) < MAXL:
            self.lines.append((a[0], a[1], b[0], b[1], kind, ink, w, 0))

    def circle(self, c, r, ink=0, w=0.8):
        self.seg(c, (r, 0), 6, ink, w)

    def text(self, x, y, s, cls='s', align=0.0, size=17):
        """align 0 left, 0.5 centre, 1 right (estimated from the string length)."""
        self.labels.append((x - align * tw(s, size), y, s, cls))

    def dim(self, a, b, off, text, ink=1, away=None):
        """Dimension line parallel to a-b, offset 'off' pixels to its left, with extension lines."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        if away is not None:
            mx, my = (a[0] + b[0]) / 2 - away[0], (a[1] + b[1]) / 2 - away[1]
            off = abs(off) if (mx * nx + my * ny) >= 0 else -abs(off)
        a2 = (a[0] + nx * off, a[1] + ny * off)
        b2 = (b[0] + nx * off, b[1] + ny * off)
        sg = 1 if off > 0 else -1
        self.seg((a[0] + nx * 6 * sg, a[1] + ny * 6 * sg), (a2[0] + nx * 7 * sg, a2[1] + ny * 7 * sg), 1, ink, 0.6)
        self.seg((b[0] + nx * 6 * sg, b[1] + ny * 6 * sg), (b2[0] + nx * 7 * sg, b2[1] + ny * 7 * sg), 1, ink, 0.6)
        self.seg(a2, b2, 2, ink, 0.7)
        mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
        self.text(mx + nx * 12 * sg - (0 if abs(nx) > 0.6 else tw(text, 17) / 2) + (6 if nx * sg > 0.6 else 0)
                  - (tw(text, 17) + 6 if nx * sg < -0.6 else 0),
                  my + ny * 12 * sg - 6 + (2 if ny * sg > 0.6 else 0) - (10 if ny * sg < -0.6 else 0),
                  text, 'a' if ink else 's')

    def stamp(self, c, x, y, size):
        """A rubber stamp that lands on the snare and lifts again (needs the take's huge=size)."""
        if c['stamp_age'] > 0.30:
            return
        pool = STAMPS_D if c['D'] else STAMPS
        s = pool[(c['stamp_i'] + int(c['seed'] * 17)) % len(pool)]
        jx = (hash1(c['stamp_i'] * 3.1) - 0.5) * 70
        jy = (hash1(c['stamp_i'] * 7.7) - 0.5) * 44
        w = tw(s, size, 0.66)
        jx = min(jx, W - 40 - w - x)
        self.text(x + jx, y + jy, s, 'x')
        self.box(x + jx - 14, y + jy - 12, x + jx + w + 14, y + jy + size * 0.95, 1, 2.2)

    def box(self, x0, y0, x1, y1, ink=0, w=0.8):
        self.seg((x0, y0), (x1, y1), 5, ink, w)

    def title_block(self, x, y, c, w=388):
        """Lower-left corner (x, y). The fields tick with the feed."""
        F, m = c['F'], MODELS[c['model']]
        h = 96
        self.box(x, y, x + w, y + h, 0, 1.4)
        self.seg((x, y + 64), (x + w, y + 64))
        self.seg((x, y + 32), (x + w, y + 32))
        self.seg((x + w * 0.52, y), (x + w * 0.52, y + 64))
        self.seg((x + w * 0.78, y), (x + w * 0.78, y + 32))
        if c['D']:
            T = TITLE_D
            self.text(x + 9, y + 73, T[0], 's')
            self.text(x + 9, y + 41, T[1] % PLAIN[c['model']], 's')
            self.text(x + w * 0.52 + 9, y + 41, T[2] % m[2], 's')
            self.text(x + 9, y + 9, T[3] % (int(F['section']) % 43 + 1), 's')
            self.text(x + w * 0.52 + 9, y + 9, T[4] % (int(F['bar_i']) % 1000), 'a')
            self.text(x + w * 0.78 + 9, y + 9, T[5] % (int(F['beat_i']) % 4 + 1), 's')
            return
        self.text(x + 9, y + 73, TITLE['org'], 's')
        self.text(x + 9, y + 41, m[3], 's')
        self.text(x + w * 0.52 + 9, y + 41, LAB['dwg'] + m[4], 's')
        self.text(x + 9, y + 9, TITLE['sheet'] % (int(F['section']) % 43 + 1), 's')
        self.text(x + w * 0.52 + 9, y + 9, LAB['rev'] % (int(F['bar_i']) % 1000), 'a')
        self.text(x + w * 0.78 + 9, y + 9, LAB['beat'] % (int(F['beat_i']) % 4 + 1), 's')

    def border(self, margin=18, zones=True):
        self.box(margin, margin, W - margin, H - margin, 0, 1.2)
        if zones:
            for i in range(1, 8):
                x = margin + (W - 2 * margin) * i / 8.0
                self.seg((x, H - margin), (x, H - margin - 9), 1, 0, 0.6)
                self.seg((x, margin), (x, margin + 9), 1, 0, 0.6)


# ---------------------------------------------------------------- takes
# Each take is a function(c, sh) -> (views, settings). c: the frame's context.

def _slab_setup(c, n_want, nviews, axis='long'):
    size, tris = MODELS[c['model']][1], MODELS[c['model']][2]
    if axis == 'long':
        ax = max(range(3), key=lambda i: size[i])
    else:
        ax = axis
    n = max(2, min(n_want, int(TRI_BUDGET / (tris * nviews))))
    return ax, n, size


def take_iso_keys(c, sh):
    """Blueprint: the parts object in isometric, exploding on the bar line and set back down part by part."""
    F, seed, t = c['F'], c['seed'], PT['iso']
    side = 1 if seed < 0.5 else -1
    yaw = side * (t['yaw'] + t['yaw_sway'] * math.sin(F['evolve'] * 0.35 + seed * 6))
    pitch = t['pitch'] + t['pitch_sway'] * math.sin(F['evolve'] * 0.23)
    cur = c['cur1']
    v = view(pitch, yaw, 0, t['scale'], t['ox'] * side, t['oy'], 0.55 + 0.45 * c['E'], cur)
    sh.border()
    sh.title_block(W - 18 - 388 if side > 0 else 18, 18, c)
    # width of the object, measured live along its own x axis
    spread = 1.0 + v['E'] * t['spread'] * (1 - smooth(0.0, 0.9, cur))
    hx, dy, dz = t['dim']
    a = proj(v, (-hx * spread, dy, dz))
    b = proj(v, (hx * spread, dy, dz))
    wd = c['words']
    sh.dim(a, b, -34, wd['dim'] % spread if wd else '%.1f' % (t['mm'] * spread))
    # leader to the part that is landing
    k = min(NKEYS - 1, int(cur * NKEYS))
    pk = proj(v, KEYC[k])
    lx = 170 if side < 0 else W - 330
    ly = H - 120
    sh.seg(pk, (lx, ly), 4, 1, 0.7)
    sh.seg((lx, ly), (lx + 150 * side, ly), 1, 1, 0.7)
    phrase = wd['typed'][c['phrase'] % len(wd['typed'])] if wd else PHRASES[c['phrase']]
    sh.text(lx + (6 if side > 0 else -144), ly + 7,
            wd['leader'] % (k + 1, NKEYS) if wd else PL['leader'] % (k + 1) + repr(phrase[k % len(phrase)]), 'a')
    typed = phrase[:int(min(1.0, cur) * len(phrase) + 0.5)]
    sh.text(40 if side > 0 else W - 40 - tw(phrase, 30, 0.62), H - 64, typed + '_', 'l')
    sh.stamp(c, 60 if side > 0 else W - 430, 50, 46)
    return [v], dict(pal='blueprint', mode=0, model=PARTS[0], chaos=t['chaos'], spread=t['spread'], lift=t['lift'],
                     rowlift=t['rowlift'], ow=1.5, cw=0.8, big=30, bigfont=0, huge=46, glow=0.3, inp='sheet')


def take_three_view(c, sh):
    """Cream drafting film: front, plan and side elevations of a sliced part, plus an exploded isometric."""
    F, seed = c['F'], c['seed']
    ax, n, size = _slab_setup(c, 6, 4)
    E = c['E']
    s = 0.70 / max(size)
    s_iso = min(1.5 * s, 0.74 / (size[ax] / 2 + (n - 1) / 2.0 * c['gap']))
    views = [
        view(0, 0, 0, s, -1.25, 0.45, 0.0, 0),                      # front
        view(math.pi / 2, 0, 0, s, -1.25, -0.45, 0.0, 0),            # plan
        view(0, -math.pi / 2, 0, s, -0.42, 0.45, 0.0, 0),            # side
        view(0.52, 0.72 + 0.35 * math.sin(F['evolve'] * 0.3 + seed * 6), 0, s_iso, 0.90, 0.16, E, 0),
    ]
    sh.border()
    sh.seg((W * 0.5, 18), (W * 0.5, H - 18), 3, 0, 0.6)
    sh.seg((18, H * 0.5), (W * 0.5, H * 0.5), 3, 0, 0.6)
    wd = c['words']
    for i, (vx, vy) in enumerate(((0, 1), (0, 0), (1, 1))):
        sh.text(30 + vx * 316, H * 0.5 + 10 if vy else 28, wd['views'][i] if wd else LAB['views'][i], 's')
    f = views[0]
    a, b = proj(f, (-size[0] / 2, -size[1] / 2, 0)), proj(f, (size[0] / 2, -size[1] / 2, 0))
    sh.dim(a, b, -20, wd['dims'][0] % min(2, F['bass']) if wd else '%.1f' % (size[0] * 300 * (1 + 0.04 * min(2, F['bass']))))
    sd = views[2]
    a, b = proj(sd, (0, -size[1] / 2, size[2] / 2)), proj(sd, (0, size[1] / 2, size[2] / 2))
    sh.dim(a, b, -18, wd['dims'][1] % size[1] if wd else '%.1f' % (size[1] * 300))
    iso = views[3]
    axv = [0, 0, 0]
    half = size[ax] / 2 + (n - 1) / 2.0 * c['gap'] * E
    axv[ax] = half
    a, b = proj(iso, tuple(-q for q in axv)), proj(iso, tuple(axv))
    sh.dim(a, b, 150 if ax != 1 else 200, wd['dims'][2] % E if wd else '%.1f' % (2 * half * 300),
           away=(W * 0.5 + 0.90 * PPU, H * 0.5 + 0.16 * PPU))
    sh.text(W * 0.5 + 16, H - 44, wd['head'] % n if wd else LAB['iso'] % n, 's')
    if wd:
        sh.text(W * 0.5 + 16, H - 66, wd['note'], 's')
    sh.title_block(W - 18 - 388, 18, c)
    sh.stamp(c, 330, 70, 40)
    return views, dict(pal='cream', mode=1, axis=ax, slabs=n, ow=1.3, cw=0.7, hatch=6, cutfill=0.16, huge=40)


def take_macro_keys(c, sh):
    """Black, one ink, no lettering: a perspective camera inside the cloud of parts."""
    F, seed, t = c['F'], c['seed'], PT['macro']
    yaw = F['evolve'] * 0.45 + seed * 6.28
    pitch = t['pitch'] + t['pitch_sway'] * math.sin(F['evolve'] * 0.31 + seed * 3)
    roll = 0.5 * math.sin(F['evolve'] * 0.2 + seed * 9)
    v = view(pitch, yaw, roll, t['scale'], t['drift'][0] * math.sin(F['evolve'] * 0.17 + seed * 20),
             t['drift'][1] * math.cos(F['evolve'] * 0.13), 0.6 + 0.6 * c['E'], c['cur1'])
    for (x, y) in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
        sh.seg((x - 12, y), (x + 12, y), 1, 0, 0.7)
        sh.seg((x, y - 12), (x, y + 12), 1, 0, 0.7)
    wd = c['words']
    if wd:
        # the only lettering this take ever has: two lines in a cleared strip (knock) over the field of parts
        sh.text(64, 62, wd['lines'][0] % NKEYS, 'l')
        sh.text(64, 30, wd['lines'][1], 'l')
    return [v], dict(pal='black', mode=0, model=PARTS[0], chaos=t['chaos'], spread=t['spread'], lift=t['lift'],
                     rowlift=0.0, casesink=t['casesink'], ow=2.2, cw=1.1, persp=1, camz=t['camz'], fov=t['fov'],
                     vig=0.9, dthr=0.03, glow=0.9, big=26, bigfont=2, knock=1 if wd else 0, inp='sheet', sheet=0.6)


def take_parts_sheet(c, sh):
    """Dot-grid green paper: twelve small views of one part, a turntable of exploded states."""
    F, seed = c['F'], c['seed']
    ax, n, size = _slab_setup(c, 4, 12)
    # fitted to its cell with the slabs fully apart, so a tall part cannot run into the row below
    s = min(0.40 / max(size), 0.50 / (size[ax] + (n - 1) * 0.26))
    beat = int(F['beat_i'])
    views = []
    for i in range(12):
        col, row = i % 4, i // 4
        ox = (col - 1.5) * 0.86
        oy = (1 - row) * 0.62 + 0.03
        yaw = i * math.pi / 6 + F['evolve'] * 0.5 + seed * 6.28
        open_ = ((i + beat) % 3 != 0)
        views.append(view(0.48, yaw, 0, s, ox, oy, (0.25 + 0.75 * c['E']) * (1.0 if open_ else 0.0), 0))
        px, py = W / 2 + ox * PPU, H / 2 + oy * PPU
        sh.circle((px - 118, py + 84), 13, 0, 0.8)
        sh.text(px - 118, py + 78, '%02d' % (i + 1), 's', 0.5)
        if i < 11:
            sh.text(px - 96, py + 78, LAB['deg'] % (int(math.degrees(yaw)) % 360), 'a' if open_ else 's')
    for i in range(1, 4):
        sh.seg((W / 2 + (i - 2) * 0.86 * PPU, 30), (W / 2 + (i - 2) * 0.86 * PPU, H - 30), 3, 0, 0.5)
    for j in (0, 1):
        y = H / 2 + (0.5 - j) * 0.62 * PPU + 0.03 * PPU
        sh.seg((30, y), (W - 30, y), 3, 0, 0.5)
    m = MODELS[c['model']]
    wd = c['words']
    sh.text(W / 2 + 0.86 * 1.5 * PPU - 96, H / 2 - 0.62 * PPU + 0.03 * PPU + 78, wd['cell'] if wd else m[4], 'a')
    if wd:
        sh.text(W / 2, 12, wd['foot'], 's', 0.5)
    return views, dict(pal='green', mode=1, axis=ax, slabs=n, ow=1.1, cw=0.6, hatch=4, cutfill=0.25, shade=1.0,
                       gap=0.26, inp='sheet', sheet=0.55)


def take_section_sweep(c, sh):
    """Deep red: one huge part with its near end cut away; every kick snaps the cutting plane
    to a new depth, so the hatched cross-section changes shape with the drums."""
    F, seed = c['F'], c['seed']
    ax, n, size = _slab_setup(c, 2, 1)
    cut = 0.22 + 0.62 * c['E'] + 0.04 * math.sin(F['beat_pos'] * math.pi)
    cut = max(0.08, min(0.95, cut))
    side = 1 if seed < 0.5 else -1
    sway = 0.10 * math.sin(F['evolve'] * 0.4)
    # the model's +axis must point towards the camera, or the cut face is hidden
    if ax == 0:
        e = (0.34, (-0.95 if side > 0 else -(math.pi - 0.95)) + sway, 0)
    elif ax == 2:
        e = (0.34, 0.7 * side + sway, 0)
    else:
        e = (0.95, 0.6 * side + sway, 0)
    # fitted to the cross-section, not the length: the part's long axis points at the viewer
    s = min(2.6 / max(size), 1.25 / max(size[(ax + 1) % 3], size[(ax + 2) % 3]))
    v = view(e[0], e[1], e[2], s, 0.28 * side, -0.02, 0.0, cut)
    wd = c['words']
    big = wd['big'] if wd else LAB['section']
    sh.text(44 if side > 0 else W - 44 - tw(big, 64, 0.66), 44, big, 'x')
    mm = size[ax] * 300 * cut
    sub = wd['sub'] % int(cut * 100) if wd else LAB['cut_at'] % (mm, MODELS[c['model']][4])
    sh.text(48 if side > 0 else W - (48 + tw(sub, 17) if wd else 300), 124, sub, 's')
    # leader from the middle of the cut face
    axv = [0, 0, 0]
    axv[ax] = (cut - 0.5) * size[ax]
    pc = proj(v, tuple(axv))
    lx = 250 if side > 0 else W - 250
    sh.seg(pc, (lx, H - 90), 4, 1, 1.0)
    sh.seg((lx, H - 90), (lx - 150 * side, H - 90), 1, 1, 1.0)
    sh.text(lx - (146 if side > 0 else -6), H - 82, wd['leader'] if wd else LAB['cut_face'] % int(cut * 100), 's')
    cm = max(size[(ax + 1) % 3], size[(ax + 2) % 3])
    return [v], dict(pal='red', mode=2, axis=ax, slabs=1, ow=2.0, cw=0.9, hatch=17, cutfill=0.22,
                     big=30, huge=64, bigfont=0, vig=0.5, fill=0.13,
                     picfit=(max(1.3 * cm, 0.75 * max(size)), max(0.8 * cm, 0.47 * max(size))))


def take_plan_typed(c, sh):
    """Pink ruled slip: the parts object square on, filling the frame, set back together two bars at a time."""
    F, seed, t = c['F'], c['seed'], PT['plan']
    cur = c['cur2']
    flip = math.pi if seed > 0.66 else 0.0
    v = view(t['pitch'], flip + 0.05 * math.sin(F['evolve'] * 0.5), 0, t['scale'], 0.0, t['oy'], 0.6 + 0.4 * c['E'], cur)
    wd = c['words']
    phrase = wd['typed'][c['phrase'] % len(wd['typed'])] if wd else PHRASES[c['phrase']]
    typed = phrase[:int(min(1.0, cur) * len(phrase) + 0.5)]
    sh.text(40, 40, typed + ('_' if int(F['beat_pos'] * 2) % 2 else ' '), 'l')
    sh.text(W - 40, 122, (wd['count'] if wd else PL['count']) % int(F.get('onsets', 0)), 'a', 1.0)
    sh.text(40, 122, wd['head'] % NKEYS if wd else PL['head'], 's')
    sh.seg((40, 112), (W - 40, 112), 1, 0, 1.0)
    return [v], dict(pal='pink', mode=0, model=PARTS[0], chaos=t['chaos'], spread=t['spread'], lift=t['lift'],
                     rowlift=0.0, ow=1.4, cw=0.8, big=52, bigfont=0, vig=0.2)


def _lay(ax, tilt=0.5):
    """Euler angles that lay the model's axis along the screen's x, seen a little from the front and above."""
    return {0: (0.36, tilt, 0.0), 2: (0.36, tilt + math.pi / 2, 0.0), 1: (0.36, tilt, -math.pi / 2)}[ax]


def take_slab_strip(c, sh):
    """Carpet grey: one part cut into many thin slabs laid out across the whole frame like a contact strip."""
    F, seed = c['F'], c['seed']
    ax, n, size = _slab_setup(c, 14, 1)
    s = 0.58 / max(size[(ax + 1) % 3], size[(ax + 2) % 3], 0.5)
    E = 0.55 + 0.45 * c['E']
    span = 3.1
    gap = (span / s - size[ax]) / max(1, n - 1)
    e = _lay(ax, 0.62 if seed < 0.5 else -0.62)
    v = view(e[0], e[1], e[2], s, 0.0, 0.06 + 0.04 * math.sin(F['evolve'] * 0.6), E, 0)
    step = size[ax] / n
    beat = int(F['beat_i'])
    ends = []
    for k in range(n):
        p = [0, 0, 0]
        p[ax] = -size[ax] / 2 + (k + 0.5) * step + (k - (n - 1) / 2.0) * gap * E
        q = proj(v, tuple(p))
        ends.append(q)
        hot = (k == beat % n)
        sh.text(q[0], q[1] - 178, '%02d' % (k + 1), 'a' if hot else 's', 0.5)
        sh.seg((q[0], q[1] - 156), (q[0], q[1] - 140 + (26 if hot else 0)), 1, 1 if hot else 0, 0.7)
    wd = c['words']
    sh.dim((ends[0][0], ends[0][1] + 150), (ends[-1][0], ends[-1][1] + 150), 26,
           wd['dim'] % E if wd else
           '%.1f' % (math.hypot(ends[-1][0] - ends[0][0], ends[-1][1] - ends[0][1]) / PPU / s * 300))
    sh.stamp(c, W - 420, H - 110, 40)
    sh.text(40, 34, wd['head'] % (PLAIN[c['model']], n) if wd else
            LAB['strip'] % (MODELS[c['model']][3], MODELS[c['model']][4], n, step * 300), 's')
    sh.text(W - 40, 34, (wd['bar'] if wd else LAB['bar']) % (int(F['bar_i']) % 1000), 'a', 1.0)
    return [v], dict(pal='grey', mode=1, axis=ax, slabs=n, gap=gap, ow=1.3, cw=0.7, hatch=5, cutfill=0.22, vig=0.35, huge=40,
                     inp='sheet')


def take_bill_of_materials(c, sh):
    """Phosphor on black: a tall exploded stack at one side, the parts list as the picture."""
    F, seed = c['F'], c['seed']
    ax, n, size = _slab_setup(c, 7, 1, axis=1)
    side = 1 if seed < 0.5 else -1
    s = 0.46 / max(size[0], size[2])
    E = 0.3 + 0.7 * c['E']
    gap = (1.65 / s - size[1]) / max(1, n - 1)
    v = view(0.42, F['evolve'] * 0.7 + seed * 6.28, 0, s, 1.12 * side, 0.0, E, 0)
    x0 = 60 if side > 0 else W - 60 - 700
    beat = int(F['beat_i'])
    wd = c['words']
    sh.text(x0, H - 150, '%06.1f' % (min(2.0, F['bass']) * 100.0 if wd
                                     else min(2.0, F['bass']) * 417.3 + int(F['bar_i']) % 100), 'x')
    sh.text(x0 + 4, H - 176, wd['label'] if wd else LAB['bass'], 's')
    rows = 8
    first = (int(F['section']) * 3) % len(MODELS)
    for r in range(rows):
        m = MODELS[(first + r) % len(MODELS)]
        y = H - 230 - r * 46
        hot = (r == beat % rows)
        line = LAB['list_row'] % (m[4], m[3], (int(hash1(r + first) * 40) + int(F['bar_i'])) % 47 + 1)
        if wd:
            line = wd['rows'][r] % (gap * E) if '%' in wd['rows'][r] else wd['rows'][r]
        sh.text(x0 + 30, y, line, 'l')
        if hot:
            sh.text(x0, y, '>', 'l')
            sh.seg((x0 + 30, y - 8), (x0 + 690, y - 8), 1, 1, 1.2)
    # leaders from the stack to the list edge, one per slab
    for k in range(n):
        p = [0, 0, 0]
        p[1] = -size[1] / 2 + (k + 0.5) * size[1] / n + (k - (n - 1) / 2.0) * gap * E
        q = proj(v, tuple(p))
        lx = q[0] - side * 150
        sh.seg(q, (lx, q[1]), 4, 0, 0.7)
        sh.text(lx - side * 8, q[1] - 6, (wd['leader'] if wd else LAB['slab']) % (k + 1), 's', 1.0 if side > 0 else 0.0)
    return [v], dict(pal='crt', mode=1, axis=1, slabs=n, gap=gap, ow=1.2, cw=0.6, hatch=5, cutfill=0.12,
                     big=27, huge=132, bigfont=0, vig=0.6, glow=0.8, inp='sheet', sheet=0.38)


def take_contour_scan(c, sh):
    """Yellow, black ink: no outline drawing at all. One huge cropped part drawn only as the rings where
    cutting planes meet its surface, like a CT stack; the kick snaps the ring count, a red scan band
    sweeps the part once a bar."""
    F, seed = c['F'], c['seed']
    size = MODELS[c['model']][1]
    ax = 1 if seed > 0.5 else max(range(3), key=lambda i: size[i])
    side = 1 if (seed * 4) % 1.0 < 0.5 else -1
    s = 2.5 / max(size)
    yaw = side * 0.7 + 0.5 * math.sin(F['evolve'] * 0.3 + seed * 9)
    pitch = 0.42 + 0.2 * math.sin(F['evolve'] * 0.21 + seed * 4)
    v = view(pitch, yaw, 0.12 * side, s, 0.42 * side, -0.05, 0.0, 0)
    rings = int(18 + 60 * c['E'])
    scan = F['bar'] % 1.0
    x0 = 40 if side > 0 else W - 40
    # a ruler down the empty side; the scan position is the long tick
    for i in range(13):
        y = 60 + i * 50
        sh.seg((x0, y), (x0 + side * (22 if i % 4 == 0 else 11), y), 1, 0, 1.0)
    ys = 60 + scan * 600
    sh.seg((x0, ys), (x0 + side * 120, ys), 1, 1, 2.0)
    wd = c['words']
    sh.text(x0 + side * 12 - (0 if side > 0 else tw(LAB['plane'] % 0, 17)), ys + 8,
            (wd['scan'] if wd else LAB['plane']) % int(scan * rings), 'a')
    sh.text(x0 + (34 if side > 0 else -34 - tw('00', 150, 0.7)), 44, '%02d' % rings, 'x')
    lab = wd['label'] if wd else LAB['planes'] % MODELS[c['model']][4]
    sh.text(x0 + (36 if side > 0 else -36 - tw(lab, 17)), 24, lab, 's')
    if wd:
        for i, ln in enumerate(wd['lines']):
            # clear of the scan tick and its PLANE label, which travel the whole ruler
            sh.text(x0 + (136 if side > 0 else -136 - tw(ln, 22, 0.70)), H - 78 - i * 30, ln, 'l')
    return [v], dict(pal='yellow', mode=1, axis=ax, slabs=1, ow=0.9, cw=0.0, contours=rings, scan=scan,
                     huge=150, bigfont=1, vig=0.35, fill=0.0, big=22, knock=1 if wd else 0)


def take_rosette(c, sh):
    """Ink navy, solid pink parts with navy lines: twelve copies of one sliced part on a wheel, cropped by
    the frame. The wheel clicks round one station per beat and its spokes burst outward with the kick."""
    F, seed = c['F'], c['seed']
    size = MODELS[c['model']][1]
    ax = 0 if size[0] >= size[2] else 2
    n = max(2, min(3, int(TRI_BUDGET / (MODELS[c['model']][2] * 12))))
    side = 1 if seed < 0.5 else -1
    E = c['E']
    gap = 0.20
    # radial length about 0.6 units, and narrow enough that twelve fit round the closed wheel
    s = min(0.60 / (size[ax] + (n - 1) * gap * 0.5), 0.31 / size[2 - ax])
    cx, cy = 0.50 * side, -0.04
    rad = 0.70 + 0.40 * E
    turn = (int(F['beat_i']) + smooth(0.0, 0.3, F['beat'] % 1.0)) * (math.pi / 6) * side + seed * 6.28
    views = []
    beat = int(F['beat_i'])
    pc = (W / 2 + cx * PPU, H / 2 + cy * PPU)
    for i in range(12):
        phi = turn + i * math.pi / 6
        ox, oy = cx + rad * math.cos(phi), cy + rad * math.sin(phi)
        views.append(view(1.18, phi + (math.pi / 2 if ax == 2 else 0.0), 0, s, ox, oy, 0.15 + 0.85 * E, 0))
    sh.circle(pc, rad * PPU, 1, 0.7)
    sh.circle(pc, 26, 0, 1.4)
    sh.seg((pc[0] - 44, pc[1]), (pc[0] + 44, pc[1]), 1, 0, 0.7)
    sh.seg((pc[0], pc[1] - 44), (pc[0], pc[1] + 44), 1, 0, 0.7)
    # the station under the fixed pointer is the one being counted
    a0 = math.pi if side > 0 else 0.0
    p0 = (pc[0] + math.cos(a0) * (rad + 0.34) * PPU, pc[1] + math.sin(a0) * (rad + 0.34) * PPU)
    tx = 60 if side > 0 else W - 60
    sh.seg(p0, (tx + side * 150, p0[1]), 4, 1, 0.9)
    wd = c['words']
    if wd:
        L = wd['lines']
        for i, ln in enumerate((L[0] % (beat % 12 + 1), L[1], L[2], L[3] % PLAIN[c['model']])):
            sh.text(tx - (0 if side > 0 else tw(ln, 17)), p0[1] + 8 if i == 0 else p0[1] - i * 22, ln, 'a' if i == 0 else 's')
    else:
        sh.text(tx - (0 if side > 0 else tw(LAB['station'] % 0, 17)), p0[1] + 8, LAB['station'] % (beat % 12 + 1), 'a')
        sh.text(tx - (0 if side > 0 else tw(MODELS[c['model']][3], 17)), p0[1] - 22, MODELS[c['model']][3], 's')
    return views, dict(pal='navy', mode=1, axis=ax, slabs=n, gap=gap, ow=1.5, cw=0.8, hatch=4, cutfill=0.55,
                       fill=1.0, vig=0.5, glow=0.22, inp='sheet', sheet=0.55)


TAKES = [take_iso_keys, take_three_view, take_macro_keys, take_contour_scan, take_parts_sheet,
         take_section_sweep, take_rosette, take_plan_typed, take_slab_strip, take_bill_of_materials]
LEVELS = (0.3, 0.85, 0.5, 1.0, 0.2, 0.9, 0.6, 0.1)

SETTINGS = dict(pal='cream', mode=1, model=None, axis=1, slabs=1, fan=0.0, gap=None,
                 chaos=0.0, spread=0.0, lift=0.0, rowlift=0.0, casesink=0.22, ow=1.4, cw=0.8, hatch=6.0, cutfill=0.15,
                 shade=0.0, vig=0.25, dthr=0.012, persp=0, camz=10.0, fov=40.0, big=30, bigfont=0, huge=120, glow=0.0,
                 contours=0, fill=0.0, scan=0.0, knock=0, picfit=None, inp='parts', sheet=0.7)


def frame(comp):
    global NKEYS
    wdat = comp.op('words')
    key = (wdat.id, wdat.text)
    if _loaded['key'] != key:
        setup(comp)
        NKEYS = len(KEYC)
        _loaded['key'] = key
    tab = comp.op('model_info')
    if tab is not None and _standin['id'] != tab.id:
        use_standins(tab)
    shot = comp.op('shot')
    take, seed, age = int(shot['take']), float(shot['seed']), float(shot['age'])
    describe = bool(comp.par.Describe.eval()) if hasattr(comp.par, 'Describe') else False
    has_input = bool(input_path(comp))
    f = (absTime.frame, take, seed, describe, has_input)
    if _cache['frame'] == f and _cache['S'] is not None:
        return _cache['S']
    hub = comp.op('hub')
    F = {ch.name: float(ch[0]) for ch in hub.chans()}
    for k in ('energy', 'bass', 'evolve', 'beat_pos', 'bar_pos', 'section', 'bar_i', 'beat_i', 'hits_low',
              'hits_mid', 'hit_low', 'hit_mid', 'hit_high', 'pulse', 'bar', 'beat', 'pitch', 'bass_pitch', 't'):
        v = F.get(k, 0.0)
        F[k] = v if v == v else 0.0
    fn = TAKES[take % len(TAKES)]

    # the explosion amount: every kick snaps it to a new level, with a short lag so it reads as a move
    now = absTime.seconds
    dt = now - _st['t']
    hits = int(F['hits_low'])
    if _st['hits'] != hits:
        _st['hits'] = hits
        _st['kick_t'] = now
        _st['target'] = LEVELS[(hits + int(seed * 8)) % len(LEVELS)]
    # a passage with no kick must not leave the parts frozen: after a second without one,
    # the beat count moves the level instead
    beat_n = int(F['beat_i'])
    if _st.get('beat_n') != beat_n:
        _st['beat_n'] = beat_n
        if now - _st.get('kick_t', -9.0) > 1.0:
            _st['target'] = LEVELS[(beat_n * 3 + int(seed * 8)) % len(LEVELS)]
    if dt < 0 or dt > 0.4 or age < 0.05:
        _st['E'] = _st['target'] * 0.2       # a new shot starts nearly closed and opens
    else:
        _st['E'] += (_st['target'] - _st['E']) * (1 - math.exp(-dt / 0.07))
    _st['t'] = now
    E = max(0.0, _st['E'] + 0.10 * min(1.5, F['hit_low']))

    # the stamp lands on the snare and holds
    mids = int(F['hits_mid'])
    if _st['mids'] != mids:
        _st['mids'] = mids
        _st['stamp_t'] = now
        _st['stamp_i'] += 1

    pool = (INPUT_POOLS.get(fn.__name__) if has_input else None) or POOLS.get(fn.__name__)
    sec = int(F['section'])
    # a new section is a new sheet: the part changes and the plotter draws it again
    if _st.get('sec') != sec:
        _st['sec'] = sec
        _st['sec_t'] = now
    c = {'F': F, 'seed': seed, 'age': age, 'take': take, 'E': E,
         'D': describe, 'words': WORDS[fn.__name__] if describe else None,
         'cur1': min(1.0, (F['bar'] % 1.0) / 0.80),
         'cur2': min(1.0, ((F['bar_pos'] % 2.0) / 2.0) / 0.85),
         'phrase': (sec + int(seed * 53)) % len(PHRASES),
         'stamp_age': now - _st['stamp_t'], 'stamp_i': _st['stamp_i'],
         'model': MI[pool[(sec + int(seed * 31)) % len(pool)]] if pool else 0,
         'gap': 0.0}
    size = MODELS[c['model']][1]
    c['gap'] = 0.16
    _zoom[0] = 0.93 + 0.14 * smooth(0.33, 0.65, F['energy'])
    sh = Sheet()
    views, cfg = fn(c, sh)
    s = dict(SETTINGS)
    s.update(cfg)
    if s['model'] is not None:
        c['model'] = MI[s['model']] if isinstance(s['model'], str) else s['model']
    size = MODELS[c['model']][1]
    pal = PAL[s['pal']]
    ax = int(s['axis'])
    nv = max(1, min(MAXV, len(views)))
    nslab = int(s['slabs']) if s['mode'] >= 1 else 1
    u = {
        'mode': s['mode'], 'slabs': nslab, 'axis': ax, 'nviews': nv, 'ninst': nv * nslab,
        'ext_lo': -size[ax] / 2 - 0.002, 'ext_hi': size[ax] / 2 + 0.002,
        'gap': s['gap'] if s['gap'] is not None else c['gap'], 'fan': s['fan'],
        'chaos': s['chaos'], 'spread': s['spread'], 'lift': s['lift'], 'rowlift': s['rowlift'], 'casesink': s['casesink'],
        'p_count': PINFO['count'], 'p_ylo': PINFO['ylo'], 'p_yspan': PINFO['yspan'],
        'p_sx': PINFO['sx'], 'p_s2': PINFO['s2'], 'p_plane': PINFO['plane'],
        'paper_r': pal[0][0], 'paper_g': pal[0][1], 'paper_b': pal[0][2], 'paper_style': pal[1],
        'ink_r': pal[2][0], 'ink_g': pal[2][1], 'ink_b': pal[2][2], 'ow': s['ow'],
        'acc_r': pal[3][0], 'acc_g': pal[3][1], 'acc_b': pal[3][2], 'cw': s['cw'],
        'hatch': s['hatch'], 'cutfill': s['cutfill'], 'shade': s['shade'], 'vig': s['vig'],
        'reveal': min(1.0, age / 0.4, 0.25 + (now - _st.get('sec_t', -9.0)) / 0.33), 'dthr': s['dthr'],
        'contours': s['contours'], 'fill': s['fill'], 'scan': s['scan'],
        'persp': s['persp'], 'camz': s['camz'], 'fov': s['fov'],
        # Input: 'parts' wraps the picture round the parts, 'sheet' drafts it onto the paper behind them
        'pic': 1.0 if (has_input and s['inp'] == 'parts') else 0.0,
        'sheet': s['sheet'] if (has_input and s['inp'] == 'sheet') else 0.0,
        'knock': 1 if (has_input and s['inp'] == 'sheet') else s['knock'],
        'capin': 1.0 if (MODELS[c['model']][0] in CAP_INSIDE and (s['mode'] == 2 or nslab > 1)) else 0.0,
        'picw': (s['picfit'] or (1.25 * max(size), 0.78 * max(size)))[0],
        'pich': (s['picfit'] or (1.25 * max(size), 0.78 * max(size)))[1],
        'model': c['model'], 'big': s['big'], 'huge': s['huge'], 'glow': s['glow'], 'bigfont': s['bigfont'], 'E': E, 'take': take % len(TAKES),
    }
    S = {'u': u, 'views': views[:MAXV], 'lines': sh.lines, 'labels': sh.labels}
    _cache['frame'] = f
    _cache['S'] = S
    return S


# ---------------------------------------------------------------- Script OP callbacks
def cook_ctl(scriptOp):
    S = frame(scriptOp.parent())
    scriptOp.clear()
    scriptOp.numSamples = 1
    for k, v in S['u'].items():
        scriptOp.appendChan(k)[0] = float(v)


def cook_views(scriptOp):
    S = frame(scriptOp.parent())
    scriptOp.clear()
    scriptOp.numSamples = MAXV
    chans = [scriptOp.appendChan(n) for n in ('a0', 'a1', 'a2', 'a3', 'b0', 'b1', 'b2', 'b3')]
    for i, v in enumerate(S['views']):
        vals = (v['e'][0], v['e'][1], v['e'][2], v['s'], v['o'][0], v['o'][1], v['E'], v['cur'])
        for ch, x in zip(chans, vals):
            ch[i] = float(x)


def cook_lines(scriptOp):
    S = frame(scriptOp.parent())
    scriptOp.clear()
    scriptOp.numSamples = MAXL
    chans = [scriptOp.appendChan(n) for n in ('x0', 'y0', 'x1', 'y1', 'k', 'c', 'w', 'u')]
    for i, ln in enumerate(S['lines'][:MAXL]):
        for ch, x in zip(chans, ln):
            ch[i] = float(x)


def cook_labels(scriptOp, cls):
    S = frame(scriptOp.parent())
    scriptOp.clear()
    scriptOp.appendRow(['x', 'y', 'text'])
    for (x, y, s, k) in S['labels']:
        if k == cls:
            scriptOp.appendRow([int(round(x)), int(round(y)), s])
