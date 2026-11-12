# sc_riso_press: a risograph / screen-print press. A three-light 3D render is separated
# into spot-colour plates, each screened and overprinted out of register on moving paper.
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md). Idempotent.
# see: experiments/sc_riso_press/NOTES.md (2026-11-10)
import td

SLUG = 'sc_riso_press'
# Files are named only through the scene's paths module (local/modules/paths, installed by the
# scaffold): shaders and the driver with mod.paths.here(), fonts with mod.paths.font(), models
# with mod.paths.model_file() / model_texture(). With no assets folder the models are
# TouchDesigner's teapot (fitted to the library's size), the fonts its default face, and the
# model texture data/blank.png. see: experiments/sc_riso_press/NOTES.md "Assets" (2026-11-11)
BIGFONTS = ('archivo', 'chicago')      # faces the big word can be set in (TAKES 'bigfont')
SEP_W, SEP_H = 1024, 640       # the sheet is 1.6 x 1.0

# Everything a pack may replace: the words the press prints and the objects it prints them
# beside. build() reads it through LIB['scene_words'], so a pack's scenes/sc_riso_press/words.json
# can give its own value for any of these names.
#   BIG      the big word (one per section and seed)
#   PHRASES  the rows of small type
#   MODELS   per take (by name): rows of [model, size], size multiplying the take's own mscale.
#            Section and seed pick one row. The type take prints no object; its row is only loaded.
DEFAULTS = {
    "BIG": ['EVERY FRAME', 'HERE. NOW.', 'DO NOT TOUCH', 'PLATE 07', 'LOOP', 'FEEDBACK.', 'INK',
            'PICTURE OUT', 'HARNESS', 'SIGNAL', 'CATALOGUE 0047', 'OBJECT 12', 'NOISE', 'FOUND, NOT MADE'],
    "PHRASES": ['REAL TIME.', 'HERE. NOW.', 'SOUND IN. PICTURE OUT.', 'SIGNAL ......... FOUND',
                'ORIGIN: UNRECORDED. SO FAR.', 'AN OBJECT OF UNKNOWN USE. KEEP IT DRY.', 'EVERY FRAME IS MADE NOW.',
                'THE KICK MOVES THE INK.', 'LISTEN WITH YOUR EYES.', 'DO NOT TOUCH', 'PLATE OF THE DAY',
                'PLATE 07', 'EXHIBIT 12-B', 'HANDLE WITH BOTH HANDS. THEN LET GO.',
                'NOTHING ON THIS SHEET IS PRERENDERED', 'THIS SHEET IS MADE OF SOUND.', 'LOUD PRINTS. QUIET IS PAPER.',
                'EVERYTHING IS INK', 'CATALOGUE NO. 0047', 'SIXTY FRAMES A SECOND',
                'PAST. PRESENT. LATER. IN ORDER.', 'LOOP. LOOP. LOOPLOOP.'],
    "MODELS": {
        'proof': [['gramophone', 1.0], ['space_helmet', 0.85], ['astrolabe', 1.0], ['hourglass', 1.0]],
        'loupe': [['ribbon_loop', 1.0], ['pierced_stone', 1.0], ['rubber_duck', 1.0]],
        'delivery': [['marble_bust', 1.0], ['lander', 1.0], ['amphora', 1.0], ['traffic_cone', 1.0]],
        'duotone': [['crystal_cluster', 1.0], ['gramophone', 1.0], ['wire_cage', 1.0], ['broken_column', 0.85]],
        'type': [['amphora', 1.0]],
        'corner': [['traffic_cone', 1.0], ['rubber_duck', 1.0], ['balanced_solids', 1.0], ['amphora', 1.0]],
        'night': [['space_helmet', 0.8], ['hourglass', 1.0], ['astrolabe', 1.0], ['lander', 1.0]],
        'makeready': [['crystal_cluster', 1.0],['marble_bust', 1.0], ['pierced_stone', 1.0], ['balanced_solids', 1.0]],
        'gang': [['rubber_duck', 1.0], ['amphora', 1.0], ['astrolabe', 1.0], ['hourglass', 1.0], ['traffic_cone', 1.0]],
        'pile': [['broken_column', 1.0], ['gramophone', 1.0], ['ribbon_loop', 1.0], ['astrolabe', 1.0], ['space_helmet', 1.0]],
        'conveyor': [['lander', 1.0], ['marble_bust', 1.0], ['hourglass', 1.0], ['crystal_cluster', 1.0], ['rubber_duck', 1.0]],
        'bond': [['marble_bust', 1.0], ['broken_column', 1.0], ['amphora', 1.0], ['astrolabe', 1.0], ['ribbon_loop', 1.0]],
        'xerox': [['wire_cage', 1.0], ['skeleton_key', 1.0], ['balanced_solids', 1.0], ['gramophone', 1.0], ['lander', 1.0]],
        'target': [['pierced_stone', 1.0], ['wire_cage', 1.0], ['crystal_cluster', 1.0], ['space_helmet', 1.0], ['traffic_cone', 1.0]],
    },
}

# Ink indices (press.frag pal()): 0 fluorescent pink, 1 teal, 2 yellow, 3 ident ink, 4 red,
# 5 blue, 6 green, 7 opaque white, 8 black, 9 fluorescent orange, 10 violet.
# Plate: src = which light (0 red, 1 green, 2 blue, 3 luma); mode 0 ink in the shade, 1 ink in
# the light, 2 no object (type and flood only), 3 plate off; screen 0 dots, 1 lines, 2 grain, 3 solid,
# 4 concentric rings, 5 guilloche waves, 6 cross-hatch. inkb = second ink of a split fountain (-1 none).
# A plate that does not name its ink takes it from the driver's INKSETS (section and seed pick the set).
PLATE = dict(src=0, mode=0, big=0.0, rows=0.0, flood=0.0, grad=0, ko=0, scale=1.0, off=(0.0, 0.0), prot=0.0,
             gamma=2.0, amt=1.0, wob=0.0, ink=0, inkb=-1, screen=0, ang=15.0, dens=1.0, fm=1.0)
ANGLES = (15.0, 75.0, 0.0, 45.0)
TAKE = dict(
    name='', zoom=1.22, rot=-4.0, rotjit=3.0, centre=(0.0, 0.0), jit=(0.05, 0.03), pan=(0.02, 0.015), snap=1.0,
    axis=1, gap=0.14, lanes=0, adv=4, lay=0.2, relatch=0.6, live=False,
    # persp tilts the bed away from the camera; pile drops sheets on a heap (spread angle, offset);
    # reprint = new plates wipe over the old impression (never blank paper); inst = sheet arrives printed;
    # negalt = every other sheet is a negative
    persp=0.0, pile=0, pilespread=(1.0, 0.7), reprint=0, inst=0, negalt=0, bigfont='archivo',
    margin=0.07, marks=1, freq=105.0, gain=1.0, rough=0.5, streak=0.35, skew=0.03, colourway=0.15,
    misreg=0.006, kick=1.0, flash=1.0,
    paper=(0.93, 0.89, 0.78), opaque=0, bed=(0.07, 0.10, 0.14),
    mscale=0.85, mpos=(0.0, 0.0), cam=(2.5, 22.0), az=0.0, azjit=1.0, spin=110.0, tilt=0.0,
    lightspin=1.0, tiles=(1, 1), sun=(0.5, 0.5, 0.4), sunjit=0.2, outline=1.0,
    # with an Input picture (COMP par Input): inbig scales the big word's weight (0 = leave the
    # picture clear), inscale replaces every plate's own artwork scale and offset (None = keep)
    inbig=1.0, inscale=None,
    words=None, describe=None, big=dict(size=300, alignx='left', aligny='top', y=0, yjit=120), rowsize=92, rowscroll=(0.0, 0.0),
    plates=[{}, {}, {}, {}],
)


def _take(**kw):
    t = dict(TAKE)
    t.update(kw)
    t['big'] = dict(TAKE['big'], **kw.get('big', {}))
    pls = []
    for i, p in enumerate(t['plates']):
        d = dict(PLATE, src=min(i, 2), ink=i, ang=ANGLES[i], swap=('ink' not in p))
        d.update(p)
        pls.append(d)
    t['plates'] = pls
    return t


# describe = the words a take shows when the COMP's Describe toggle is on (they explain the
# technique; see SCENE_BRIEF.md "Describe mode and Input"): big = options for the big word
# (fitted to the visible sheet unless bigfit=False), label = a Chicago caption printed by the
# key plate, slug = the margin line in place of the take's name (%04d = sheet count)
# ('|' = new line in a label; at = ('view', x, y) in screen heights from the view centre, or
# ('paper', x, y) in sheet heights from the sheet centre; intext = the caption to use instead
# while an Input picture stands in for the model), rows = sentences
# for the rows of type (rowlines = one short sentence per line, set where the view sees it),
# rot = view rotation override (makeready lies upside down otherwise), aligny = where the big
# word sits when the take's own place would collide with the caption or the model, bigamt = tone
# of the big word (1 = solid line art), mscale / mpos = model size and place while describing.
# Each take is a different picture from the same press. The cutter picks take % len(TAKES);
# Seed moves the view, the model, the phrase, the light rig and the sun inside a take.
TAKES = [
    # 0 proof: one sheet almost filling the frame, model right, yellow type cropped left
    _take(name='proof',
          describe=dict(big=['RISOGRAPH', 'SPOT COLOUR', 'OVERPRINT', 'HALFTONE'], bigmax=150, mscale=0.7, mpos=(0.2, -0.12),
                        label=dict(text='A 3D MODEL UNDER RED,|GREEN AND BLUE LIGHTS.|EACH LIGHT PRINTS AS|ONE PLATE OF INK.',
                                   intext='A PICTURE FROM ANOTHER|SCENE. ITS RED, GREEN|AND BLUE EACH PRINT AS|ONE PLATE OF INK.',
                                   size=26, at=('paper', -0.70, -0.38), alignx='left', aligny='bottom')),
          mpos=(0.2, 0.0),
          plates=[{}, {}, {'big': 1.0}, {}]),
    # 1 loupe: extreme close-up of the screens; giant rosettes, register fringes, no word
    _take(name='loupe',
          describe=dict(big=['DOTS'], bigfit=False,
                        label=dict(text='HALFTONE|DOTS', size=14, at=('view', 0.0, 0.0))),
          zoom=0.20, rot=18.0, rotjit=25.0, centre=(0.0, 0.0), jit=(0.13, 0.08), pan=(0.05, 0.04),
          big=dict(size=380, aligny='center', yjit=60),
          freq=85.0, marks=0, margin=0.0, adv=8, lay=1.0, kick=0.45, misreg=0.005, rough=0.7, snap=0.5, reprint=1,
          mscale=1.25, cam=(2.2, 14.0),
          plates=[{'big': 0.5, 'amt': 0.7, 'gamma': 2.6}, {'flood': 0.3, 'grad': 2, 'amt': 0.6, 'gamma': 2.6},
                  {'screen': 1, 'flood': 0.35, 'grad': 5, 'amt': 0.8}, {}]),
    # 2 delivery: far above the bed, lanes of small sheets running in opposite directions
    _take(name='delivery',
          describe=dict(big=['EDITION', '1 PER BEAT', 'COPIES'], aligny='top', bigmax=135, mscale=0.74, mpos=(0.0, -0.13)),
          zoom=3.3, rot=14.0, rotjit=10.0, axis=0, lanes=1, gap=0.16, adv=1, lay=0.09,
          freq=40.0, skew=0.09, colourway=0.55, misreg=0.02, margin=0.06, jit=(0.5, 0.3), pan=(0.2, 0.1),
          mscale=0.95, outline=1.0,
          bed=(0.09, 0.12, 0.16), big=dict(size=260, aligny='bottom'),
          plates=[{'flood': 0.3, 'grad': 1}, {'big': 0.55}, {}, {}]),
    # 3 duotone: two line screens crossing into moire, full bleed, pink stock, seen from above
    _take(name='duotone',
          describe=dict(big=[], label=dict(text='2 INKS, 2 LINE SCREENS|RED AT 32 DEG, BLUE AT -28|WHERE THEY CROSS: MOIRE',
                                               size=24, at=('view', 0.30, -0.30))),
          zoom=0.80, rot=0.0, rotjit=2.0, jit=(0.04, 0.05), margin=0.0, marks=0, freq=50.0,
          paper=(0.97, 0.84, 0.80), colourway=0.0, adv=4, lay=0.5, snap=0.4, reprint=1,
          mscale=0.82, cam=(2.4, 42.0), mpos=(-0.12, 0.0),
          outline=0.0,
          plates=[{'ink': 4, 'screen': 1, 'ang': 32.0, 'gamma': 0.9},
                  {'ink': 5, 'screen': 1, 'ang': -28.0, 'mode': 1, 'flood': 0.55, 'grad': 5, 'src': 2},
                  {'mode': 3}, {'mode': 3}]),
    # 4 type sheet: no model; rows of phrases on two plates sliding past each other, grain screens
    _take(name='type',
          describe=dict(big=['TWO PLATES', 'TYPE ONLY', 'OVERPRINT'], bigfit=False, rowsize=52, rowlines=True, rows=[
              'THIS SHEET HAS NO 3D MODEL.',
              'SAME WORDS ON TWO INK PLATES.',
              'ONE PRINTS SOLID, ONE AS GRAIN.',
              'THEY NEVER QUITE LINE UP.',
              'A KICK KNOCKS THE SOLID PLATE.',
              'A SNARE KNOCKS THE GRAIN PLATE.',
              'BOTH SPRING BACK INTO REGISTER.',
              'BASS THICKENS THE GRAIN.',
              'EACH BAR A ROLLER PRINTS AGAIN.',
              'THE DISC IS A PLATE OF BIG DOTS.',
              'THE STRIPES ARE ONE HUGE WORD.']),
          zoom=0.56, rot=-7.0, rotjit=5.0, jit=(0.2, 0.12), margin=0.0, marks=0, freq=120.0,
          adv=4, lay=0.5, rowscroll=(0.012, 0.0), colourway=0.2, sun=(0.6, 0.5, 0.36), sunjit=0.5, reprint=1,
          big=dict(size=420, aligny='center', yjit=200),
          plates=[{'mode': 2, 'rows': 1.0, 'wob': 0.012, 'ink': 0, 'inkb': 9},
                  {'mode': 2, 'rows': 0.72, 'screen': 2, 'off': (0.02, -0.03), 'wob': 0.02, 'ink': 1, 'inkb': 10},
                  {'mode': 2, 'flood': 0.95, 'grad': 3, 'fm': 0.42},
                  {'mode': 2, 'big': 0.5, 'screen': 1, 'fm': 0.5, 'ang': 90.0}]),
    # 5 poster corner: big field of paper, a sun of coarse dots, a tiny model, the marks up close
    _take(name='corner',
          describe=dict(big=[], label=dict(text='REGISTER CROSSES AND COLOUR BAR:|EACH INK PLATE PRINTS ITS OWN.|A DRUM HIT SPLITS THEM APART.',
                                               size=24, at=('paper', -0.68, 0.17), alignx='left', aligny='top')),
          zoom=0.80, rot=3.0, centre=(-0.40, -0.12), jit=(0.04, 0.04), margin=0.09, freq=46.0,
          mscale=0.34, mpos=(-0.3, -0.22), cam=(2.6, 12.0),
          sun=(0.34, 0.5, 0.40), sunjit=0.1, colourway=0.1, kick=1.4,
          plates=[{'ink': 4, 'flood': 1.0, 'grad': 3}, {}, {'flood': 0.5, 'grad': 1, 'fm': 1.6}, {}]),
    # 6 night stock: opaque white, pink and yellow on dark paper; ink where the light falls
    _take(name='night',
          describe=dict(big=['OPAQUE INK', 'DARK STOCK', 'WHITE INK'],
                        label=dict(text='OPAQUE WHITE, PINK AND YELLOW|PRINT WHERE THE LIGHT FALLS.',
                                   size=24, at=('paper', 0.70, 0.39), alignx='right', aligny='top')),
          inbig=0.0,
          zoom=1.05, rot=5.0, paper=(0.075, 0.10, 0.15), opaque=1, bed=(0.30, 0.27, 0.22),
          colourway=0.0, freq=88.0, mscale=0.9,
          cam=(2.3, 6.0), mpos=(-0.16, 0.0), outline=0.0, big=dict(size=150, alignx='right', aligny='bottom', y=60, yjit=40),
          plates=[{'ink': 7, 'mode': 1, 'gamma': 1.6, 'amt': 0.8}, {'ink': 0, 'mode': 1, 'gamma': 1.4, 'amt': 0.84},
                  {'ink': 2, 'mode': 1, 'screen': 1, 'gamma': 1.4, 'amt': 0.84}, {'ink': 7, 'mode': 2, 'big': 1.0}]),
    # 7 makeready: waste sheet; every plate carries the model at a different size and angle
    _take(name='makeready',
          describe=dict(big=['MAKEREADY', 'TEST SHEET', 'WASTE SHEET'], rot=-4.0, aligny='top', bigamt=1.0,
                        label=dict(text='EVERY PLATE HOLDS THE MODEL|AT ITS OWN SIZE AND ANGLE.',
                                   intext='EVERY PLATE HOLDS THE PICTURE|AT ITS OWN SIZE AND ANGLE.',
                                   size=26, at=('paper', -0.70, -0.33), alignx='left', aligny='bottom')),
          zoom=0.95, rot=176.0, rotjit=8.0, margin=0.05, paper=(0.80, 0.71, 0.56),
          colourway=0.12, freq=70.0, adv=4, lay=0.5,
          big=dict(size=220, aligny='bottom'), misreg=0.02,
          plates=[{'scale': 1.5, 'off': (-0.14, 0.04), 'prot': 14.0, 'gamma': 1.0, 'fm': 0.6},
                  {'scale': 0.8, 'off': (0.22, -0.10), 'screen': 1, 'big': 0.45, 'prot': -8.0, 'gamma': 1.0},
                  {'scale': 2.1, 'off': (0.04, 0.10), 'screen': 2, 'prot': 30.0, 'gamma': 1.6},
                  {'scale': 1.0, 'prot': -20.0, 'off': (-0.05, 0.0)}]),
    # 8 gang sheet: the artwork stepped and repeated twelve times, each tile in its own inks
    _take(name='gang',
          describe=dict(big=[], slug='STEP AND REPEAT 4 X 3  %04d'),
          zoom=1.03, rot=1.5, rotjit=2.0, tiles=(4, 3), freq=128.0, adv=2, lay=0.25, colourway=0.1,
          mscale=0.8, cam=(2.5, 26.0),
          plates=[{}, {}, {}, {}]),
    # 9 pile: every beat a printed sheet is slapped onto a heap at its own angle
    _take(name='pile',
          describe=dict(big=['STACK', 'EDITION', '1 PER BEAT'], aligny='top', bigmax=135, mscale=0.72, mpos=(0.0, -0.13)),
          zoom=1.85, rot=8.0, rotjit=20.0, pile=1, pilespread=(1.1, 0.8), inst=1, adv=1, skew=0.0,
          colourway=0.45, misreg=0.015, freq=58.0, jit=(0.2, 0.12), pan=(0.08, 0.05), bed=(0.17, 0.12, 0.09),
          mscale=0.9, big=dict(size=230, aligny='bottom'),
          plates=[{'flood': 0.35, 'grad': 5}, {}, {'big': 0.8}, {}]),
    # 10 conveyor: low angle down the bed, lanes of sheets stepping toward and away from the camera
    _take(name='conveyor',
          describe=dict(big=['PRESS RUN', 'EDITION', '1 PER BEAT'], aligny='top', bigmax=125, mscale=0.74, mpos=(0.0, -0.13)),
          zoom=1.55, rot=-10.0, rotjit=16.0, persp=0.9, centre=(0.0, 0.35), jit=(0.5, 0.2),
          pan=(0.15, 0.05), axis=1, lanes=1, gap=0.22, adv=1, lay=0.09, freq=44.0, skew=0.07, colourway=0.5,
          misreg=0.02, margin=0.06, bed=(0.05, 0.075, 0.11), snap=0.6,
          mscale=0.95,
          big=dict(size=280, aligny='center'), plates=[{'big': 0.6}, {}, {'flood': 0.4, 'grad': 1}, {}]),
    # 11 bond: security printing; guilloche wave lines engrave the model on green-grey stock
    _take(name='bond',
          describe=dict(big=['GUILLOCHE', 'WAVE LINES', 'ENGRAVED'], aligny='top', bigamt=0.84,
                        label=dict(text='LINE WIDTH CARRIES THE TONE|AS ON A BANKNOTE', size=24, at=('view', 0.0, -0.33))),
          inbig=0.0, inscale=1.0,
          zoom=0.66, rot=-2.0, rotjit=4.0, jit=(0.1, 0.08), margin=0.0, marks=0, reprint=1, freq=64.0,
          paper=(0.85, 0.90, 0.80), colourway=0.0, streak=0.2, lay=0.4, outline=0.0, snap=0.5,
          mscale=0.9, cam=(2.4, 10.0),
          sun=(0.5, 0.5, 0.75), sunjit=0.3, big=dict(size=250, aligny='bottom', yjit=220),
          plates=[{'ink': 6, 'screen': 5, 'ang': 8.0, 'scale': 1.5, 'gamma': 1.0, 'amt': 0.8, 'flood': 0.5, 'grad': 2},
                  {'ink': 3, 'screen': 5, 'ang': -11.0, 'mode': 2, 'big': 0.75, 'fm': 1.3},
                  {'ink': 0, 'screen': 4, 'mode': 2, 'flood': 0.26, 'fm': 0.8, 'dens': 0.6},
                  {'mode': 3}]),
    # 12 xerox: a 1-bit photocopy; black cross-hatch and Chicago type, every other copy a negative
    _take(name='xerox',
          describe=dict(big=['PHOTOCOPY', '1-BIT', 'NEGATIVE', 'CROSS-HATCH'], aligny='top',
                        label=dict(text='BLACK INK ONLY, CROSS-HATCHED|EVERY 2ND COPY IS A NEGATIVE', size=24, at=('view', 0.0, -0.33))),
          inbig=0.0, inscale=1.0,
          zoom=0.74, rot=1.0, rotjit=3.0, jit=(0.08, 0.06), margin=0.0, marks=0, reprint=1, negalt=1,
          adv=2, lay=0.2, freq=40.0, gain=1.3, flash=0.4, paper=(0.95, 0.95, 0.93), colourway=0.0, streak=1.0, rough=0.9,
          cam=(2.3, 18.0), outline=1.0,
          bigfont='chicago', big=dict(size=300, aligny='center', yjit=300),
          plates=[{'ink': 8, 'src': 3, 'screen': 6, 'ang': 45.0, 'scale': 1.7, 'gamma': 0.75, 'off': (0.08, 0.0)},
                  {'mode': 3}, {'mode': 3}, {'ink': 8, 'big': 1.0, 'screen': 2, 'scale': 1.7, 'off': (0.08, 0.0)}]),
    # 13 target: two concentric-ring screens with different centres; bullseye moire on yellow stock
    _take(name='target',
          describe=dict(big=[], label=dict(text='RING SCREENS: 2 INKS, 2 CENTRES|WHERE RINGS CROSS: BULLSEYE MOIRE',
                                               size=24, at=('view', 0.0, -0.33))),
          inscale=1.0,
          zoom=0.80, rot=5.0, rotjit=10.0, jit=(0.08, 0.05), margin=0.0, marks=0, reprint=1,
          freq=30.0, paper=(0.97, 0.90, 0.66), colourway=0.0, adv=4, lay=0.5, outline=0.0,
          cam=(2.4, 30.0),
          plates=[{'ink': 9, 'screen': 4, 'scale': 1.5, 'gamma': 0.8, 'amt': 0.82, 'flood': 0.35, 'grad': 1},
                  {'ink': 5, 'screen': 4, 'mode': 1, 'src': 2, 'scale': 1.5, 'flood': 0.4, 'grad': 5, 'fm': 1.15},
                  {'mode': 3}, {'mode': 3}]),
]


def _glsl(scene, name, frag, w, h, fmt, uniforms):
    dat = scene.create(td.textDAT, name + '_frag')
    dat.par.file.expr = "mod.paths.here('shaders/%s')" % frag
    dat.par.syncfile = True
    dat.par.loadonstartpulse.pulse()
    top = scene.create(td.glslTOP, name)
    for extra in ('_pixel', '_compute'):
        d = scene.op(name + extra)
        if d:
            d.destroy()
    top.par.pixeldat = dat.name
    top.par.outputresolution = 'custom'
    top.par.resolutionw, top.par.resolutionh = w, h
    top.par.format = fmt
    top.seq.vec.numBlocks = len(uniforms)
    for i, uname in enumerate(uniforms):
        getattr(top.par, 'vec%dname' % i).val = uname
    return top, dat


def _text(scene, name, font, size, x, y):
    t = scene.create(td.textTOP, name)
    t.par.fontfile.expr = "mod.paths.font(%r)" % font
    t.par.bold.expr = "not me.par.fontfile.eval()"     # no font file: the default face, in bold (thin strokes print poorly)
    t.par.outputresolution = 'custom'
    t.par.resolutionw, t.par.resolutionh = SEP_W, SEP_H
    t.par.fontsizex = size
    t.par.fontcolorr = t.par.fontcolorg = t.par.fontcolorb = 1
    t.par.bgalpha = 1
    t.par.format = 'mono8fixed'
    t.nodeX, t.nodeY = x, y
    return t


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, x=500, y=-1100)
    W = LIB['scene_words'](scene, DEFAULTS)
    # each take gets its rows of [model, size] from the words; the driver reads tk['models']
    takes = [dict(tk, models=[[str(r[0]), float(r[1])] for r in W['MODELS'][tk['name']]]) for tk in TAKES]
    models = []
    for tk in takes:
        for row in tk['models']:
            if row[0] not in models:
                models.append(row[0])
    scene.store('TAKES', takes)
    scene.store('WORDS', {'BIG': list(W['BIG']), 'PHRASES': list(W['PHRASES'])})
    scene.store('driver_error', '')
    out1 = scene.op('out1')

    # ---- the artwork: one library model at a time, lit by three pure-colour lights ----
    target = scene.create(td.nullCOMP, 'target')
    target.nodeX, target.nodeY = -400, -460
    # the stand-in for a missing library model is TouchDesigner's teapot, which is neither
    # centred nor one unit long: measure it once so each model's `fit` can bring it to the
    # library's convention. (A File In SOP: computeBounds on a File In POP read zero here.)
    probe = scene.create(td.fileinSOP, 'teapot_probe')
    probe.par.file.expr = "mod.paths.samples() + '/Geo/UtahTeapot.obj'"
    probe.cook(force=True)
    longest = max(probe.size.x, probe.size.y, probe.size.z) or 1.0
    fit_s = 1.0 / longest
    fit_t = [-c * fit_s for c in (probe.center.x, probe.center.y, probe.center.z)]
    probe.destroy()
    for i, slug in enumerate(models):
        g = LIB['import_model'](scene, 'm_' + slug, slug)
        have = "mod.paths.have('models/%s/model.obj')" % slug
        fit = g.create(td.transformPOP, 'fit')      # identity for a library model
        fit.inputConnectors[0].connect(g.op('mesh'))
        fit.par.scale.expr = "1 if %s else %r" % (have, round(fit_s, 6))
        for ax, v in zip('xyz', fit_t):
            getattr(fit.par, 't' + ax).expr = "0 if %s else %r" % (have, round(v, 6))
        g.op('mesh').render = g.op('mesh').display = False
        fit.render = fit.display = True
        # no library, no texture: a flat grey so the Movie File In has a file and the plates still take light
        g.op('tex').par.file.expr = "mod.paths.model_texture(%r) or mod.paths.here('data/blank.png')" % slug
        g.nodeX, g.nodeY = -400 + 150 * (i % 7), -620 - 140 * (i // 7)
        g.par.render = (i == 0)
        # plates carry light, not hue: grey, lifted texture so a black prop still takes light
        mono = g.create(td.monochromeTOP, 'mono')
        mono.inputConnectors[0].connect(g.op('tex'))
        lift = g.create(td.levelTOP, 'lift')
        lift.inputConnectors[0].connect(mono)
        lift.par.outlow, lift.par.outhigh = 0.62, 1.0
        m = g.op('mat')
        m.par.basecolormap = lift.path
        m.par.metallic, m.par.roughness = 0.0, 0.55
        for n in ('mesh', 'fit', 'tex', 'mono', 'lift', 'mat'):
            g.op(n).cook(force=True)      # load now, not at the first cut to this model
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.lookat = target.path
    cam.par.fov = 40
    cam.par.tz = 2.5
    cam.nodeX, cam.nodeY = -250, -460
    for i, col in enumerate(((1, 0, 0), (0, 1, 0), (0, 0, 1))):
        l = scene.create(td.lightCOMP, 'light%d' % i)
        l.par.cr, l.par.cg, l.par.cb = col
        l.par.dimmer = 3.6
        l.par.lookat = target.path
        l.nodeX, l.nodeY = -100 + 150 * i, -460
    render = scene.create(td.renderTOP, 'render')
    render.par.camera = 'cam'
    render.par.geometry = 'm_*'
    render.par.lights = 'light*'
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1024, 600
    render.par.antialias = 'aa4'
    render.par.format = 'rgba8fixed'
    render.nodeX, render.nodeY = 0, -200

    # ---- type: big cropped word, slug line, rows of phrases ----
    t_big = _text(scene, 't_big', 'archivo', 300, -200, 200)
    t_big.par.alignx, t_big.par.aligny = 'left', 'top'
    t_slug = _text(scene, 't_slug', 'chicago', 24, -200, 80)
    t_slug.par.alignx, t_slug.par.aligny = 'right', 'bottom'
    t_slug.par.positionx = -52
    t_rows = _text(scene, 't_rows', 'barlow', 92, -200, -40)
    t_rows.par.alignx, t_rows.par.aligny = 'left', 'top'
    t_rows.par.wordwrap = True
    t_rows.par.linespacing = -14
    typepack, d = _glsl(scene, 'typepack', 'typepack.frag', SEP_W, SEP_H, 'rgba8fixed', ['uScroll'])
    typepack.inputConnectors[0].connect(t_big)
    typepack.inputConnectors[1].connect(t_slug)
    # the Describe caption (blank unless Describe is on) goes straight to the press, which prints
    # it in the key ink as clean line art: through the separation its thin strokes broke up
    t_cap = _text(scene, 't_cap', 'chicago', 24, -350, 80)
    t_cap.par.alignx, t_cap.par.aligny = 'center', 'center'
    t_cap.par.text = ''
    typepack.inputConnectors[2].connect(t_rows)
    typepack.nodeX, typepack.nodeY = 0, 80
    d.nodeX, d.nodeY = 0, 200

    # ---- separation, held per plate; and the previous sheet ----
    black = scene.create(td.constantTOP, 'black')
    black.par.colorr = black.par.colorg = black.par.colorb = 0
    black.par.alpha = 0
    black.par.outputresolution = 'custom'
    black.par.resolutionw, black.par.resolutionh = SEP_W, SEP_H
    black.par.format = 'rgba8fixed'
    black.nodeX, black.nodeY = 0, -360
    sep, d = _glsl(scene, 'sep', 'sep.frag', SEP_W, SEP_H, 'rgba8fixed',
                   ['uLatch', 'uImg', 'uSun', 'uAmt'] + ['uP%s%d' % (c, i) for c in 'abc' for i in range(4)] + ['uIn'])
    d.nodeX, d.nodeY = 250, 80
    fb_sep = scene.create(td.feedbackTOP, 'fb_sep')
    fb_sep.inputConnectors[0].connect(black)
    fb_sep.par.top = 'sep'
    fb_sep.nodeX, fb_sep.nodeY = 150, -360
    # Input: the picture a take separates is the three-light render, or (COMP par Input) another
    # TOP: its red, green and blue channels stand in for the three lights. The driver points
    # in_sel at the Input TOP and flips src_sw; blank Input = index 0 = the render, untouched.
    in_sel = scene.create(td.selectTOP, 'in_sel')
    in_sel.par.top = 'black'
    in_sel.nodeX, in_sel.nodeY = -150, -330
    in_prep, d = _glsl(scene, 'in_prep', 'in_prep.frag', 1024, 600, 'rgba8fixed', ['uPrep'])
    in_prep.inputConnectors[0].connect(in_sel)
    in_prep.par.vec0valuex, in_prep.par.vec0valuey = 0.16, 0.8
    in_prep.nodeX, in_prep.nodeY = 0, -330
    d.nodeX, d.nodeY = -150, -230
    src_sw = scene.create(td.switchTOP, 'src_sw')
    src_sw.inputConnectors[0].connect(render)
    src_sw.inputConnectors[1].connect(in_prep)
    src_sw.par.index = 0
    src_sw.nodeX, src_sw.nodeY = 130, -200
    sep.inputConnectors[0].connect(src_sw)
    sep.inputConnectors[1].connect(typepack)
    sep.inputConnectors[2].connect(fb_sep)
    sep.nodeX, sep.nodeY = 250, -60
    hold, d = _glsl(scene, 'hold', 'hold.frag', SEP_W, SEP_H, 'rgba8fixed', ['uLatch', 'uLaid'])
    d.nodeX, d.nodeY = 450, -480
    fb_hold = scene.create(td.feedbackTOP, 'fb_hold')
    fb_hold.inputConnectors[0].connect(black)
    fb_hold.par.top = 'hold'
    fb_hold.nodeX, fb_hold.nodeY = 300, -360
    hold.inputConnectors[0].connect(sep)
    hold.inputConnectors[1].connect(fb_hold)
    hold.nodeX, hold.nodeY = 450, -360

    # ---- the press ----
    press, d = _glsl(scene, 'press', 'press.frag', 1280, 720, 'rgba8fixed',
                     ['uView', 'uFeed', 'uLay', 'uRegA', 'uRegB', 'uPl0', 'uPl1', 'uPl2', 'uPl3',
                      'uTone', 'uFm', 'uPaper', 'uBed', 'uMisc', 'uFx', 'uCam', 'uMode', 'uInkB'])
    press.inputConnectors[0].connect(sep)
    press.inputConnectors[1].connect(hold)
    press.inputConnectors[2].connect(t_cap)
    press.nodeX, press.nodeY = 700, -60
    d.nodeX, d.nodeY = 700, 80
    out1.inputConnectors[0].connect(press)

    # ---- Describe words: measure every string once (width at font size 100) so the driver can
    # fit them to the sheet without asking a Text TOP each frame ----
    dw = {}
    # (measured in whatever face mod.paths.font returns, so the fit also holds for the default face)
    for fkey in BIGFONTS:
        t_big.par.fontfile.expr = "mod.paths.font(%r)" % fkey
        t_big.par.fontsizex = 100
        t_big.cook(force=True)
        for tk in TAKES:
            if tk['bigfont'] == fkey:
                for st in (tk['describe'] or {}).get('big', []):
                    dw[(fkey, st)] = float(t_big.evalTextSize(st)[0])
    # the driver picks the big word's face per take through this CHOP (its own, not ctl: ctl
    # cooks every frame and would re-rasterise the word every frame)
    fontsel = scene.create(td.constantCHOP, 'fontsel')
    fontsel.par.name0 = 'bigfont'
    fontsel.nodeX, fontsel.nodeY = -350, 200
    t_big.par.fontfile.expr = "mod.paths.font(%r[int(op('fontsel')['bigfont'])])" % (BIGFONTS,)
    t_big.par.fontsizex = 300
    # rows set one sentence per line: the widest line at font size 100, per take
    t_rows.par.fontsizex = 100
    t_rows.cook(force=True)
    for ti, tk in enumerate(TAKES):
        dd = tk['describe'] or {}
        if dd.get('rowlines'):
            dw[('rows', ti)] = max(float(t_rows.evalTextSize(st)[0]) for st in dd['rows'])
    t_rows.par.fontsizex = 92
    scene.store('DW', dw)

    # ---- state readout and the driver (replaces the scaffold's cook driver) ----
    ctl = scene.create(td.constantCHOP, 'ctl')
    names = ['take', 'sheet', 'slide', 'lay0', 'lay1', 'lay2', 'lay3', 'latches', 'gain', 'reg0', 'reg1', 'driver_ms']
    ctl.seq.const.numBlocks = len(names)
    for i, n in enumerate(names):
        getattr(ctl.par, 'const%dname' % i).val = n
    ctl.nodeX, ctl.nodeY = -400, -200
    drv = scene.op('cook_driver')
    drv.par.file.expr = "mod.paths.here('press_driver.py')"
    drv.par.syncfile = True
    drv.par.loadonstartpulse.pulse()
    return scene.path
