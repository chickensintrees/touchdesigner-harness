# Builder for /project1/sc_point_morph. Run inside TouchDesigner (see SCENE_BRIEF.md).
# Idempotent: destroys and rebuilds the whole scene.
# see: experiments/sc_point_morph/NOTES.md (2026-11-10, "Takes"; 2026-11-11, "Assets")
import td

SLUG = 'sc_point_morph'
# Where things are: no folder is named here. The repository is wherever the project file is saved,
# and every file parameter is an expression on the scene's own paths module (mod.paths).
# see: experiments/sw_hub/SCENE_BRIEF.md ("Portability", 2026-11-11)
LIB = {'op': op}  # noqa: F821  `op` is a TouchDesigner global, passed in by the caller
exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)

SIDE = 352                 # 352 x 352 = 123,904 points; drawn twice (floor reflection) = 247,808
NPTS = SIDE * SIDE
# Every shape a take can ask for is baked at build and stays loaded: a cut never loads anything.
# Slots, in atlas order. 'model0'..'model8' are filled from the MODELS rows of the scene's words,
# so an index here means the same slot whatever pack is in use.
LAYOUT = ['model0', 'word', 'model1', 'model2', 'model3', 'model4',
          'model5', 'model6', 'model7', 'model8',
          'word_made', 'word_out', 'mosaicA', 'mosaicB',
          # Describe mode: the same lettering technique, but the words say what it is (baked like the rest)
          'word_d0', 'word_d1', 'word_d2', 'word_d3',
          # Input: a flat sheet of points that wears the Input picture (picture.py)
          'word_pic']
DESCRIBE_PHRASES = {'word_d0': 'POINT CLOUD', 'word_d1': '123,904 POINTS', 'word_d2': 'ONE CLOUD\nMANY SHAPES',
                    'word_d3': 'MADE OF\nPOINTS'}
D0, D1, D2, D3, PIC = (LAYOUT.index(n) for n in ('word_d0', 'word_d1', 'word_d2', 'word_d3', 'word_pic'))
WORDS = tuple(i for i, n in enumerate(LAYOUT) if n.startswith('word'))
NMODELS = sum(1 for n in LAYOUT if n.startswith('model'))
GRID = (5, 3)              # catalogue take: columns, rows
NS = len(LAYOUT)

# Everything the scene says and shows that belongs to an asset pack. A pack may replace any of
# these names with its own scenes/sc_point_morph/words.json (LIB['scene_words'], read in build()).
#   MODELS       nine rows, one per model slot: the pack's model, the yaw (radians) at which it shows
#                its best side to a camera on +Z, how far above its middle the camera sits, a factor
#                on the camera distance, and the accent colour of its sun (linear light)
#   PHRASES      the three pieces of lettering the cloud can become
#   RED_FROM     how far across a piece of lettering its last mark turns red (1.0: never)
#   CAPTIONS     the corner line of the takes that have one, three per take, picked by seed
#   TAKE_SHAPES  what each take walks through, by model name or phrase name
# see: experiments/sc_point_morph/NOTES.md (2026-11-11, "Words and models")
DEFAULTS = {
    'MODELS': [
        {'name': 'ribbon_loop', 'front': 0.0, 'high': 0.32, 'back': 1.0, 'tint': [0.72, 0.13, 0.34]},
        {'name': 'marble_bust', 'front': 0.0, 'high': 0.32, 'back': 1.0, 'tint': [0.82, 0.60, 0.07]},
        {'name': 'gramophone', 'front': 0.5, 'high': 0.32, 'back': 1.0, 'tint': [0.40, 0.62, 0.16]},
        {'name': 'space_helmet', 'front': 0.0, 'high': 0.32, 'back': 1.15, 'tint': [0.03, 0.38, 0.62]},
        {'name': 'skeleton_key', 'front': 1.57, 'high': 0.32, 'back': 1.0, 'tint': [0.90, 0.15, 0.07]},
        {'name': 'astrolabe', 'front': 0.0, 'high': 0.32, 'back': 1.0, 'tint': [0.72, 0.13, 0.34]},
        {'name': 'amphora', 'front': 0.0, 'high': 0.32, 'back': 1.0, 'tint': [0.03, 0.38, 0.62]},
        {'name': 'hourglass', 'front': 0.0, 'high': 0.32, 'back': 1.0, 'tint': [0.86, 0.42, 0.05]},
        {'name': 'lander', 'front': 0.0, 'high': 0.32, 'back': 1.1, 'tint': [0.03, 0.38, 0.62]},
    ],
    'PHRASES': {'word': 'REAL TIME.', 'word_made': 'THIS FRAME\nIS MADE NOW.', 'word_out': 'SOUND IN.\nPICTURE OUT.'},
    'RED_FROM': 0.96,
    'CAPTIONS': {
        'catalogue': ['CATALOGUE NO. 47', 'OBJECT OF UNKNOWN USE', 'FOUND, NOT MADE.'],
        'plan': ['PLATE 07', 'PLAN 12-B', 'DO NOT TOUCH'],
        'raster': ['EVERY DOT IS LIVE.', 'LOUD IS BRIGHT.', 'NOT A RECORDING.'],
        'duel': ['PAST. PRESENT. LATER.', '', 'HANDLE WITH BOTH HANDS'],
    },
    'TAKE_SHAPES': {
        'sculpture': ['ribbon_loop', 'word', 'marble_bust', 'astrolabe', 'space_helmet', 'word_made',
                      'amphora', 'skeleton_key', 'hourglass', 'gramophone', 'word_out', 'lander'],
        'inside': ['space_helmet', 'amphora', 'lander', 'marble_bust'],
        'plan': ['gramophone', 'astrolabe', 'lander', 'space_helmet', 'ribbon_loop', 'marble_bust'],
        'streak': ['astrolabe', 'gramophone', 'ribbon_loop', 'amphora', 'lander', 'skeleton_key'],
        'raster': ['skeleton_key', 'amphora', 'space_helmet', 'gramophone', 'lander', 'astrolabe'],
        'duel': ['amphora', 'marble_bust', 'astrolabe', 'hourglass', 'space_helmet', 'lander', 'skeleton_key'],
    },
}
# Filled in by _configure() from the scene's words, before anything is built.
SHAPES, MOSAIC, PHRASES, TINTS, FRONT, HIGH, BACK, RED_FROM = [], [], {}, '', (), '', {}, 1.0


def hexlin(h):
    """'#RRGGBB' (sRGB) -> linear floats, as the shaders work in linear light."""
    return tuple(round((int(h[i:i + 2], 16) / 255.0) ** 2.2, 4) for i in (1, 3, 5))


def hexs(h):
    return tuple(round(int(h[i:i + 2], 16) / 255.0, 4) for i in (1, 3, 5))


INK, IVORY, RED, YELLOW, BLUE, GREEN, PINK = '#192B3B', '#EEE4CC', '#DC563D', '#DCB53D', '#287E9B', '#99AB54', '#B85779'

# One row per take. The cutter counts a scene's visits in its Take parameter; take % len(TAKES)
# picks the row, and Seed (0-1) varies things inside it: which shapes, which side, which palette,
# which phrase. Anything a row leaves out comes from TAKE_DEFAULTS; a take's shapes and captions
# come from the scene's words (TAKE_SHAPES, CAPTIONS) unless the row gives them.
#   shapes   indices into LAYOUT this take may show (section + seed walks through them)
#   layout   0 one object, 1 catalogue grid, 2 duel (two objects side by side)
#   cmode    0 lit texture, 2 raster of discs, 3 two inks, 4 contour lines
#   cam      0 orbit camera, 1 straight down, 2 inside the model
#   mdur     fraction of a section the migration takes (the rest of it the shape holds)
#   bg       0 room with halftone sun, 1 flat paper, 2 black void, 3 drawing grid
#   papers / inks / inks2   three choices each, picked by seed
#   dshapes / dcaptions / dcapsize   Describe mode: the shape list and captions whose words explain
#            the technique (default: the take's own shapes, no caption). Mirrored in preset.json "words".
#   capplate how dark a plate sits behind a Describe caption (0 none), for busy pictures
#   dang / ddfix / dtgtx / dtgty   camera angle, distance and target offset used instead of ang / dfix /
#            tgtx / tgty in
#            Describe mode (negative / -99: no change), where the
#            take's own rake leaves the lettering unreadable (captures/d2_sheet_words.png)
#   inmode   what the take does with an Input picture: 0 ignores it, 1 the cloud becomes a sheet of
#            points wearing the picture (ishapes = the shape list then), 2 every point takes the
#            picture's colour at its place on screen, 3 the sheet lies flat under the plan camera as a
#            relief whose height is the picture's brightness
#   indmul / intgtx / intgty   camera distance factor and target offset used instead of dmul / tgtx / tgty
#            while an Input picture is on (negative / -99: no change); incell the same for cellpx
#   inwear   inmode 1: how far the objects in ishapes also wear the picture (front projection)
TAKE_DEFAULTS = dict(
    layout=0, cmode=0, wscale=1.0, nsign=1.0, keep=1.0, sizemul=1.0, minpx=1.5, maxpx=24.0, cellpx=16.0,
    gain=1.0, inst=1, burst=1.0, mdur=0.5, captop=0, spin=0.0, sway=1.0, yawseed=0.0, mono=0.0, fog=0.0,
    cam=0, dmul=1.0, dfix=0.0, hfix=-99.0, ang=0.0, swing=1.0, fov=40.0, drift=0.0, tgtx=0.0, tgty=0.0,
    bg=2, glow=1.0, vig=1.0, echo=0.8, decay=0.80, decaye=0.10, zoom=1.0,
    papers=[INK] * 3, inks=[IVORY] * 3, inks2=[RED] * 3,
    captions=[''] * 3, capsize=24, capcol=IVORY,
    dcaptions=[''] * 3, dcapsize=24, capplate=0.0, dang=-1.0, ddfix=-1.0, dtgtx=-99.0, dtgty=-99.0, inmode=0, inwear=0.0, indmul=-1.0, intgtx=-99.0, intgty=-99.0, incell=-1.0)
TAKES = [
    # 0 the first cut's picture: one sculpture on a reflecting floor in front of a halftone sun
    dict(name='sculpture', inst=2, bg=0, drift=1.0, capplate=0.5,
         dcaptions=['POINT CLOUD MORPH\n123,904 POINTS SAMPLED FROM THE SURFACE\nOF A 3D MODEL, EACH IN ITS TEXTURE COLOUR.',
                    'EVERY POINT HAS A PLACE ON TWO SHAPES.\nWHEN THE SONG CHANGES SECTION\nIT FLIES FROM ONE TO THE OTHER.',
                    'ONCE A BEAT A BRIGHT BAND CLIMBS THE CLOUD.\nKICKS PUSH THE SURFACE OUTWARD.\nVOCALS MAKE POINTS SHIMMER.'],
         inmode=1, inwear=0.55),
    # 1 fifteen small clouds on paper, a different model in every cell, the beat walks a cursor through them
    dict(name='catalogue', shapes=[12, 13], layout=1, dfix=21.5, fov=20.0, hfix=-0.3, tgty=-0.3, swing=0.5, sway=0.0,
         bg=1, glow=0.0, vig=0.25, echo=0.0, decay=0.0, decaye=0.0, zoom=0.0, burst=0.0,
         papers=[IVORY, '#C8BFA6', '#DCE4C6'], capcol=INK,
         dcaptions=['ONE CLOUD DEALT INTO 15 CELLS: POINT i GOES TO CELL i MOD 15.',
                    '15 SMALL CLOUDS OF ABOUT 8,260 POINTS EACH. NINE MODELS.',
                    'THE BEAT STEPS A HIGHLIGHT FROM CELL TO CELL.']),
    # 2 the camera stands inside a five-times model and looks out through its skin
    dict(name='inside', cam=2, wscale=5.0, nsign=-1.0, keep=0.75, maxpx=22.0,
         sizemul=0.32, fog=0.20, gain=1.7, sway=0.0, glow=0.7, vig=0.6, echo=0.9, decay=0.84, decaye=0.08,
         zoom=1.6, burst=0.5, mdur=0.3, capplate=0.72, inmode=2,
         dcaptions=['INSIDE THE CLOUD\nTHE CAMERA STANDS WITHIN A MODEL ENLARGED\nFIVE TIMES AND LOOKS OUT THROUGH ITS SKIN.',
                    'INSIDE THE CLOUD\nEVERY DISC IS ONE SURFACE POINT OF A 3D MODEL,\nSEEN FROM THE WRONG SIDE.',
                    'INSIDE THE CLOUD\nKICKS THROW THE PICTURE OUTWARD\nAS RAYS OF VIDEO FEEDBACK.']),
    # 3 plan view: straight down on the object, drawn only as climbing contour lines on a drawing grid
    dict(name='plan', cam=1, cmode=4, sway=0.0, yawseed=1.0, spin=0.35, sizemul=0.85,
         bg=3, glow=0.35, vig=0.35, echo=0.0, decay=0.0, decaye=0.0, zoom=0.0,
         papers=[INK, '#0F3A4A', '#7A1F1B'], inks=[IVORY, YELLOW, IVORY], inks2=[RED, IVORY, YELLOW],
         capcol=IVORY, capplate=0.6,
         dcaptions=['PLAN VIEW: THE CLOUD SEEN FROM STRAIGHT ABOVE.\nONLY POINTS NEAR A HEIGHT LEVEL ARE INKED,\nSO THE MODEL DRAWS ITS OWN CONTOUR MAP.',
                    'CONTOUR LINES FROM POINTS\n15 HEIGHT LEVELS PER UNIT, CLIMBING SLOWLY.\nA BRIGHT CONTOUR RISES ON EVERY BEAT.',
                    'NO MESH, NO LINES: JUST 123,904 POINTS.\nTHE ONES NEAR A HEIGHT LEVEL ARE DRAWN,\nTHE REST LEFT DARK.'],
         inmode=3, ishapes=[PIC]),
    # 4 long exposure: one point in seven, the model turning, every point leaves its orbit as a line
    dict(name='streak', keep=0.025, sizemul=0.6, minpx=2.0, gain=5.0, spin=14.0,
         sway=0.0, swing=0.0, dmul=0.72, hfix=0.8, glow=0.5, vig=0.7, echo=1.0, decay=0.988, decaye=0.006, zoom=0.0,
         burst=0.6, capplate=0.7,
         dcaptions=['LONG EXPOSURE\nONLY 1 POINT IN 40 IS DRAWN. THE MODEL SPINS\nAND THE FRAME FADES SLOWLY, SO POINTS DRAW LINES.',
                    'LONG EXPOSURE\nEACH FRAME KEEPS ABOUT 99% OF THE LAST ONE.\nA SPINNING POINT LEAVES ITS ORBIT BEHIND.',
                    'LONG EXPOSURE\nABOUT 3,100 POINTS OF 123,904, TURNING FAST.\nTHE TRAILS ARE VIDEO FEEDBACK.']),
    # 5 the object as a print screen of big flat discs in two inks on coloured paper, cropped close
    dict(name='raster', cmode=2, cellpx=18.0, dmul=0.58, ang=0.45, tgtx=0.35, captop=1, burst=0.0,
         bg=1, glow=0.0, vig=0.15, echo=0.0, decay=0.0, decaye=0.0, zoom=0.0,
         papers=[YELLOW, PINK, IVORY], inks=[INK, INK, INK], inks2=[RED, IVORY, BLUE],
         capsize=40, capcol=INK, dcapsize=40,
         dcaptions=['A HALFTONE\nMADE OF POINTS.', 'DARKER SURFACE,\nBIGGER DOT.', 'THE NEAREST POINT\nWINS EACH CELL.'],
         inmode=1, ishapes=[PIC], indmul=1.25, intgtx=0.0, intgty=0.27, incell=12.0),
    # 6 two objects in two inks, seen from the floor, a strand of points forever pulled from one into the other
    dict(name='duel', layout=2, cmode=3, dfix=3.9, fov=52.0, hfix=-0.28, tgty=0.08,
         swing=0.6, glow=1.0, vig=0.8, echo=0.9, decay=0.86, decaye=0.06, zoom=0.5, burst=0.7,
         inks=[RED, YELLOW, GREEN], inks2=[BLUE, PINK, IVORY],
         capcol=IVORY, capplate=0.7,
         dcaptions=['TWO SHAPES, ONE CLOUD: HALF THE POINTS EACH.\nA STRAND OF POINTS CROSSES FROM ONE TO THE OTHER.\nKICKS TEAR MORE OF THEM LOOSE.',
                    'ONE INK PER SHAPE. A POINT IN THE STRAND\nCHANGES INK AS IT CROSSES, IN FOUR BEATS.',
                    '6% OF THE POINTS ARE ALWAYS IN TRANSIT.\nA HARD KICK PULLS A QUARTER OF THEM\nOUT OF THEIR SHAPE.']),
    # 7 a phrase as landscape, printed in one ink on coloured stock and fading into it with distance,
    #   the camera raking along the letters from one end
    dict(name='phrase', shapes=[LAYOUT.index('word_made'), LAYOUT.index('word_out'), LAYOUT.index('word')],
         dfix=1.9, fov=55.0, hfix=0.04, ang=0.8, tgtx=0.5, swing=0.5, sizemul=0.75, mdur=0.22,
         sway=0.25, mono=1.0, fog=0.36, gain=1.0, maxpx=12.0, bg=1, glow=0.0, vig=0.3, echo=0.0, decay=0.0,
         decaye=0.0, zoom=0.0, burst=1.4,
         papers=['#A8322B', BLUE, '#6C7860'], inks=[IVORY, IVORY, '#DCE4C6'],
         dshapes=[D3, D0, D2], capplate=0.6, dang=0.45, ddfix=2.7, dtgtx=0.1, dtgty=-0.1,
         dcaptions=['LETTERS SAMPLED INTO 123,904 POINTS, IN ONE INK.\nDISTANCE FADES THEM INTO THE PAPER.'] * 3,
         inmode=1, ishapes=[PIC]),   # dark ink hid the letter faces (h_sheet.png)
]
NT = len(TAKES)
T = "int(op('shot')['take'])%" + str(NT)
SEED3 = "int(op('shot')['seed']*2.999)"


def _col(key):
    return tuple(dict(TAKE_DEFAULTS, **t)[key] for t in TAKES)


def C(name):
    return "op('ctl')['" + name + "']"


def _bake_shape(scene, i, name, callbacks):
    """Area-weighted sample of NPTS points on one shape; returns its atlas TOP (pos / colour / normal)."""
    y = 900 - i * 260
    is_word = name.startswith('word')
    if is_word:
        src = scene.create(td.textPOP, 'src_' + name)
        src.par.text = PHRASES[name]
        src.par.fontfile.expr = "mod.paths.font('archivo')"   # no assets: TouchDesigner's default face
        src.par.alignx = 'center'
        src.par.aligny = 'center'
        src.par.linespacing = -0.12
        src.par.extrude = True
        src.par.extrudedepth = 0.5          # raw units; sample_surface.py fits the phrase to 2.4 wide
    else:
        src = scene.create(td.fileinPOP, 'src_' + name)
        # no assets: the bundled teapot loads here, and sample_surface.py bakes a stand-in shape instead
        src.par.file.expr = "mod.paths.model_file(%r)" % name
        tex = scene.create(td.moviefileinTOP, 'tex_' + name)
        # no assets: a flat ivory tile, so the operator has a file (the stand-in bake does not read it)
        tex.par.file.expr = "mod.paths.model_texture(%r) or mod.paths.here('stand_in.png')" % name
        tex.nodeX, tex.nodeY = -2000, y - 110
    src.nodeX, src.nodeY = -2400, y
    # one point per triangle corner, so three consecutive points are one triangle
    tri = scene.create(td.facetPOP, 'tri_' + name)
    tri.par.operation = 'unique'
    tri.par.computenormals = False
    src.outputConnectors[0].connect(tri)
    tri.nodeX, tri.nodeY = -2200, y
    wanted = [('vp', 'P', 'point')]
    if not is_word:
        wanted += [('vn', 'N', 'vertex'), ('vt', 'Tex', 'vertex')]
    for j, (tag, attr, cls) in enumerate(wanted):
        t = scene.create(td.poptoTOP, tag + '_' + name)
        t.par.pop = tri.path
        t.par.rgbamode = 'custom'
        t.par.extract = cls
        t.par.layout = 'square'
        t.par.attribscope = attr
        t.nodeX, t.nodeY = -2000 + j * 150, y
    bake = scene.create(td.scriptTOP, 'bake_' + name)
    for d in list(bake.docked):
        d.destroy()
    bake.par.callbacks = callbacks.path
    bake.nodeX, bake.nodeY = -1400, y
    return bake


# Manual on the scene's custom page freezes the state for inspection (Shape = target, Morph = progress).
PROGRESS = "(parent().par.Morph if parent().par.Manual else min(1, op('hub')['section_pos']/op('ctl')['mdur']))"
IDX_A = "int(op('sel')['a'])"
IDX_B = "int(op('sel')['b'])"
# accent colour of each lettering slot, used for the room glow (linear light). The models' own
# accents come from the MODELS rows, each chosen against the object's colour.
SLOT_TINTS = {'word': (0.72, 0.13, 0.34), 'word_made': (0.03, 0.38, 0.62), 'word_out': (0.90, 0.15, 0.07),
              'mosaicA': (0.5, 0.5, 0.5), 'mosaicB': (0.5, 0.5, 0.5),
              'word_d0': (0.72, 0.13, 0.34), 'word_d1': (0.03, 0.38, 0.62), 'word_d2': (0.90, 0.15, 0.07),
              'word_d3': (0.03, 0.38, 0.62), 'word_pic': (0.03, 0.38, 0.62)}


def _configure(W):
    """Turn the scene's words into the tables the builder reads. Slot i of LAYOUT is SHAPES[i]."""
    global SHAPES, MOSAIC, PHRASES, TINTS, FRONT, HIGH, BACK, RED_FROM
    models = W['MODELS']
    assert len(models) == NMODELS, 'MODELS needs %d rows' % NMODELS
    for m in models:
        assert not m['name'].startswith(('word', 'mosaic')), m['name']
    row = {('model%d' % i): m for i, m in enumerate(models)}
    SHAPES = [row[n]['name'] if n in row else n for n in LAYOUT]
    MOSAIC = [m['name'] for m in models]
    PHRASES = dict(DESCRIBE_PHRASES, **W['PHRASES'])
    RED_FROM = float(W['RED_FROM'])
    TINTS = str(tuple(tuple(row[n]['tint']) if n in row else SLOT_TINTS[n] for n in LAYOUT))
    # yaw at which each shape shows its best side to a camera on +Z (found by looking, NOTES 06)
    FRONT = tuple(float(row[n]['front']) if n in row else 0.0 for n in LAYOUT)
    # how far above the object's middle the camera sits (an object whose face is its top wants more)
    HIGH = str(tuple(row[n]['high'] if n in row else (0.2 if n.startswith('word') else 0.32) for n in LAYOUT))
    # a factor on the fitted camera distance, for shapes that still crowd the frame when seen
    BACK = dict({m['name']: m['back'] for m in models}, word_pic=0.78)
    for t in TAKES:
        if t['name'] in W['CAPTIONS']:
            t.setdefault('captions', list(W['CAPTIONS'][t['name']]))
        if t['name'] in W['TAKE_SHAPES']:
            t.setdefault('shapes', [SHAPES.index(n) for n in W['TAKE_SHAPES'][t['name']]])
    # the first take also has a Describe list (its lettering replaced by lettering that explains)
    # and an Input list (the picture sheet between its first seven models)
    first = TAKES[0]
    swap = {LAYOUT.index('word'): D0, LAYOUT.index('word_made'): D1, LAYOUT.index('word_out'): D2}
    first['dshapes'] = [swap.get(i, i) for i in first['shapes']]
    first['ishapes'] = [j for i in [k for k in first['shapes'] if k not in WORDS][:7] for j in (PIC, i)]
    return


def _tables(baked):
    """Per-shape framing: (camera distance, height of its middle). Sizes are read from the bakes."""
    import numpy as np
    dist, mid = [], []
    for n, b in zip(SHAPES, baked):
        if n.startswith('mosaic'):
            dist.append(3.0)
            mid.append(0.0)
            continue
        b.cook(force=True)
        p = np.asarray(b.numpyArray(), dtype=np.float32)[0:SIDE, :, :3].reshape(-1, 3)
        sx, sy, sz = [float(v) for v in (p.max(axis=0) - p.min(axis=0))]
        is_word = n.startswith('word')
        lift, fillw = (0.22, 0.72) if is_word else (0.0, 0.55)
        hyp = sx if is_word else (sx * sx + sz * sz) ** 0.5
        # fit the turning footprint to the frame width and the height to the frame height,
        # then step back by half the depth because the near face is what fills the picture
        depth = 0.0 if is_word else 0.6 * max(sx, sz)
        back = BACK.get(n, 1.0)
        dist.append(round((max(hyp / fillw / 0.728, sy / 0.62 / 0.41) + depth) * back, 3))
        mid.append(round(-0.5 + lift + sy / 2, 3))
    return str(tuple(dist)), str(tuple(mid))


def _yaw(idx):
    # Shapes sway about their front instead of spinning: the word is never edge-on and a
    # model never spends a whole section showing its back. Takes can add a spin or a seeded turn.
    return ("(" + str(FRONT) + "[" + idx + "]+(parent().par.Yaw if parent().par.Manual else ("
            + C('sway') + "*(0.24 if (" + idx + ") in " + str(WORDS) + " else 0.4)*math.sin(op('hub')['evolve']*0.55+("
            + idx + ")*1.3)+" + C('spin') + "*op('hub')['evolve']+" + C('yawseed') + "*op('shot')['seed']*6.283)))")


def _shader(scene, name, rel, x, y):
    """Text DAT synced to a file of this experiment (rel is relative to the experiment's folder)."""
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here(%r)" % rel
    d.par.syncfile = True
    d.text = open(LIB['experiment'](SLUG, rel), encoding='utf-8').read()
    d.nodeX, d.nodeY = x, y
    return d


def _vecs(o, rows):
    """rows: [(name, (x, y, z, w))]; each component a number or an expression string."""
    o.seq.vec.numBlocks = len(rows)
    for i, (name, vals) in enumerate(rows):
        getattr(o.par, 'vec%dname' % i).val = name
        for c, v in zip('xyzw', vals):
            p = getattr(o.par, 'vec%dvalue%s' % (i, c))
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _chans(scene, name, rows, x, y):
    """Constant CHOP whose channels are expressions. rows: [(channel, expression string)]."""
    c = scene.create(td.constantCHOP, name)
    c.seq.const.numBlocks = len(rows)
    for i, (n, e) in enumerate(rows):
        getattr(c.par, 'const%dname' % i).val = n
        getattr(c.par, 'const%dvalue' % i).expr = e
    c.nodeX, c.nodeY = x, y
    return c


def build():
    scene = LIB['new_scene'](SLUG, 500, -700)
    _configure(LIB['scene_words'](scene, DEFAULTS))
    page = scene.customPages[0]
    page.appendToggle('Manual', label='Manual (ignore the section)')[0].val = False
    sh = page.appendInt('Shape', label='Shape (manual)')[0]
    sh.normMin, sh.normMax, sh.val = 0, NS - 1, 0
    page.appendFloat('Morph', label='Morph (manual)')[0].val = 1
    yw = page.appendFloat('Yaw', label='Yaw (manual, radians)')[0]
    yw.normMin, yw.normMax, yw.val = -3.2, 3.2, 0
    scene.store('side', SIDE)
    scene.store('cells', GRID[0] * GRID[1])
    scene.store('mosaic_models', MOSAIC)
    scene.store('mosaic_shift', 4)
    callbacks = _shader(scene, 'sample_surface', 'sample_surface.py', -1700, 1050)
    mosaic_cb = _shader(scene, 'mosaic', 'mosaic.py', -1500, 1050)
    _shader(scene, 'shoot_code', 'shoot.py', -1300, 1050)     # review helper: captures takes by schedule
    picture_cb = _shader(scene, 'picture', 'picture.py', -1100, 1050)
    _shader(scene, 'stand_in', 'stand_in.py', -900, 1050)        # shapes for model slots when there is no library
    baked = []
    for i, n in enumerate(SHAPES):
        if n.startswith('mosaic') or n == 'word_pic':
            b = scene.create(td.scriptTOP, 'bake_' + n)
            for d in list(b.docked):
                d.destroy()
            b.par.callbacks = (picture_cb if n == 'word_pic' else mosaic_cb).path
            b.nodeX, b.nodeY = -1400, 900 - i * 260
            baked.append(b)
        else:
            baked.append(_bake_shape(scene, i, n, callbacks))
    DIST, MID = _tables(baked)

    # ---- the take: one channel per column of TAKES, chosen by the shot's take number
    numeric = [k for k, v in TAKE_DEFAULTS.items() if isinstance(v, (int, float))]
    rows = [(k, str(_col(k)) + "[" + T + "]") for k in numeric]
    for key, pre, conv in (('papers', 'paper', hexlin), ('inks', 'ink', hexlin), ('inks2', 'inkb', hexlin)):
        table = str(tuple(tuple(conv(h) for h in t) for t in _col(key)))
        rows += [(pre + c, table + "[" + T + "][" + SEED3 + "][" + str(j) + "]") for j, c in enumerate('rgb')]
    capcol = str(tuple(hexs(h) for h in _col('capcol')))
    rows += [('cap' + c, capcol + "[" + T + "][" + str(j) + "]") for j, c in enumerate('rgb')]
    rows.append(('side', "1 if op('shot')['seed']>=0.5 else -1"))
    # Input is on when the parameter names a TOP outside this scene (never our own output: a cook loop)
    rows.append(('inon', "(lambda o: 1 if (o is not None and o.isTOP and not o.path.startswith(parent().path+'/')) else 0)"
                         "(op(parent().par.Input.eval()) if parent().par.Input.eval() else None)"))
    rows.append(('desc', "1 if parent().par.Describe else 0"))
    ctl = _chans(scene, 'ctl', rows, -800, 700)

    # ---- which pair of shapes: the section walks through the take's own list, the seed says where it starts
    # four tables: the take's own shapes, its Describe shapes, and both again with an Input picture
    def _lists(describe, inp):
        return tuple(tuple((t.get('ishapes') if inp else None) or (t.get('dshapes') if describe else None) or t['shapes'])
                     for t in TAKES)
    lists = ("(" + ",".join(str(_lists(d, i)) for i in (0, 1) for d in (0, 1))
             + ")[int(op('ctl')['inon'])*2+int(op('ctl')['desc'])]")
    walk = "(int(op('hub')['section'])+int(op('shot')['seed']*89))"
    pick = "(lambda L,n: L[n%len(L)])(" + lists + "[" + T + "],"
    _chans(scene, 'sel', [
        ('a', "(int(parent().par.Shape)-1)%" + str(NS) + " if parent().par.Manual else " + pick + walk + "-1)"),
        ('b', "int(parent().par.Shape)%" + str(NS) + " if parent().par.Manual else " + pick + walk + ")"),
    ], -800, 600)

    # from / to selectors
    sw = {}
    for k, (ab, idx) in enumerate([('A', IDX_A), ('B', IDX_B)]):
        s = scene.create(td.switchTOP, 'atlas' + ab)
        for b in baked:
            b.outputConnectors[0].connect(s)
        s.par.index.expr = idx
        s.nodeX, s.nodeY = -800, 400 - k * 150
        sw[ab] = s

    # ---- Input: the picture this scene is given to work on (another scene's out1). Blank: a black
    # 16 x 16 constant that nothing reads, because no take's list holds the picture sheet then.
    black = scene.create(td.constantTOP, 'in_black')
    black.par.colorr, black.par.colorg, black.par.colorb = 0, 0, 0
    black.par.outputresolution = 'custom'
    black.par.resolutionw, black.par.resolutionh = 16, 16
    black.nodeX, black.nodeY = -1000, -150
    insel = scene.create(td.selectTOP, 'in_sel')
    insel.par.top.expr = "parent().par.Input.eval() if op('ctl')['inon'] else 'in_black'"
    insel.nodeX, insel.nodeY = -800, -150

    # the cloud: a SIDE x SIDE grid of points whose xy is the address of its texel
    geo = scene.create(td.geometryCOMP, 'cloud')
    for c in geo.children:
        c.destroy()
    grid = geo.create(td.gridPOP, 'grid')
    grid.par.surftype = 'points'
    grid.par.cols = SIDE
    grid.par.rows = SIDE
    grid.par.normal = 'none'
    grid.par.texture = 'none'
    grid.render = True
    grid.display = True
    geo.par.instancing = True
    geo.par.instancecountmode = 'manual'
    geo.par.numinstances.expr = "int(" + C('inst') + ")"   # instance 1 is the reflection in the floor
    geo.nodeX, geo.nodeY = -400, 300

    vert = _shader(scene, 'cloud_vertex', 'shaders/cloud_vertex.glsl', -600, -300)
    pix = _shader(scene, 'cloud_pixel', 'shaders/cloud_pixel.glsl', -600, -420)
    mat = scene.create(td.glslMAT, 'cloud_mat')
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = vert.path
    mat.par.pdat = pix.path
    mat.seq.sampler.numBlocks = 3
    for i, ab in enumerate('AB'):
        getattr(mat.par, 'sampler%dname' % i).val = 's' + ab
        getattr(mat.par, 'sampler%dtop' % i).val = sw[ab].path
        getattr(mat.par, 'sampler%dfilter' % i).val = 'nearest'
    mat.par.sampler2name = 'sIn'
    mat.par.sampler2top = insel.path
    H = "op('hub')"
    AGE = "op('shot')['age']"
    wordA = "1 if " + IDX_A + " in " + str(WORDS) + " else 0"
    wordB = "1 if " + IDX_B + " in " + str(WORDS) + " else 0"
    cells = GRID[0] * GRID[1]
    focal = "640/math.tan(math.radians((" + C('fov') + ",14,100)[int(" + C('cam') + ")]/2))"
    _vecs(mat, [
        ('uMorph', (PROGRESS, H + "['evolve']", _yaw(IDX_A), _yaw(IDX_B))),
        ('uAudio', (H + "['hit_low']", H + "['bass']", H + "['vocals']", H + "['pulse']")),
        ('uAudio2', (H + "['hit_high']", H + "['energy']", H + "['hit_mid']", H + "['beat_pos']")),
        ('uLook', (1.8, -0.5, wordA, wordB)),
        ('uGain', (C('gain'), 0, 0, 0)),
        ('uAccent', (TINTS + "[" + IDX_B + "][0]", TINTS + "[" + IDX_B + "][1]", TINTS + "[" + IDX_B + "][2]",
                     H + "['section_pos']")),
        ('uTake', (C('layout'), C('cmode'), C('wscale'), C('nsign'))),
        ('uShot', (AGE, "op('shot')['seed']", C('burst'), focal)),
        ('uSize', (C('sizemul'), C('minpx'), C('maxpx'),
                   "(" + C('incell') + " if " + C('inon') + " and " + C('incell') + ">0 else " + C('cellpx') + ")")),
        ('uInk', (C('inkr'), C('inkg'), C('inkb'), C('mono'))),
        ('uInk2', (C('inkbr'), C('inkbg'), C('inkbb'), C('fog'))),
        ('uPaperM', (C('paperr'), C('paperg'), C('paperb'), "1 if " + C('bg') + " in (1, 3) else 0")),
        ('uGrid', (GRID[0], GRID[1], C('keep'), "int(" + H + "['beat_i'])%" + str(cells))),
        # x, y: shape A / B is the picture sheet; z: how far objects wear the picture; w: input mode (0 when no Input)
        ('uPic', ("1 if " + IDX_A + "==" + str(PIC) + " else 0", "1 if " + IDX_B + "==" + str(PIC) + " else 0",
                  C('inwear'), C('inmode') + "*" + C('inon'))),
        ('uDesc', (C('desc'), RED_FROM, 0, 0)),
    ])
    # opaque depth-tested points (additive was tried first: white models blew out, see NOTES 03)
    mat.nodeX, mat.nodeY = -400, -300
    geo.par.material = mat.path

    mixp = "(lambda p: p*p*(3-2*p))(" + PROGRESS + ")"

    def blend(table):
        return "(" + table + "[" + IDX_A + "]+(" + table + "[" + IDX_B + "]-" + table + "[" + IDX_A + "])*" + mixp + ")"
    WIDE = str(tuple(0.0 if n.startswith('word') else 1.0 for n in SHAPES))
    # the orbit camera steps back while the cloud is in flight, so the stream stays inside the frame
    fit = "(" + blend(DIST) + "*(1-0.08*op('hub')['energy'])*(1+0.32*math.sin(math.pi*" + PROGRESS + ")))"
    camctl = _chans(scene, 'camctl', [
        ('mid', blend(MID)),
        ('dist', "(" + C('ddfix') + " if " + C('desc') + " and " + C('ddfix') + ">0 else " + C('dfix') + " if " + C('dfix') + ">0 else " + fit + "*(" + C('indmul') + " if " + C('inon')
         + " and " + C('indmul') + ">0 else " + C('dmul') + "))"),
        ('tgtx', "(" + C('intgtx') + " if " + C('inon') + " and " + C('intgtx') + ">-50 else " + C('dtgtx') + " if " + C('desc') + " and " + C('dtgtx') + ">-50 else " + C('tgtx') + ")"),
        ('tgty', "(" + C('intgty') + " if " + C('inon') + " and " + C('intgty') + ">-50 else " + C('dtgty') + " if " + C('desc') + " and " + C('dtgty') + ">-50 else " + C('tgty') + ")"),
        ('ang', "(" + C('dang') + " if " + C('desc') + " and " + C('dang') + ">0 else " + C('ang') + ")*" + C('side')
         + "+" + C('swing')
         + "*0.30*math.sin(op('hub')['evolve']*0.13+op('shot')['seed']*6.283)"),
        ('hi', "(" + C('hfix') + " if " + C('hfix') + ">-50 else " + blend(HIGH) + ")"),
        ('wide', blend(WIDE)),
    ], -800, 100)
    K = "op('camctl')"
    target = scene.create(td.nullCOMP, 'target')
    target.par.ty.expr = K + "['mid']+" + K + "['tgty']"
    # the subject drifts between the thirds instead of sitting dead centre; the word stays centred
    target.par.tx.expr = ("0.28*math.sin(op('hub')['evolve']*0.11+1.0)*" + K + "['wide']*" + C('drift')
                          + "+" + K + "['tgtx']*" + C('side'))
    target.nodeX, target.nodeY = -400, 100
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.tx.expr = "op('target').par.tx+" + K + "['dist']*math.sin(" + K + "['ang'])"
    cam.par.tz.expr = K + "['dist']*math.cos(" + K + "['ang'])"
    cam.par.ty.expr = K + "['mid']+" + K + "['hi']+0.12*math.sin(op('hub')['evolve']*0.09)"
    cam.par.lookat = target.path
    cam.par.fov.expr = C('fov')
    cam.par.near = 0.05
    cam.par.far = 50
    cam.nodeX, cam.nodeY = -400, 0
    # plan view: straight down. The object turns under it (yawseed, spin), the camera does not.
    top = scene.create(td.cameraCOMP, 'cam_top')
    top.par.ty = 8
    top.par.rx = -90
    top.par.tx.expr = "0.12*math.sin(op('hub')['evolve']*0.17)"
    top.par.tz.expr = "0.08*math.cos(op('hub')['evolve']*0.13)"
    top.par.fov = 14
    top.par.near, top.par.far = 0.05, 50
    top.nodeX, top.nodeY = -250, 0
    # inside: at the middle of the scaled-up model, turning slowly
    inn = scene.create(td.cameraCOMP, 'cam_in')
    inn.par.tx.expr = "0.3*math.sin(op('hub')['evolve']*0.3)"
    inn.par.tz.expr = "0.3*math.cos(op('hub')['evolve']*0.23)"
    inn.par.ty.expr = "-0.5+" + C('wscale') + "*(" + K + "['mid']+0.5)"
    inn.par.ry.expr = "op('hub')['evolve']*22+op('shot')['seed']*360"
    inn.par.rx.expr = "14*math.sin(op('hub')['evolve']*0.21)"
    inn.par.fov = 100
    inn.par.near, inn.par.far = 0.05, 50
    inn.nodeX, inn.nodeY = -100, 0

    render = scene.create(td.renderTOP, 'render')
    render.par.camera.expr = "('cam','cam_top','cam_in')[int(" + C('cam') + ")]"
    render.par.geometry = geo.path
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.antialias = '1x'
    render.nodeX, render.nodeY = 0, 0

    fb = scene.create(td.feedbackTOP, 'trail_fb')
    trail = scene.create(td.glslTOP, 'trail')
    trail.par.pixeldat = _shader(scene, 'trail_frag', 'shaders/trail.frag', 200, -300).path
    trail.par.format = 'rgba16float'
    render.outputConnectors[0].connect(fb)
    render.outputConnectors[0].connect(trail.inputConnectors[0])
    fb.outputConnectors[0].connect(trail.inputConnectors[1])
    fb.par.top = trail.path
    # where the sculpture stands across the frame; only the orbit camera's subject wanders
    centre = "(0.5-op('target').par.tx/(0.728*max(1, op('cam').par.tz)) if " + C('cam') + "==0 and " \
        + C('drift') + ">0 else 0.5)"
    # a cut must not show the last visit's echo: the trail is emptied for the first frames of a shot
    _vecs(trail, [('uTrail', ("(" + C('decay') + "+" + C('decaye') + "*min(1, op('hub')['energy']))*(1 if " + AGE + ">0.07 else 0)",
                              "(0.004+0.016*op('hub')['hit_low']+0.008*op('hub')['pulse'])*(0.35 if "
                              + IDX_B + " in " + str(WORDS) + " else 1)*" + C('zoom'),
                              centre, 0.47))])
    fb.nodeX, fb.nodeY = 200, -150
    trail.nodeX, trail.nodeY = 400, 0

    # glow: a quarter-size blur. (Bloom TOP was tried: it lifted the whole frame to grey, NOTES 04.)
    small = scene.create(td.resolutionTOP, 'glow_small')
    small.par.outputresolution = 'custom'
    small.par.resolutionw, small.par.resolutionh = 320, 180
    trail.outputConnectors[0].connect(small)
    glow = scene.create(td.blurTOP, 'glow')
    glow.par.size = 14
    small.outputConnectors[0].connect(glow)
    small.nodeX, small.nodeY = 600, -150
    glow.nodeX, glow.nodeY = 750, -150

    post = scene.create(td.glslTOP, 'post')
    post.par.pixeldat = _shader(scene, 'post_frag', 'shaders/post.frag', 800, -300).path
    post.par.format = 'rgba8fixed'
    trail.outputConnectors[0].connect(post.inputConnectors[0])
    glow.outputConnectors[0].connect(post.inputConnectors[1])
    render.outputConnectors[0].connect(post.inputConnectors[2])
    _vecs(post, [
        ('uRoom', (0.33, H + "['energy']", H + "['pulse']", H + "['evolve']")),
        ('uRoom2', (H + "['hit_high']", H + "['vocals']", centre, 0)),
        ('uTint', (TINTS + "[" + IDX_B + "][0]", TINTS + "[" + IDX_B + "][1]", TINTS + "[" + IDX_B + "][2]", H + "['hit_low']")),
        ('uSec', (H + "['section_pos']", wordB, H + "['beat_pos']", 0)),
        ('uPost', (C('bg'), C('glow'), C('vig'), C('echo'))),
        ('uPaper', (C('paperr'), C('paperg'), C('paperb'), AGE)),
        ('uCap', (C('capplate') + "*" + C('desc'), 0, 0, 0)),     # Describe: a dark band behind the caption
    ])
    post.nodeX, post.nodeY = 800, 0

    # caption: a small line in the caption face, in a bottom corner, in the takes that have one
    caps = str(tuple(tuple(t) for t in _col('captions')))
    cap = scene.create(td.textTOP, 'caption')
    dcaps = str(tuple(tuple(t) for t in _col('dcaptions')))
    cap.par.text.expr = "(" + dcaps + " if parent().par.Describe else " + caps + ")[" + T + "][" + SEED3 + "]"
    cap.par.fontfile.expr = "mod.paths.font('chicago')"   # no assets: TouchDesigner's default face
    cap.par.fontsizex.expr = "(" + C('dcapsize') + " if parent().par.Describe else " + C('capsize') + ")"
    cap.par.alignx.expr = "'right' if op('ctl')['side']>0 else 'left'"
    cap.par.aligny.expr = "'top' if " + C('captop') + " else 'bottom'"
    cap.par.borderspace1, cap.par.borderspace2 = 44, 34
    cap.par.fontcolorr.expr, cap.par.fontcolorg.expr, cap.par.fontcolorb.expr = C('capr'), C('capg'), C('capb')
    cap.par.bgalpha = 0
    cap.par.outputresolution = 'custom'
    cap.par.resolutionw, cap.par.resolutionh = 1280, 720
    cap.nodeX, cap.nodeY = 800, 150
    over = scene.create(td.overTOP, 'titled')
    cap.outputConnectors[0].connect(over.inputConnectors[0])
    post.outputConnectors[0].connect(over.inputConnectors[1])
    over.nodeX, over.nodeY = 1000, 0
    over.outputConnectors[0].connect(scene.op('out1'))
    fb.par.resetpulse.pulse()
    return scene.path
