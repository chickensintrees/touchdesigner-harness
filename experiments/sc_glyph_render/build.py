# sc_glyph_render: library models (or a corridor) redrawn as running bitmap text, 1-bit.
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md). Idempotent:
# build() destroys /project1/sc_glyph_render and makes it again.
# Why things are the way they are: experiments/sc_glyph_render/NOTES.md
# No folder is named here: the repository is td.project.folder, and every file
# parameter is an expression on mod.paths (experiments/sw_hub/paths_module.py).
# see: NOTES.md "Assets" and log 29 (2026-11-11)
import td

SLUG = 'sc_glyph_render'
FONT = "mod.paths.font('chicago')"      # '' with no assets: TouchDesigner's default face

# ---------------------------------------------------------------------------
# DEFAULTS: everything this scene shows that is content and not technique. A pack may
# replace any of these names with its own scenes/sc_glyph_render/words.json; build()
# reads them once through scene_words and uses W[...] from there on.
#   MODELS   [name, scale, yaw] per model. All are loaded at build time and switched by
#            render flags, so a cut never loads anything. scale: the camera fov is
#            horizontal, so 1 unit is already large. yaw: degrees added to the model's
#            front (ry 0), for a model whose best side is not straight on.
#   PHRASES  the running text, in reading order. Upper case, ASCII 32..95 only.
#   POSTERS  the big words, chosen by section + seed ('|' = line break).
#   FACE, FACE_NOTE  what the Describe texts call the font the pack gives for 'chicago'
#            (they stand where the texts say {FACE} and {FACE_NOTE}).
#   FACE_SIZE  that font's size in cell widths, in the six atlases: as large as it can
#            be with its capitals still inside a cell (cells are 3 wide, 4 high).
# see: NOTES.md log 30 (2026-11-11)
# ---------------------------------------------------------------------------
DEFAULTS = {
    'FACE': 'MONOSPACE',
    'FACE_NOTE': 'THE SMALLEST SIZE USED HERE',
    'FACE_SIZE': 1.2,
    'MODELS': [
        ['marble_bust', 1.15, 0],
        ['space_helmet', 1.1, 0],
        ['gramophone', 1.15, 0],
        ['rubber_duck', 1.2, 0],
        ['hourglass', 1.15, 0],
        ['amphora', 1.15, 0],
    ],
    'PHRASES': [
        'EVERY FRAME IS MADE NOW.',
        'THIS PICTURE IS MADE OF LETTERS.',
        'SOUND IN. PICTURE OUT.',
        'PAST. PRESENT. LATER.',
        'LISTEN WITH YOUR EYES.',
        'FOUND, NOT MADE. KEPT, NOT EXPLAINED.',
        'NOTHING HERE IS PRERENDERED.',
        'BLACK OR WHITE. THERE IS NO GREY HERE.',
        'CATALOGUE NO. 0047: AMPHORA',
        'SIXTY FRAMES A SECOND, EVERY ONE NEW',
        'EVERYTHING IS TYPE',
        'HANDLE WITH BOTH HANDS.',
        'OBJECT OF THE DAY: PLATE 07',
        'SIGNAL ACQUIRED...',
        'FEEDBACK LOOP .... CLOSED',
        'DO NOT TOUCH',
        'EXHIBIT 12-B',
        'ORIGIN: UNRECORDED',
        'OBJECT OF UNKNOWN USE',
        'AMPHORA. HOURGLASS. GRAMOPHONE.',
        'LOOP. LOOP. LOOPLOOP.',
    ],
    'POSTERS': [
        'EVERY|FRAME IS|MADE NOW.',
        'MADE OF|TYPE.',
        'IN|REAL TIME',
        'HERE.|NOW.',
        'DO NOT|TOUCH',
        'ONE|BIT',
        'ITEM|0047',
        'ORIGIN|UNKNOWN',
        'LOOP.|LOOP.',
        'EVERYTHING|IS TYPE',
        'PLATE|12-B',
        'REAL|TIME',
        'NOTHING|IS STORED.',
    ],
}

# ---------------------------------------------------------------------------
# TAKES: one row per variation. The cutter sets the COMP's Take; row = Take % len(TAKES).
# Every number here becomes a channel of the `tk` CHOP; Seed varies things inside a take.
#   mode    what tone.frag draws: 0 lit model, 1 ghost (flat inverse silhouette on a
#           full wall of type), 2 corridor (no model), 3 keyhole (page seen through the word)
#   poster  0 none, 1 grey block word, 2 the word is a window (keyhole)
#   lo, hi  range of atlas sizes the bar's energy may choose (0..5 = 48 36 24 18 15 12 px)
#   chunk   screen pixels per bitmap pixel (+ up to chunkvar more, by seed)
#   quad    1 = quadtree: cell size chosen block by block from local contrast
#   tiles   the render repeated tiles x tiles (+ up to tilevar more, by seed), checker polarity
#   inv     1 = white page, black type
#   multi   how many models stand side by side (0 = none)
#   tx      model's distance from the frame centre (times side), drift = slow travel
#   msc     model scale multiplier, land = overshoot at the cut, swing = degrees of ry swing
#   void    least luminance of the void (0.33 = regular type everywhere)
#   tz cty crx dutch   camera distance, height, pitch, and roll range by seed
#   pcx pcy ps pj      poster centre, scale, and how far seed moves the centre
#   ticker  1 = every row is its own ticker, alternate rows run opposite ways
#   rev     how the page arrives: 0 rows top-down, 1 columns left to right, 2 random
#           cells, 3 centre out; revt = seconds it takes
#   dvoid   least luminance of the void while the COMP's Describe is on (the page take
#           fills its paper with regular type then, so the sentences can be read)
#   inz inj while the COMP's Input names a TOP: how far that picture is zoomed in,
#           and how far seed moves its centre
# Not channels (text):
#   describe  the running text while Describe is on: what this take is, in plain words.
#             Upper case and ASCII 32..95 only (the atlases hold nothing else), apart from
#             {FACE} and {FACE_NOTE}, which _say() fills from the words.
#   dwords    the poster words while Describe is on ('|' = line break), chosen by section + seed
# see: NOTES.md log 26 (Describe) and 27 (Input)
# ---------------------------------------------------------------------------
_BASE = dict(mode=0, poster=0, lo=1, hi=5, chunk=1, chunkvar=0, quad=0, tiles=1, tilevar=0, inv=0,
             multi=1, tx=0.52, drift=0.0, msc=1.0, land=0.5, swing=42, tz=3.3, cty=-0.05, crx=2.5,
             dutch=0, void=0.0, pcx=0.5, pcy=0.5, ps=1.0, pj=0.0, ticker=0, rev=0, revt=0.45,
             dvoid=0.0, inz=1.0, inj=0.0)
TAKES = [
    dict(_BASE, name='poster', poster=1, ps=0.9, pj=0.08,
         dwords=['DRAWN|IN TYPE', 'MADE OF|LETTERS', '1-BIT|TYPE'],
         describe='THIS PICTURE IS MADE OF TYPE. A 3D MODEL IS RENDERED, THEN A SHADER REDRAWS IT AS '
                  '{FACE} BITMAP LETTERS IN PURE BLACK AND WHITE. BRIGHTNESS NEVER PICKS THE LETTER, '
                  'ONLY ITS WEIGHT: BLANK, GREYED, REGULAR OR BOLD. LIT AREAS FLIP TO BLACK TYPE ON WHITE. '
                  'THE TEXT MOVES TWO CHARACTERS A BEAT. LOUDER BARS USE SMALLER LETTERS. THE SNARE '
                  'INVERTS THE FRAME. THE KICK FLASHES THE BIG WORD WHITE.'),
    dict(_BASE, name='wall', mode=1, lo=5, hi=5, tx=0.2, drift=0.45, msc=2.5, land=0.8, swing=25,
         ticker=1, rev=2, revt=0.4, dutch=10, inz=1.3, inj=0.1,
         dwords=[],
         describe='EVERY ROW IS ITS OWN TICKER. ALTERNATE ROWS RUN OPPOSITE WAYS. A ROW MOVES 2, 4 OR 6 '
                  'CHARACTERS A BEAT. THE 3D MODEL IS NOT DRAWN: WHERE IT IS LIT, THE WALL OF TYPE TURNS '
                  'TO INVERSE VIDEO. THIS IS 12 X 16 PIXEL {FACE}, {FACE_NOTE}. '
                  'THE SNARE FLIPS THE WHOLE WALL.'),
    dict(_BASE, name='macro', lo=1, hi=1, chunk=2, chunkvar=2, tx=0.12, msc=1.0, land=0.25,
         tz=1.35, cty=0.05, dutch=30, rev=2, revt=0.5, inz=2.6, inj=0.3,
         dwords=[],
         describe='MACRO: EVERY FONT PIXEL IS DRAWN 2 OR 3 SCREEN PIXELS WIDE. LIGHT TURNS THE TYPE TO '
                  'BLACK ON WHITE.'),
    dict(_BASE, name='page', poster=1, inv=1, multi=3, lo=3, hi=5, tx=0.0, msc=0.8, land=0.3,
         tz=3.6, cty=0.75, crx=-12, pcx=0.22, pcy=0.80, ps=0.34, pj=0.0, rev=1, revt=0.5, dvoid=0.33,
         dwords=['BLACK TYPE|WHITE PAGE', 'THE FRAME|INVERTED', 'THREE|MODELS'],
         describe='THE SAME SHADER WITH THE FRAME INVERTED: A WHITE PAGE OF BLACK TYPE. THREE 3D MODELS '
                  'SEEN FROM ABOVE ARE REDRAWN AS BLOCKS OF {FACE} BITMAP TEXT. THEIR LIT SIDES PRINT '
                  'BLACK, THE EMPTY SPACE AROUND THEM IS PAPER. THE PAGE IS TYPED IN FROM THE LEFT AT '
                  'EACH CUT. THE SNARE TURNS IT BLACK.'),
    dict(_BASE, name='corridor', mode=2, poster=1, multi=0, lo=3, hi=4, pcx=0.5, pcy=0.5,
         ps=0.2, pj=0.34, rev=3, revt=0.4,
         dwords=['NO 3D|MODEL', 'SHADER|CORRIDOR', 'NO|GEOMETRY'],
         describe='NO 3D MODEL HERE. THIS CORRIDOR IS A FEW LINES OF SHADER MATHS: ONE DIVIDE GIVES DEPTH, '
                  'THEN STRIPES BECOME CEILING TUBES, A CHECKER BECOMES CARPET AND RECTANGLES BECOME DOORS. '
                  'THE RESULT IS A BRIGHTNESS MAP, REDRAWN AS {FACE} BITMAP TYPE. IT TRAVELS HALF A TUBE '
                  'EVERY BEAT. THE KICK MAKES THE TUBES SURGE.'),
    dict(_BASE, name='quadtree', quad=1, void=0.33, tx=0.22, msc=1.9, land=0.3, rev=0, revt=0.01, dutch=6,
         inz=1.25, inj=0.1,
         dwords=[],
         describe='QUADTREE: THE FRAME STARTS AS 96 X 128 PIXEL LETTERS. A BLOCK SPLITS IN FOUR WHEREVER '
                  'THE PICTURE INSIDE IT HAS CONTRAST, DOWN TO 12 X 16. FLAT AREAS KEEP HUGE LETTERS, '
                  'EDGES GET TINY ONES. A KICK SPLITS MORE BLOCKS.'),
    dict(_BASE, name='wallpaper', lo=5, hi=5, tiles=3, tilevar=3, tx=0.0, msc=1.55, land=0.0,
         swing=42, rev=2, revt=0.3,
         dwords=[],
         describe='ONE RENDER OF A 3D MODEL, REPEATED AS A GRID OF 3 TO 5 TILES A SIDE. EVERY OTHER COLUMN '
                  'IS MIRRORED. EVERY OTHER TILE IS DRAWN IN NEGATIVE, AND THAT CHECKER SWAPS ON EACH BEAT. '
                  'THE LETTERS ARE NOT TILED: ONE PAGE OF 12 PIXEL TYPE RUNS ACROSS ALL OF THEM.'),
    dict(_BASE, name='keyhole', mode=3, poster=2, lo=4, hi=5, ps=1.3, pj=0.3, tx=0.0, drift=0.75, msc=1.1,
         land=0.4, swing=30, rev=0, revt=0.4,
         dwords=['WORD AS|WINDOW', 'TEXT AS|A MASK', 'KEYHOLE|IN TYPE'],
         describe='THE BIG WORD IS A WINDOW. THE PAGE OF TYPE EXISTS ONLY INSIDE ITS LETTERS. THE 3D MODEL '
                  'IS A BLACK HOLE IN THAT PAGE, WITH A WHITE OUTLINE THAT CARRIES ON OUTSIDE THE WORD. '
                  'KICKS AND BEATS FILL THE DARK AROUND IT WITH GREYED TYPE FOR A MOMENT.'),
]
TAKE_KEYS = [k for k in _BASE]
# The running text while Describe is on and Input names a TOP: then the picture is
# not this scene's model, so the take's own sentences would not be true.
DESCRIBE_INPUT = ('THIS IS ANOTHER SCENE\'S PICTURE, REDRAWN AS TYPE. ITS BRIGHTNESS IS CUT TO PURE BLACK AND '
                  'WHITE AND EVERY CELL BECOMES A {FACE} BITMAP LETTER. BRIGHTNESS NEVER PICKS THE LETTER, '
                  'ONLY ITS WEIGHT: BLANK, GREYED, REGULAR OR BOLD. THE TEXT MOVES TWO CHARACTERS A BEAT. '
                  'THE SNARE INVERTS THE FRAME.')
DWORDS_PER_TAKE = 3      # rows of the posters table per take; short lists repeat

SEP = '  '

# atlas: ASCII 32..95 in a 16x4 grid, one per cell size, rasterised 1:1.
# 12x16 is Chicago's native bitmap size and the floor: at 9x12 R and A become the
# same shape (NOTES.md log 04).
A_COLS, A_ROWS = 16, 4
CELLS = [(48, 64), (36, 48), (24, 32), (18, 24), (15, 20), (12, 16)]
LEVEL_AT = (0.38, 0.44, 0.50, 0.57)      # energy thresholds between sizes 1..5
PACK_W = A_COLS * CELLS[0][0]
PACK_H = sum(A_ROWS * c[1] for c in CELLS)


def _atl_glsl():
    """The packed atlas table exactly as glyph.frag must declare it."""
    rows, oy = [], 0
    for cw, ch in CELLS:
        rows.append('ivec3(%d, %d, %d)' % (cw, ch, oy))
        oy += A_ROWS * ch
    return 'const ivec3 ATL[%d] = ivec3[%d](%s);' % (len(CELLS), len(CELLS), ', '.join(rows))


CODES_CB = '''# Writes the running texts as one texel per character (ASCII code - 32), one row
# per text: row 0 the scene's phrases, then one row per take for Describe mode, then
# the Describe text used when Input is set. Rows are padded with spaces; the shader
# is told each row's real length.
import numpy as np

def onCook(scriptOp):
    rows = [op('phrase_text').text] + op('describe_text').text.split(chr(10))
    w = max(len(s) for s in rows)
    a = np.zeros((len(rows), w, 1), dtype=np.float32)
    for i, s in enumerate(rows):
        a[i, :len(s), 0] = [min(63, max(0, ord(ch) - 32)) for ch in s]
    scriptOp.copyNumpyArray(a)
    return
'''

# All six atlases in one texture, stacked from the bottom, so the shader can use
# any size (and several at once: the quadtree take) without a Switch TOP.
PACK_CB = '''# Stacks atlas0..N (one per cell size) into one mono texture, bottom up.
import numpy as np

def onCook(scriptOp):
    out = np.zeros((%d, %d, 1), dtype=np.float32)
    y = 0
    for k in range(%d):
        a = op('atlas%%d' %% k).numpyArray()
        h, w = a.shape[0], a.shape[1]
        out[y:y + h, 0:w, 0] = a[:, :, 0]
        y += h
    scriptOp.copyNumpyArray(out)
    return
''' % (PACK_H, PACK_W, len(CELLS))

HUB = "op('hub')"
SHOT = "op('shot')"
TK = "op('tk')"
TD_ = "op('tkd')"
SEC = "int(" + HUB + "['section'])"
SEED = "float(" + SHOT + "['seed'])"
AGE = "float(" + SHOT + "['age'])"
PUMP = "min(1.0, float(" + HUB + "['hit_low']))"
SIDE = TD_ + "['side']"
S1 = "((" + SEED + " * 7.31 + 0.13) % 1)"
S2 = "((" + SEED + " * 13.77 + 0.41) % 1)"
S3 = "((" + SEED + " * 29.11 + 0.70) % 1)"


def _strip(phrases):
    """The phrases as one running text, and where each one starts in it."""
    s, starts = '', []
    for p in phrases:
        bad = [ch for ch in p if not 32 <= ord(ch) <= 95]
        if bad:
            raise RuntimeError('phrase has characters the atlas lacks: %r in %r' % (bad, p))
        starts.append(len(s))
        s += p + SEP
    return s, starts


def _say(text, words=None):
    """A Describe text with the font's name filled in."""
    words = words or DEFAULTS
    return text.replace('{FACE_NOTE}', words['FACE_NOTE']).replace('{FACE}', words['FACE'])


def _describe_strips(words=None):
    """One running text per take plus the Input one, each ending in a separator."""
    rows = [_say(t['describe'], words) + SEP + ' ' for t in TAKES] + [_say(DESCRIBE_INPUT, words) + SEP + ' ']
    for r in rows:
        bad = [ch for ch in r if not 32 <= ord(ch) <= 95]
        if bad:
            raise RuntimeError('describe text has characters the atlas lacks: %r in %r' % (bad, r[:40]))
    return rows


def _const(scene, name, chans, x, y):
    c = scene.create(td.constantCHOP, name)
    c.nodeX, c.nodeY = x, y
    c.seq.const.numBlocks = len(chans)
    for i, (n, e) in enumerate(chans):
        getattr(c.par, 'const%dname' % i).val = n
        getattr(c.par, 'const%dvalue' % i).expr = e
    return c


def _obj_fit(path):
    """(centre, 1 / longest side) of an OBJ file, read from its `v` lines."""
    lo, hi = [1e30] * 3, [-1e30] * 3
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('v '):
                v = [float(x) for x in line.split()[1:4]]
                lo = [min(a, b) for a, b in zip(lo, v)]
                hi = [max(a, b) for a, b in zip(hi, v)]
    size = max(h - l for h, l in zip(hi, lo))
    return [(h + l) / 2 for h, l in zip(hi, lo)], (1.0 / size if size > 0 else 1.0)


def _atlas_font_size(raw, cw, pack_font, face_size):
    """Font size in pixels for a cell `cw` wide. A pack's font is `face_size` cell
    widths: 1 for Chicago, whose W is one em wide (measuring it instead gave 35 and 17
    for the 36 and 18 px cells). With no font at all (TouchDesigner's default face) it
    is the largest size at which the widest character still fits the cell."""
    size = int(round(cw * face_size)) if pack_font else cw
    while size > 6 and not pack_font:
        raw.par.fontsizex = size
        if max(raw.evalTextSize(chr(c))[0] for c in range(33, 32 + A_COLS * A_ROWS)) <= cw:
            break
        size -= 1
    raw.par.fontsizex = size
    return size


def build():
    LIB = {'op': op}
    exec(open(td.project.folder.replace(chr(92), '/') + '/experiments/sw_hub/scene_lib.py',
              encoding='utf-8').read(), LIB)
    frag = open(LIB['experiment'](SLUG, 'shaders/glyph.frag'), encoding='utf-8').read()
    if _atl_glsl() not in frag:
        raise RuntimeError('glyph.frag ATL table does not match CELLS: expected ' + _atl_glsl())

    scene = LIB['new_scene'](SLUG, 750, -700)
    # the installed module, not LIB: only it sees the COMP's Assets parameter
    paths_dat = scene.op('local/modules/paths')
    paths_dat.cook(force=True)
    P = paths_dat.module
    W = LIB['scene_words'](scene, DEFAULTS)      # the pack's words.json wins, name by name
    MODELS, POSTERS = W['MODELS'], W['POSTERS']
    NT, NM = len(TAKES), len(MODELS)

    # ---------------- the take table as channels ----------------
    pick = "[int(" + SHOT + "['take']) % " + str(NT) + "]"
    _const(scene, 'tk', [(k, repr(tuple(t[k] for t in TAKES)) + pick) for k in TAKE_KEYS], -600, 330)
    # Input: 1 while the COMP's Input names a TOP outside this scene (a scene must
    # never read its own output). Describe: which row of `codes` the text comes from.
    _const(scene, 'inp', [
        ('on', "1 if (lambda o: o is not None and o.isTOP and not o.path.startswith(parent().path + '/'))"
               "(op(parent().par.Input.eval().strip() or '/none')) else 0"),
    ], -800, 330)
    _const(scene, 'dsc', [
        ('on', "1 if parent().par.Describe else 0"),
        ('row', "0 if not parent().par.Describe else (" + str(NT + 1) + " if op('inp')['on'] else 1 + int("
                + SHOT + "['take']) % " + str(NT) + ")"),
    ], -800, 200)
    DSC = "op('dsc')['on']"
    tnames = scene.create(td.tableDAT, 'take_names')
    tnames.nodeX, tnames.nodeY = -600, 440
    tnames.clear()
    for i, t in enumerate(TAKES):
        tnames.appendRow([i, t['name']])

    # energy wobbles across the thresholds about twice a second (453 changes in
    # the 249 s track), so the cell size is taken once per bar: sample and hold
    e_now = scene.create(td.selectCHOP, 'energy_now')
    e_now.nodeX, e_now.nodeY = -400, -200
    e_now.par.chop = 'hub'
    e_now.par.channames = 'energy'
    bar_gate = scene.create(td.constantCHOP, 'bar_gate')
    bar_gate.nodeX, bar_gate.nodeY = -400, -300
    bar_gate.par.const0name = 'gate'      # on for the first half of each bar: rises on the bar line
    bar_gate.par.const0value.expr = "1 if " + HUB + "['bar'] < 0.5 else 0"
    held = scene.create(td.holdCHOP, 'energy_bar')
    held.nodeX, held.nodeY = -250, -250
    e_now.outputConnectors[0].connect(held.inputConnectors[0])
    bar_gate.outputConnectors[0].connect(held.inputConnectors[1])
    held.par.sample = 'offtoon'

    # values derived from take + seed + feed (a Constant CHOP may not read itself)
    tiles = "(" + TK + "['tiles'] + int(" + S2 + " * " + TK + "['tilevar']))"
    _const(scene, 'tkd', [
        ('side', "(1 if (" + SEC + " + int(" + SEED + " * 8)) % 2 else -1)"),
        ('base', "(" + SEC + " + int(" + SEED + " * 31)) % " + str(NM)),
        ('s1', S1), ('s2', S2), ('s3', S3),
        # louder bar -> finer type, inside the take's own range
        ('lvl', "max(" + TK + "['lo'], min(" + TK + "['hi'], 1 + sum(op('energy_bar')['energy'] > t for t in "
                + repr(LEVEL_AT) + ")))"),
        ('chunk', TK + "['chunk'] + int(" + S3 + " * " + TK + "['chunkvar'])"),
        ('tiles', tiles),
        # the wallpaper arrives as one tile and zooms out to its grid
        ('tiles_now', "1 + (" + tiles + " - 1) * min(1.0, " + AGE + " / 0.45) ** 0.5"),
        # page reveal: retyped at each section change and at each cut
        ('rev', "min(1.0, float(" + HUB + "['section_pos']) / 0.08, " + AGE + " / " + TK + "['revt'])"),
        # Describe: the take's own words, which sit after the scene's own rows of the table
        ('poster', "(" + SEC + " + int(" + SEED + " * 53)) % " + str(len(POSTERS)) + " if not " + DSC
                   + " else " + str(len(POSTERS)) + " + (int(" + SHOT + "['take']) % " + str(NT) + ") * "
                   + str(DWORDS_PER_TAKE) + " + (" + SEC + " + int(" + SEED + " * 53)) % " + str(DWORDS_PER_TAKE)),
    ], -600, 200)

    # ---------------- 3D: the models; `base` picks one, `multi` shows its neighbours ----------------
    for i, (slug, mscale, yaw) in enumerate(MODELS):
        geo = LIB['import_model'](scene, 'm%d' % i, slug)
        geo.nodeX, geo.nodeY = -200, 300 - i * 110
        slot = "((" + str(i) + " - int(" + TD_ + "['base'])) % " + str(NM) + ")"
        geo.par.render.expr = slot + " < " + TK + "['multi']"
        # kick: the model swells; cut: it lands from larger
        geo.par.scale.expr = (str(mscale) + " * " + TK + "['msc'] * (1 + 0.07 * " + PUMP + ")"
                              " * (1 + " + TK + "['land'] * math.exp(-9 * " + AGE + "))")
        geo.par.tx.expr = ("(" + slot + " - 1) * 1.08 if " + TK + "['multi'] > 1 else " + TK + "['tx'] * " + SIDE
                           + " + " + TK + "['drift'] * math.sin(" + HUB + "['evolve'] * 0.45 + 6.283 * " + S1 + ")")
        geo.par.ty.expr = "0.04 * math.sin(" + HUB + "['evolve'] * 0.7 + " + slot + ")"
        # ry 0 is the model's front. A full spin showed the back half the time (a
        # white lump, NOTES.md log 16), so it swings about the front, turned a
        # little toward the frame centre, leans into each beat, and whips once
        # round as each section's page is typed.
        geo.par.ry.expr = ("-16 * " + SIDE + " + " + TK + "['swing'] * math.sin(" + HUB + "['evolve'] * 0.55 + 2 * " + slot + ")"
                           " + 10 * math.sin(" + HUB + "['beat_pos'] * math.pi)"
                           " + 360 * (1 - min(1.0, float(" + HUB + "['section_pos']) / 0.10)) ** 3")
        if yaw:
            geo.par.ry.expr += " + %s" % yaw
        geo.par.rx.expr = "8 * math.sin(" + HUB + "['evolve'] * 0.5) - 10 * " + PUMP
        geo.par.rz.expr = "5 * math.sin(" + HUB + "['bar_pos'] * math.pi)"
        mat = geo.op('mat')
        mat.par.roughness = 0.45
        # no library: the mesh is TouchDesigner's teapot (mod.paths.model_file). An empty
        # Movie File In warns "File not found", so the texture falls back to grey bands (white left the teapot bare: no type on it).
        geo.op('tex').par.file.expr = "mod.paths.model_texture(%r) or mod.paths.here('data/standin.png')" % slug
        mat.par.basecolormap = geo.op('tex').path      # the scaffold leaves it unset with no library
        if not P.have('models/%s/model.obj' % slug):
            # the teapot is not centred or 1 unit long as the library models are
            centre, k = _obj_fit(P.model_file(slug))
            k *= 1.3      # it is long where the library models are tall: at 1 unit it looked small
            fit = geo.create(td.transformPOP, 'fit')
            geo.op('mesh').outputConnectors[0].connect(fit)
            fit.par.scale = k
            fit.par.tx, fit.par.ty, fit.par.tz = [-c * k for c in centre]
            fit.render = fit.display = True
            geo.op('mesh').render = geo.op('mesh').display = False
            geo.par.ry.expr += " + %d" % (i * 60)      # six teapots: at least not six identical views
        # load now: a hidden model's first cook (25-50 ms mesh, 13 ms texture)
        # would otherwise land on the cut that first shows it
        geo.op('mesh').cook(force=True)
        geo.op('tex').cook(force=True)

    cam = scene.create(td.cameraCOMP, 'cam')
    cam.nodeX, cam.nodeY = -200, -380
    cam.par.tz.expr = TK + "['tz']"
    cam.par.ty.expr = TK + "['cty'] + 0.3 * " + TK + "['dutch'] / 30 * (" + S1 + " - 0.5)"
    cam.par.rx.expr = TK + "['crx']"
    cam.par.rz.expr = TK + "['dutch'] * (2 * " + S2 + " - 1)"
    cam.par.fov = 42

    # key from the frame centre side and above; rim from behind on the outer side
    key = scene.create(td.lightCOMP, 'key')
    key.nodeX, key.nodeY = -200, -490
    key.par.tx.expr = "-2.4 * " + SIDE
    key.par.ty, key.par.tz = 2.0, 2.6
    key.par.dimmer = 3.0
    rim = scene.create(td.lightCOMP, 'rim')
    rim.nodeX, rim.nodeY = -200, -600
    rim.par.tx.expr = "3.2 * " + SIDE
    rim.par.ty, rim.par.tz = 0.6, -2.2
    rim.par.dimmer = 3.0

    # weak fill from the camera so most of the model is on the inverse-video side
    fill = scene.create(td.lightCOMP, 'fill')
    fill.nodeX, fill.nodeY = -200, -670
    fill.par.tz = 3.3
    fill.par.dimmer = 0.22

    render = scene.create(td.renderTOP, 'render')
    render.nodeX, render.nodeY = 0, 100
    render.par.camera = cam.path
    render.par.geometry = 'm*'
    render.par.lights = 'key rim fill'
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.bgcolora = 0
    render.par.filtertype = 'mipmap'      # the wallpaper take reads it several times smaller

    # ---------------- poster word ----------------
    posters = scene.create(td.tableDAT, 'posters')
    posters.nodeX, posters.nodeY = -200, -800
    poster = scene.create(td.textTOP, 'poster')
    poster.nodeX, poster.nodeY = 0, -60
    poster.par.fontfile.expr = FONT
    poster.par.outputresolution = 'custom'
    poster.par.resolutionw, poster.par.resolutionh = 1280, 720
    # 'alwaysfit' fits the width only and lets a two-line stack run off the top
    # and bottom, so measure each stack once and store its size
    poster.par.fontautosize = 'nofit'
    poster.par.fontsizexunit = 'pixels'
    poster.par.fontsizex = 100
    poster.par.alignx = 'center'
    poster.par.aligny = 'center'
    poster.par.alignymode = 'bbox'
    poster.par.bgalpha = 1
    poster.par.filtertype = 'mipmap'      # tone.frag draws it smaller in some takes
    posters.clear()
    dwords = []
    for t in TAKES:
        ws = t['dwords'] or [t['name'].upper()]      # a take with no words never shows its row
        dwords += [ws[k % len(ws)] for k in range(DWORDS_PER_TAKE)]
    for p in POSTERS + dwords:
        w, h = poster.evalTextSize(p.replace('|', chr(10)))
        posters.appendRow([p, round(100 * min(1220.0 / w, 680.0 / h), 1)])
    row = "op('posters')[int(" + TD_ + "['poster'])"
    poster.par.text.expr = row + ", 0].val.replace('|', chr(10))"
    poster.par.fontsizex.expr = row + ", 1]"

    # ---------------- tone: one luminance plane ----------------
    tone_src = scene.create(td.textDAT, 'tone_frag')
    tone_src.nodeX, tone_src.nodeY = 200, -120
    tone_src.par.file.expr = "mod.paths.here('shaders/tone.frag')"
    tone_src.par.syncfile = True
    tone = scene.create(td.glslTOP, 'tone')
    tone.nodeX, tone.nodeY = 400, 0
    tone.par.pixeldat = tone_src
    tone.par.outputresolution = 'custom'
    tone.par.resolutionw, tone.par.resolutionh = 1280, 720
    tone.par.format = 'rgba16float'
    tone.par.inputfiltertype = 'mipmap'
    # ---------------- Input: another scene's picture in place of the render ----------------
    # The render is where a picture enters the technique, so that is where the switch is.
    # `inprep` turns the picture into what tone.frag expects of a render: luminance,
    # with the dark parts keyed out as void (alpha 0) so it keeps a silhouette and a rim.
    insel = scene.create(td.selectTOP, 'insel')
    insel.nodeX, insel.nodeY = 0, 330
    insel.par.top.expr = "parent().par.Input.eval().strip() if op('inp')['on'] else 'render'"
    prep_src = scene.create(td.textDAT, 'inprep_frag')
    prep_src.nodeX, prep_src.nodeY = 0, 220
    prep_src.par.file.expr = "mod.paths.here('shaders/inprep.frag')"
    prep_src.par.syncfile = True
    inprep = scene.create(td.glslTOP, 'inprep')
    inprep.nodeX, inprep.nodeY = 200, 330
    inprep.par.pixeldat = prep_src
    inprep.par.outputresolution = 'custom'
    inprep.par.resolutionw, inprep.par.resolutionh = 1280, 720
    inprep.par.format = 'rgba16float'
    inprep.par.inputfiltertype = 'linear'
    inprep.par.inputextenduv = 'mirror'
    inprep.par.filtertype = 'mipmap'
    insel.outputConnectors[0].connect(inprep.inputConnectors[0])
    inprep.seq.vec.numBlocks = 2
    inprep.par.vec0name = 'uIn'
    # zoom: the take's own, the landing at the cut and the kick's swell, like the model
    inprep.par.vec0valuex.expr = (TK + "['inz'] * (1 + 0.07 * " + PUMP + ") * (1 + 0.5 * " + TK
                                  + "['land'] * math.exp(-9 * " + AGE + "))")
    inprep.par.vec0valuey.expr = "math.radians(" + TK + "['dutch'] * (2 * " + S2 + " - 1))"
    inprep.par.vec0valuez.expr = TK + "['inj'] * (" + S1 + " - 0.5)"
    inprep.par.vec0valuew.expr = TK + "['inj'] * (" + S3 + " - 0.5)"
    inprep.par.vec1name = 'uKey'
    inprep.par.vec1valuex, inprep.par.vec1valuey, inprep.par.vec1valuez = 2.0, 0.07, 0.13
    src = scene.create(td.switchTOP, 'src')
    src.nodeX, src.nodeY = 200, 100
    render.outputConnectors[0].connect(src.inputConnectors[0])
    inprep.outputConnectors[0].connect(src)
    src.par.index.expr = "int(op('inp')['on'])"
    src.par.filtertype = 'mipmap'
    src.outputConnectors[0].connect(tone.inputConnectors[0])
    poster.outputConnectors[0].connect(tone.inputConnectors[1])
    tone.seq.vec.numBlocks = 5
    tone.par.vec4name = 'uVoid'
    tone.par.vec4valuex.expr = TK + "['void']"
    tone.par.vec4valuez.expr = TK + "['dvoid'] * " + DSC
    tone.par.vec4valuey.expr = "op('inp')['on']"
    tone.par.vec0name = 'uTone'
    tone.par.vec0valuex.expr = PUMP
    tone.par.vec0valuey.expr = SIDE
    tone.par.vec0valuez.expr = HUB + "['evolve']"
    tone.par.vec0valuew.expr = TK + "['mode']"
    tone.par.vec1name = 'uPost'
    tone.par.vec1valuex.expr = TK + "['pcx'] + " + TK + "['pj'] * (" + S1 + " - 0.5)"
    tone.par.vec1valuey.expr = TK + "['pcy'] + 0.5 * " + TK + "['pj'] * (" + S2 + " - 0.5)"
    tone.par.vec1valuez.expr = TK + "['ps']"
    tone.par.vec1valuew.expr = HUB + "['beat_pos']"
    tone.par.vec2name = 'uShot'
    tone.par.vec2valuex.expr = AGE
    tone.par.vec2valuey.expr = S1
    tone.par.vec2valuez.expr = S2
    tone.par.vec2valuew.expr = S3
    tone.par.vec3name = 'uMod'
    tone.par.vec3valuex.expr = TK + "['tx'] * " + SIDE + " * (1 if " + TK + "['multi'] == 1 else 0)"
    tone.par.vec3valuey.expr = TD_ + "['tiles_now']"
    tone.par.vec3valuez.expr = TD_ + "['tiles']"
    tone.par.vec3valuew.expr = "int(" + HUB + "['beat_i']) % 2"      # the checker of tiles swaps on each beat

    # ---------------- glyph atlases: one per cell size, rasterised 1:1 ----------------
    # see: NOTES.md log "02" (one scaled atlas lost every horizontal stroke at 8 px)
    for k, (cw, ch) in enumerate(CELLS):
        raw = scene.create(td.textTOP, 'atlas%d' % k)
        raw.nodeX, raw.nodeY = 400, -300 - k * 110
        raw.par.fontfile.expr = FONT
        raw.par.legacyparsing = False
        raw.par.wordwrap = False
        raw.par.smartpunct = False
        raw.par.outputresolution = 'custom'
        raw.par.resolutionw, raw.par.resolutionh = A_COLS * cw, A_ROWS * ch
        raw.par.fontautosize = 'nofit'
        raw.par.fontsizexunit = 'pixels'
        _atlas_font_size(raw, cw, bool(P.font('chicago')), W['FACE_SIZE'])
        raw.par.alignx = 'left'
        raw.par.aligny = 'bottom'
        raw.par.bgalpha = 1
        raw.par.format = 'r8fixed'
        raw.par.filtertype = 'nearest'
        spec = scene.create(td.tableDAT, 'atlas%d_spec' % k)
        spec.nodeX, spec.nodeY = 200, -300 - k * 110
        spec.clear()
        spec.appendRow(['x', 'y', 'text'])
        for code in range(1, A_COLS * A_ROWS):      # 0 is space: leave the cell empty
            col, row_ = code % A_COLS, code // A_COLS
            w = raw.evalTextSize(chr(32 + code))[0]
            # whole-pixel positions: a half-pixel offset blurs the bitmap
            spec.appendRow([col * cw + int((cw - w) // 2),
                            (A_ROWS - 1 - row_) * ch + int(ch * 0.25), chr(32 + code)])
        raw.par.specdat = spec
        raw.cook(force=True)
    pack = scene.create(td.scriptTOP, 'atlas')
    pack.nodeX, pack.nodeY = 650, -300
    pcb = pack.par.callbacks.eval()
    if pcb is None:
        pcb = scene.create(td.textDAT, 'atlas_callbacks')
        pack.par.callbacks = pcb
    pcb.nodeX, pcb.nodeY = 650, -410
    pcb.text = PACK_CB
    pack.par.filtertype = 'nearest'
    pack.cook(force=True)

    # ---------------- running text as a strip of character codes ----------------
    strip, starts = _strip(W['PHRASES'])
    ptxt = scene.create(td.textDAT, 'phrase_text')
    ptxt.nodeX, ptxt.nodeY = 200, -1000
    ptxt.text = strip
    dstrips = _describe_strips(W)
    dtxt = scene.create(td.textDAT, 'describe_text')
    dtxt.nodeX, dtxt.nodeY = 0, -1000
    dtxt.text = chr(10).join(dstrips)
    lens = tuple([len(strip)] + [len(r) for r in dstrips])
    st = scene.create(td.tableDAT, 'starts')
    st.nodeX, st.nodeY = 200, -1110
    st.clear()
    for s in starts:
        st.appendRow([s])
    codes = scene.create(td.scriptTOP, 'codes')
    codes.nodeX, codes.nodeY = 400, -1000
    cb = codes.par.callbacks.eval()
    if cb is None:
        cb = scene.create(td.textDAT, 'codes_callbacks')
        codes.par.callbacks = cb
    cb.nodeX, cb.nodeY = 400, -1110
    cb.text = CODES_CB
    codes.cook(force=True)

    # ---------------- the glyph pass ----------------
    glyph_src = scene.create(td.textDAT, 'glyph_frag')
    glyph_src.nodeX, glyph_src.nodeY = 600, -120
    glyph_src.par.file.expr = "mod.paths.here('shaders/glyph.frag')"
    glyph_src.par.syncfile = True
    glyph = scene.create(td.glslTOP, 'glyph')
    glyph.nodeX, glyph.nodeY = 900, 0
    glyph.par.pixeldat = glyph_src
    glyph.par.outputresolution = 'custom'
    glyph.par.resolutionw, glyph.par.resolutionh = 1280, 720
    glyph.par.format = 'rgba8fixed'
    glyph.par.inputfiltertype = 'linear'
    glyph.par.filtertype = 'nearest'
    # GLSL TOP has separate input connectors: connect(op) would replace input 0 each time
    tone.outputConnectors[0].connect(glyph.inputConnectors[0])
    pack.outputConnectors[0].connect(glyph.inputConnectors[1])
    codes.outputConnectors[0].connect(glyph.inputConnectors[2])
    glyph.seq.vec.numBlocks = 5
    ROW = "int(op('dsc')['row'])"
    glyph.par.vec4name = 'uRow'
    glyph.par.vec4valuex.expr = ROW
    glyph.par.vec0name = 'uCell'
    glyph.par.vec0valuex.expr = TD_ + "['lvl']"
    glyph.par.vec0valuey.expr = TD_ + "['chunk']"
    glyph.par.vec0valuez.expr = TD_ + "['rev']"
    glyph.par.vec0valuew.expr = TK + "['rev']"
    glyph.par.vec1name = 'uText'
    glyph.par.vec1valuex.expr = HUB + "['beat_pos'] * 2"     # two characters a beat (floored in the shader)
    glyph.par.vec1valuey.expr = repr(lens) + "[" + ROW + "]"
    # Describe: every text starts at its beginning; a sentence is the unit there
    glyph.par.vec1valuez.expr = ("op('starts')[(" + SEC + " * 5 + int(" + SEED + " * 97)) % "
                                 + str(len(starts)) + ", 0] if " + ROW + " == 0 else 0")
    # hats scatter stray characters; half as many in Describe, where the sentences have to be read
    glyph.par.vec1valuew.expr = "min(1.0, float(" + HUB + "['hit_high'])) * (0.5 if " + DSC + " else 1)"
    glyph.par.vec2name = 'uFx'
    # snare: inverse video; the page take is inverse to begin with, so there the snare gives black
    glyph.par.vec2valuex.expr = "(1 if " + HUB + "['hit_mid'] > 0.45 else 0) ^ int(" + TK + "['inv'])"
    glyph.par.vec2valuey.expr = "absTime.frame % 100000"
    glyph.par.vec2valuez = 0.22
    # poster rests as a grey block and snaps to a white one on each kick and,
    # briefly, on each beat
    glyph.par.vec2valuew.expr = ("1 if (" + HUB + "['pulse'] > 0.6 or " + HUB + "['hit_low'] > 0.25) else 0")
    glyph.par.vec3name = 'uMode'
    glyph.par.vec3valuex.expr = TK + "['poster']"
    glyph.par.vec3valuey.expr = TK + "['quad']"
    glyph.par.vec3valuez.expr = TK + "['ticker']"
    # quadtree: contrast a block needs before it splits. Starts out of reach at the
    # cut (all coarse), settles in half a second; a kick splits more blocks
    glyph.par.vec3valuew.expr = "0.16 + 3 * (1 - min(1.0, " + AGE + " / 0.5)) ** 2 - 0.11 * " + PUMP

    glyph.outputConnectors[0].connect(scene.op('out1'))

    # inspection only (not upstream of out1, so it costs nothing unless viewed):
    # the middle 320x180 of the frame at 4x, to read the letters
    zc = scene.create(td.cropTOP, 'zoom_crop')
    zc.nodeX, zc.nodeY = 900, 200
    for n, v in (('cropleft', 480), ('cropright', 800), ('cropbottom', 270), ('croptop', 450)):
        getattr(zc.par, n + 'unit').val = 'pixels'
        getattr(zc.par, n).val = v
    glyph.outputConnectors[0].connect(zc)
    zoom = scene.create(td.resolutionTOP, 'zoom')
    zoom.nodeX, zoom.nodeY = 1050, 200
    zoom.par.outputresolution = 'custom'
    zoom.par.resolutionw, zoom.par.resolutionh = 1280, 720
    zoom.par.inputfiltertype = 'nearest'
    zoom.par.filtertype = 'nearest'
    zc.outputConnectors[0].connect(zoom)
    return scene.path
