# Builder for /project1/sc_flow_mosh: optical-flow datamosh. Run inside TouchDesigner:
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open(project.folder + '/experiments/sc_flow_mosh/build.py', encoding='utf-8').read(), g); g['build']()
# Idempotent: destroys and rebuilds the whole scene. See NOTES.md.
#
# No folder is named here. The repository is td.project.folder; every parameter that names
# a file is an expression on the scaffold's module DAT (mod.paths.here / font / model_file /
# model_texture / asset), so the saved .tox holds the expression. Everything under <assets>
# is optional: see "Assets" in NOTES.md for what each missing thing falls back to.
import json
import random

import td

SLUG = "sc_flow_mosh"
CHICAGO = "mod.paths.font('chicago')"      # expressions, not paths; '' = TouchDesigner's default face
ARCHIVO = "mod.paths.font('archivo')"

# ---- the scene's content -----------------------------------------------------------
# Everything here is what an asset pack may replace: build() reads it through
# LIB['scene_words'], which takes any of these names from <pack>/scenes/sc_flow_mosh/words.json
# when the pack has that file. The values below suit the pack that ships with the repository.
#   PHRASES  16 short lines in the phrase face: the 1-bit wall's rows, the void's caption,
#            the floor-plan paint and the transplant card's header line. At most 38
#            characters: the shipped pack's phrase face is 32 px a character at 40 px and
#            a row is 1260 px (sync_words.py --check counts them)
#   CARDS    the transplant take's four big type cards (line breaks as written)
#   MARKS    the two wordmarks set in type when the pack has no lettering art
#            (art/stack_rgb.png, art/mark_rgb.png): stacked, then one line
#   HEROES   the four models shown one at a time: [model, colour of the stand-in teapot when
#            the model is not there, PBR MAT parameters set on top of the common ones]
#   WORLD    the props of the field: [model, scale, how many of the 90 distinct cells, the
#            mesh's height in units when the pack has no info.json for it (_world reads
#            size_units[1] of the pack's info.json when there is one), stand-in colour,
#            and optionally PBR MAT parameters as for a hero].
#            The counts must add up to 90 (build() checks the 162 instances that makes).
DEFAULTS = {
    "PHRASES": [
        "HERE. NOW. IN REAL TIME.", "SOUND IN. PICTURE OUT.", "SIGNAL ......... FOUND",
        "OBJECT 12-B: USE UNKNOWN.", "NOTHING YOU SEE HERE IS PRERENDERED.",
        "EVERY FRAME IS MADE NOW.", "LISTEN WITH YOUR EYES.", "THE KICK REDRAWS IT ALL.",
        "DO NOT TOUCH", "FOUND, NOT MADE.", "PLATE 07 OF 16",
        "SIXTY FRAMES A SECOND. NONE ARE KEPT.", "PAST. PRESENT. LATER. ON ONE SHELF.",
        "HANDLE WITH BOTH HANDS.", "LOUD IS BRIGHT.", "LOOP. LOOP. LOOPLOOP.",
    ],
    "CARDS": ["SOUND IN.\nPICTURE\nOUT.", "DO NOT\nTOUCH", "NO\nPLAYBACK", "ORIGIN\nUNKNOWN."],
    "MARKS": ["REAL\nTIME", "HARNESS"],
    "HEROES": [
        ["gramophone", [0.10, 0.17, 0.23], {}],
        # white shells and marble burn out under the key light: a darker base colour keeps their modelling
        ["space_helmet", [1.0, 1.0, 1.0], {"basecolorr": 0.5, "basecolorg": 0.5, "basecolorb": 0.5, "roughness": 0.3}],
        ["marble_bust", [0.49, 0.61, 0.69], {"basecolorr": 0.6, "basecolorg": 0.6, "basecolorb": 0.6}],
        ["hourglass", [0.86, 0.34, 0.24], {}],
    ],
    "WORLD": [
        ["balanced_solids", 1.7, 12, 1.0, [0.71, 0.58, 0.35]],
        ["amphora", 1.1, 12, 1.0, [0.84, 0.80, 0.71]],
        ["broken_column", 1.25, 8, 1.0, [0.78, 0.75, 0.65], {"basecolorr": 0.62, "basecolorg": 0.62, "basecolorb": 0.62}],
        ["traffic_cone", 0.9, 10, 1.0, [0.66, 0.20, 0.17]],
        ["astrolabe", 1.1, 10, 1.0, [0.72, 0.34, 0.47]],
        ["rubber_duck", 0.6, 8, 0.7802, [0.93, 0.89, 0.78]],
        ["skeleton_key", 1.2, 6, 1.0, [0.10, 0.17, 0.23]],
        ["lander", 1.0, 8, 1.0, [0.49, 0.61, 0.69]],
        ["wire_cage", 1.2, 6, 0.97, [0.86, 0.34, 0.24]],
        ["crystal_cluster", 1.2, 6, 0.6487, [0.60, 0.67, 0.33]],
        ["ribbon_loop", 1.1, 4, 1.0, [0.86, 0.71, 0.24]],
    ],
}
# TouchDesigner's bundled teapot (the stand-in for every library model) is not centred or
# unit-sized as the library's meshes are: x -0.9959..0.9681, y 0..0.9158, z +-0.6105
# (read from its points 2026-11-11, build 2025.33230). _stand_in scales it by TEAPOT_K
# so its longest side is 1 unit, like a library model.
TEAPOT_K = 0.5092
TEAPOT_CX = -0.0139
TEAPOT_H = 0.9158 * TEAPOT_K      # its height once scaled

# ---- the takes ---------------------------------------------------------------------
# One row per take; the cutter's Take parameter picks `take % len(TAKES)`. Everything a
# take needs stays loaded: a take is a row of numbers read by expressions (the `tk` CHOP).
#   smode      which picture src.frag draws (0 poster, 1 aisle, 2 transplant donor, 4 1-bit wall, 5 void, 6 floor plan)
#   world      0 hero model render, 1 prop field from the aisle camera, 2 prop field from above
#   gain       flow gain multiplier          block   macroblock size in px
#   streak     vertical sort floor (above 1 = dominant)   updir  share of sort columns that rise
#   reveal     how partial I-frames arrive (0 clusters, 1 rising columns, 2 scan from the top)
#   arrive     seconds the shot takes to print itself over what was on screen
#   fullhit    kick strength for a full I-frame        rotbeat  seconds of rot before any beat refreshes
#   maxrot     seconds before a forced I-frame         kickresid  1 = every kick stamps the donor's frame difference
#   transplant 1 = I-frames come from the card, motion from the donor
#   zoom       post zoom into the buffer     vectors  analyser overlay     mono  1-bit output
COLS = ["name", "smode", "world", "gain", "block", "streak", "updir", "reveal", "arrive",
        "fullhit", "rotbeat", "maxrot", "kickresid", "transplant", "zoom", "vectors", "mono"]
TAKES = [
    # name        smode world gain block streak updir reveal arrive fullhit rotbeat maxrot kres transp zoom vec mono
    ("poster",      0,   0,   1.0,   8,  0.0,  0.5,   0,   0.25,  0.62,  0.30,  4.0,  0,   0,    1.0, 0,  0),
    ("aisle",       1,   1,   1.3,  16,  0.0,  0.5,   0,   0.30,  0.80,  0.95,  3.0,  0,   0,    1.0, 0,  0),
    ("transplant",  2,   0,   1.5,   8,  0.0,  0.5,   0,   0.30,  0.90,  1.90,  3.6,  1,   1,    1.0, 0,  0),
    ("macro",       0,   0,   1.2,  16,  0.0,  0.5,   0,   0.20,  0.62,  0.45,  4.0,  0,   0,    5.0, 1,  0),
    ("onebit",      4,   0,   1.3,  16,  0.0,  0.5,   2,   0.35,  0.70,  0.60,  4.0,  0,   0,    1.0, 0,  1),
    ("void",        5,   0,   0.8,   8,  1.6,  1.0,   1,   0.30,  0.92,  1.90,  3.8,  0,   0,    1.0, 0,  0),
    ("plan",        6,   2,   1.3,   8,  0.0,  0.5,   0,   0.30,  0.62,  0.45,  4.0,  0,   0,    1.0, 0,  0),
]

# ---- Describe mode ------------------------------------------------------------------
# What each take shows when the COMP's Describe toggle is on: the same places the scene's
# own words go, but the words say what the viewer is looking at. Everything here is baked at
# build beside the scene's own version and chosen by Switch operators, so the toggle needs no
# rebuild. Mirrored into preset.json as "words". Phrase rows must fit 1260 px at 40 px
# Chicago (about 34 characters); _phrase_atlas raises if one does not.
#   stack / mark   the big Archivo word in the poster's two wordmark layouts
#   label          two crisp Chicago lines on an ink plate, drawn by post.frag outside the
#                  loop so they never rot: (title, sentence, "top" or "bottom")
#   label_input    the label shown instead while the COMP's Input names a picture
#   cards          the transplant take's four big type cards
#   phrases        the take's Chicago phrase rows (repeated to fill the 16-row atlas)
DESCRIBE = {
    "poster": {
        "stack": "DATA\nMOSH",
        "label_input": ("DATAMOSH OF ANOTHER SCENE",
                        "A KICK SHOWS THE INPUT CLEAN. ITS OWN MOTION DRAGS IT APART.", "bottom"),
        "mark": "DATAMOSH",
        "label": ("OPTICAL-FLOW DATAMOSH",
                  "A KICK REDRAWS THE POSTER. THEN ITS OWN MOTION DRAGS IT APART.", "top"),
    },
    "aisle": {
        "label_input": ("DATAMOSH OF ANOTHER SCENE, LEFT TO ROT",
                        "FEWER CLEAN FRAMES: 16 PX BLOCKS SLIDE ALONG THE INPUT'S MOTION.", "bottom"),
        "label": ("DATAMOSH, TRACKING SHOT",
                  "THE CAMERA SLIDES PAST 162 PROPS. NEAR ONES SMEAR FASTER.", "bottom"),
    },
    "transplant": {
        "label_input": ("DATAMOSH TRANSPLANT",
                        "THE INPUT IS THE CLEAN FRAME. A HIDDEN 3D MODEL MOVES IT.", "bottom"),
        "cards": ["THIS TYPE\nIS A\nKEYFRAME.", "BORROWED\nMOTION", "MOTION\nTRANSPLANT",
                  "A HIDDEN\nMODEL\nMOVES THIS."],
        "phrases": ["MOTION FROM A MODEL YOU NEVER SEE.", "EACH KICK STAMPS THE MODEL IN.",
                    "KEYFRAME: TYPE. MOTION: 3D MODEL.", "A HARD KICK REDRAWS THE CARD."],
        "label": ("DATAMOSH TRANSPLANT",
                  "THE TYPE IS THE CLEAN FRAME. A HIDDEN 3D MODEL MOVES IT.", "bottom"),
    },
    "macro": {   # the picture under the zoom is the poster, so it shares the poster's big word
        "label_input": ("DATAMOSH OF ANOTHER SCENE, ZOOMED IN",
                        "EACH SQUARE IS ONE BLOCK. ITS LINE IS THE MOTION IT COPIES.", "bottom"),
        "label": ("DATAMOSH, ZOOMED IN 5X",
                  "EACH SQUARE IS ONE BLOCK. ITS LINE IS THE MOTION IT COPIES.", "bottom"),
    },
    "onebit": {  # the rows are the explanation; the label is for the moments they are smeared past reading
        "label": ("1-BIT DATAMOSH",
                  "PURE BLACK AND WHITE. KICKS REDRAW IT. MOTION SMEARS IT.", "bottom"),
        "label_input": ("1-BIT DATAMOSH OF ANOTHER SCENE",
                        "THE INPUT IS DITHERED TO BLACK AND WHITE, THEN SMEARED.", "bottom"),
        "phrases": [
            "DATAMOSH IN PURE BLACK AND WHITE.", "OPTICAL FLOW MOVES OLD PIXELS.",
            "BETWEEN KICKS, OLD PIXELS ARE PUSHED.", "THE KICK DRUM REDRAWS THE FRAME.",
            "WEAK KICKS REDRAW ONLY THE TOP.", "SNARES MAKE THE BLOCKS BIGGER.",
            "LOUDER MUSIC SMEARS FASTER.", "BLOCKS OF 16 PIXELS MOVE AS ONE.",
            "MOTION IS MEASURED AT 320 X 180.", "ROWS SLIDE IN OPPOSITE DIRECTIONS.",
            "A DITHERED 3D MODEL CUTS THROUGH.", "OUTPUT IS THRESHOLDED TO 1 BIT.",
            "EVERY PIXEL IS BLACK OR WHITE.", "A NEW SHOT SCANS IN FROM THE TOP.",
            "VOCALS ADD VERTICAL STREAKS.", "ONE SHADER FED ITS OWN LAST FRAME.",
        ],
    },
    "void": {
        "label_input": ("DATAMOSH WITH A VERTICAL SORT",
                        "THE INPUT'S BRIGHT PIXELS COPY UPWARD. A HARD KICK CLEARS THEM.", "top"),
        "phrases": ["BRIGHT PIXELS COPY UPWARD.", "EACH LIGHT GROWS A RISING COLUMN.",
                    "A HARD KICK WIPES THE COLUMNS.", "DATAMOSH WITH A VERTICAL SORT."],
        "label": ("DATAMOSH WITH A VERTICAL SORT",
                  "BRIGHT PIXELS COPY UPWARD EACH FRAME. A HARD KICK CLEARS THEM.", "top"),
    },
    "plan": {
        "label_input": ("DATAMOSH OF ANOTHER SCENE",
                        "A KICK SHOWS THE INPUT CLEAN. ITS OWN MOTION DRAGS IT APART.", "bottom"),
        "phrases": ["TOP-DOWN DATAMOSH OF 162 PROPS.", "THE CAMERA TURNS WITH THE MUSIC.",
                    "CAMERA MOTION SMEARS THE FLOOR.", "SEEN FROM ABOVE: 162 PROPS."],
        "label": ("DATAMOSH, SEEN FROM ABOVE",
                  "162 PROPS ON TILES. THE CAMERA SWINGS IN TIME WITH THE MUSIC.", "bottom"),
    },
}

PITCH = 1.6          # grid spacing; the field repeats every 10 columns (16 units) so the camera can wrap
PERIOD = 10
PROP_INSTANCES = 162  # what that makes; build() checks it, because the Describe words say it

# Replaces the scaffold's cook driver: same gate, but first works out this frame's
# I-frame decision from the feed and the take, and writes it to the 'ctl' Constant CHOP.
DRIVER = '''ST = {'hl': None, 'sec': None, 'since': 0, 'hold': 0, 'n': 0, 'log': [],
      'now': None, 't_full': 0.0, 'bloom_t0': -99.0, 'bloom': 0, 'key': None, 'arr': 0, 'rk': -99.0}

def step(h, c):
    P = parent().par
    K = op('tk')
    now = absTime.seconds
    dt = 1.0 / 60 if ST['now'] is None else now - ST['now']
    fresh = ST['now'] is None or dt > 0.25      # first frame, or the scene was just cut to
    ST['now'] = now
    key = (int(P.Take.eval()), round(float(P.Seed.eval()), 5), round(float(P.Shotstart.eval()), 3))
    newshot = key != ST['key']
    ST['key'] = key
    sage = max(0.0, now - float(P.Shotstart.eval()))
    arrive = float(K['arrive'][0])
    fullhit = float(K['fullhit'][0]); rotbeat = float(K['rotbeat'][0]); maxrot = float(K['maxrot'][0])
    hl = int(h['hits_low'][0]); sec = int(h['section'][0])
    hm = int(h['hits_mid'][0]); beat = int(h['beat_i'][0])
    strength = 0.0; full = 0; first = 0
    if fresh or newshot:
        # a new shot: what is on screen (the last shot's remains) is overprinted by the new
        # picture over 'arrive' seconds, then the clean frame snaps in
        ST['bloom'] = 0
        if sage < arrive:
            ST['arr'] = 1; first = 1
        else:
            ST['arr'] = 0; full = 1
    elif ST['arr']:
        if sage >= arrive:
            ST['arr'] = 0; full = 1
        else:
            strength = max(0.04, (sage / arrive) ** 1.5)
    elif sec != ST['sec'] and P.Bloom.eval() > 0:
        # section change: no I-frame yet. The old picture is carried by the new
        # picture's motion (and its residual) until the next beat, then it snaps.
        ST['bloom'] = 1; ST['bloom_t0'] = now; first = 1
    elif sec != ST['sec']:
        full = 1
    elif ST['bloom']:
        el = now - ST['bloom_t0']
        if (beat != ST.get('beat') and el > 0.12) or el > P.Bloom.eval():
            ST['bloom'] = 0; full = 1
    else:
        if hl != ST['hl']:
            strength = min(1.0, max(0.15, float(h['hit_low'][0])))
            ST['log'] = (ST['log'] + [round(strength, 2)])[-48:]
            ST['rk'] = now
            if strength > fullhit:
                full = 1
        elif hm != ST.get('hm'):
            strength = 0.3            # snare: about a third of the picture comes back clean
        if beat != ST.get('beat') and now - ST['t_full'] > rotbeat:
            full = 1                  # no kick for a while: refresh on the beat instead
        if now - ST['t_full'] > maxrot:
            full = 1
    ST['hl'] = hl; ST['sec'] = sec; ST['hm'] = hm; ST['beat'] = beat
    if full:
        ST['hold'] = int(P.Hold.eval()); ST['since'] = 0; ST['t_full'] = now
    elif ST['hold'] > 0:
        ST['hold'] -= 1; full = 1; ST['t_full'] = now
    else:
        ST['since'] += 1
    ST['n'] += 1
    age = now - ST['t_full']
    # the rot starts slowly so the clean picture can be read, then lets go
    e = min(1.0, max(0.0, (age - 0.03) / max(0.01, P.Ease.eval())))
    if ST['arr']:
        e = 1.0                       # an arriving shot is carried by its motion from the first frame
    c.par.value0 = 1.0 if full else strength
    c.par.value1 = full
    c.par.value2 = ST['n'] % 1024
    c.par.value3 = (sec + int(key[1] * 97)) % 4
    c.par.value4 = (hl + int(key[1] * 211)) % 512
    c.par.value5 = ST['since']
    c.par.value6 = age
    c.par.value7 = 0.08 + 0.92 * e * e * (3 - 2 * e)
    c.par.value8 = min(4.0, max(0.5, dt * 60))      # frame time in 60ths: per-frame terms scale by it
    c.par.value9 = 0.5 if first else (1.0 if ST['bloom'] else 0.0)   # 0.5 = a cut frame: flow is muted
    # residual: strong for the first frames of a bloom (the new picture prints itself once),
    # then fading, or it piles up into rainbow noise within about 8 frames
    r = 0.0 if (first or not ST['bloom']) else max(0.0, 1.0 - (now - ST['bloom_t0']) / 0.2) ** 2
    if K['kickresid'][0] > 0 and not first:
        r = max(r, max(0.0, 1.0 - (now - ST['rk']) / 0.12))        # transplant: the kick stamps the donor
    c.par.value10 = r

def onFrameStart(frame):
    hub = op('/project1/sw_hub')
    me_on = parent().par.Preview.eval()
    if hub is not None:
        me_on = me_on or hub.par.Solo.eval() or hub.par.Scene.eval() == parent().name
    if me_on:
        h = op('hub')
        h.cook(force=True)
        step(h, op('ctl'))
        op('out1').cook(force=True)
        dbg = op('dbg/cache')
        if dbg is not None:
            dbg.cook(force=True)
    return
'''


def _glsl(scene, name, frag, w=1280, h=720, fmt="rgba16float", multi=False, dat=None):
    if dat is None:
        dat = scene.create(td.textDAT, name + "_frag")
        dat.par.file.expr = "mod.paths.here(%r)" % ("shaders/" + frag)
        dat.par.syncfile = True
    g = scene.create(td.glslmultiTOP if multi else td.glslTOP, name)   # the plain GLSL TOP takes 3 inputs
    g.par.pixeldat = dat.name
    g.par.outputresolution = "custom"
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    for suffix in ("_pixel", "_compute"):           # docked DATs the TOP brings with it
        d = scene.op(name + suffix)
        if d is not None:
            d.destroy()
    return g


def _uniforms(g, table):
    """table: list of (name, [expr or number] * up to 4)."""
    g.seq.vec.numBlocks = len(table)
    for i, (name, vals) in enumerate(table):
        g.par["vec%dname" % i] = name
        for comp, v in zip("xyzw", vals):
            p = g.par["vec%dvalue%s" % (i, comp)]
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _wire(src, dst, i):
    src.outputConnectors[0].connect(dst.inputConnectors[i])


DBG_EXEC = """# Freezes the debug cache a few frames after an event so the sequence can be captured
# at leisure. Arm with op('dbg').store('arm', 'bloom' | 'full'); re-arm to release.
def onFrameEnd(frame):
    d = parent(); c = op('../ctl'); ca = op('cache')
    arm = d.fetch('arm', None)
    if arm is None:
        return
    if arm == 'go':
        ca.par.active = True; d.store('arm', d.fetch('next', None)); d.store('count', -1); return
    cnt = d.fetch('count', -1)
    b = float(c['bloom'][0]); f = float(c['full'][0]); pb = d.fetch('pb', 0.0); pf = d.fetch('pf', 0.0)
    d.store('pb', b); d.store('pf', f)
    if cnt < 0:
        if (arm == 'bloom' and pb > 0 and b == 0) or (arm == 'full' and pf > 0 and f == 0 and pb == 0):
            d.store('count', d.fetch('after', 14))
    elif cnt == 0:
        ca.par.active = False; d.store('arm', None); d.store('count', -1)
    else:
        d.store('count', cnt - 1)
"""


def debug_sheet(scene, step=3):   # 12 tiles x 3 = 33 frames; shift the cs* indices for more
    """Optional: a contact sheet of recent frames (every 'step'th), oldest first,
    so the rot between two hits can be looked at in one still. Not part of the scene."""
    d = scene.create(td.baseCOMP, "dbg")
    d.nodeX, d.nodeY = 1200, -300
    sel = d.create(td.selectTOP, "sel")
    sel.par.top = "../out1"
    sm = d.create(td.resolutionTOP, "sm")
    sm.par.outputresolution = "custom"
    sm.par.resolutionw, sm.par.resolutionh = 640, 360
    _wire(sel, sm, 0)
    ca = d.create(td.cacheTOP, "cache")
    ca.par.cachesize = 64
    _wire(sm, ca, 0)
    lay = d.create(td.layoutTOP, "sheet")
    lay.par.align = "gridrows"
    lay.par.numcols = 4
    lay.par.numrows = 3
    lay.par.outputresolution = "custom"
    lay.par.resolutionw, lay.par.resolutionh = 1280, 540
    ex = d.create(td.executeDAT, "freeze")
    ex.text = DBG_EXEC
    ex.par.frameend = True
    for i in range(12):
        cs = d.create(td.cacheselectTOP, "cs%d" % i)
        cs.par.cachetop = "cache"
        cs.par.index = -(11 - i) * step
        cs.outputConnectors[0].connect(lay)
    return d


def _paths(scene):
    """The scene's own paths module: unlike the scaffold's helpers it sees the COMP's Assets
    parameter, so the builder decides exactly as the scene's expressions will."""
    return scene.op("local/modules/paths").module


def _archivo(t):
    """Archivo Black on a Text TOP; with no font file, TouchDesigner's default face in bold
    (Bold only takes effect with Legacy Font Selection on; both are off while the file exists)."""
    t.par.fontfile.expr = ARCHIVO
    t.par.legacyfontselection.expr = "not " + ARCHIVO
    t.par.bold.expr = "not " + ARCHIVO


def _stand_in(scene, geo, slug, colour, base=None):
    """Make a library model survive a missing library. Decided by expressions, not at build,
    so a saved .tox opened on a machine without the assets also gets it:
    - fit: a Transform POP after `mesh`. Identity while the model's file exists; otherwise it
      brings the bundled teapot to the library's convention (longest side 1 unit, centred on
      the origin), or with `base` (the library mesh's height) stands it where that mesh's
      base was, so instanced props still sit on the floor.
    - flat: a plain colour the material uses while there is no base colour image.
    """
    mesh, tex, mat = geo.op("mesh"), geo.op("tex"), geo.op("mat")
    have = "mod.paths.have('models/%s/model.obj')" % slug
    fit = geo.create(td.transformPOP, "fit")
    mesh.outputConnectors[0].connect(fit.inputConnectors[0])
    fit.par.scale.expr = "1 if %s else %r" % (have, TEAPOT_K)
    fit.par.tx.expr = "0 if %s else %r" % (have, round(-TEAPOT_CX * TEAPOT_K, 5))
    fit.par.ty.expr = "0 if %s else %r" % (have, round(-(TEAPOT_H if base is None else base) / 2, 5))
    mesh.render = False
    mesh.display = False
    fit.render = True
    fit.display = True
    # the image parameter is never empty (an empty Movie File In warns if anything cooks it)
    tex.par.file.expr = "mod.paths.model_texture(%r) or mod.paths.samples() + '/Map/Black.tiff'" % slug
    flat = geo.create(td.constantTOP, "flat")
    flat.par.colorr, flat.par.colorg, flat.par.colorb = colour
    flat.par.outputresolution = "custom"
    flat.par.resolutionw, flat.par.resolutionh = 16, 16
    mat.par.basecolormap.expr = "'tex' if mod.paths.model_texture(%r) else 'flat'" % slug
    fit.cook(force=True)                     # a hidden model otherwise loads on the frame it is first shown
    if _paths(scene).model_texture(slug):
        tex.cook(force=True)
    return fit


def _takes(scene):
    """The TAKES table as a Table DAT, and 'tk': the current take's row as channels."""
    tab = scene.create(td.tableDAT, "takes")
    tab.clear()
    tab.appendRow(COLS)
    for row in TAKES:
        tab.appendRow(list(row))
    tab.nodeX, tab.nodeY = -600, 330
    tk = scene.create(td.constantCHOP, "tk")
    tk.seq.const.numBlocks = len(COLS) - 1
    for i, name in enumerate(COLS[1:]):
        tk.par["const%dname" % i] = name
        tk.par["const%dvalue" % i].expr = (
            "float(op('takes')[int(op('shot')['take']) %% %d + 1, '%s'])" % (len(TAKES), name))
    tk.nodeX, tk.nodeY = -600, 200
    return tk


def _phrase_atlas(scene, name, phrases, x=-800, strict=False):
    """16 phrases, one per 80 px row of a 1280x1280 atlas, in Chicago, and their widths
    (as a fraction of the atlas width) in one channel of 16 samples. Returns (TOP, CHOP)."""
    phrases = [phrases[i % len(phrases)] for i in range(16)]
    spec = scene.create(td.tableDAT, name + "_spec")
    spec.clear()
    spec.appendRow(["x", "y", "text"])
    for i, s in enumerate(phrases):
        spec.appendRow([10, i * 80 + 22, s])
    phr = scene.create(td.textTOP, name)
    phr.par.fontfile.expr = CHICAGO
    phr.par.fontsizex = 40
    phr.par.alignx = "left"
    phr.par.aligny = "bottom"
    phr.par.outputresolution = "custom"
    phr.par.resolutionw, phr.par.resolutionh = 1280, 1280
    phr.par.bgalpha = 1
    phr.par.specdat = spec.name
    phr.cook(force=True)
    sizes = [float(phr.evalTextSize(s)[0]) for s in phrases]
    if max(sizes) > 1260.0 and not _paths(scene).font("chicago"):
        # the default face is wider than Chicago: set the whole atlas smaller so every row fits
        phr.par.fontsizex = 40 * 1250.0 / max(sizes)
        phr.cook(force=True)
        sizes = [float(phr.evalTextSize(s)[0]) for s in phrases]
    if strict and max(sizes) > 1260.0:
        raise ValueError("%s: phrase too wide for the atlas: %r" % (name, phrases[sizes.index(max(sizes))]))
    widths = [min(1260.0, w) / 1280.0 for w in sizes]
    pwc = scene.create(td.constantCHOP, name.replace("phr", "pw") + "_ch")
    pwc.seq.const.numBlocks = len(phrases)
    for i, w in enumerate(widths):
        pwc.par["const%dname" % i] = "w%d" % i
        pwc.par["const%dvalue" % i] = w
    pw = scene.create(td.shuffleCHOP, name.replace("phr", "pw"))   # 16 channels -> one channel of 16 samples
    pw.par.method = "swap"
    pwc.outputConnectors[0].connect(pw)
    for i, o in enumerate((spec, phr, pwc, pw)):
        o.nodeX, o.nodeY = x, 330 - i * 110
    return phr, pw


def _card_atlas(scene, name, cards, x=-1000, fit=None):
    """Four big Archivo Black phrase cards in a 2x2 atlas. fit=(w, h) in px sets each card's
    type as large as fits that box in its 640x360 cell (the Describe cards, which src.frag
    keeps wholly inside the frame)."""
    lay = scene.create(td.layoutTOP, name)
    lay.par.align = "gridrows"
    lay.par.numcols = 2
    lay.par.numrows = 2
    lay.par.outputresolution = "custom"
    lay.par.resolutionw, lay.par.resolutionh = 1280, 720
    for i, s in enumerate(cards):
        t = scene.create(td.textTOP, "%s%d" % (name.replace("cards", "card"), i))
        _archivo(t)
        t.par.text = s
        t.par.fontsizex = 100 if s.count("\n") == 2 else 128
        t.par.fontautosize = "fitiffat"
        t.par.linespacing = -18
        t.par.alignx = "center"
        t.par.aligny = "center"
        t.par.outputresolution = "custom"
        t.par.resolutionw, t.par.resolutionh = 640, 360
        t.par.bgalpha = 1
        if fit:
            t.par.fontautosize = "nofit"
            t.par.fontsizex = 100
            t.par.linespacing = -14
            t.cook(force=True)
            w, h = [float(v) for v in t.evalTextSize(s)[:2]]
            k = min(fit[0] / w, fit[1] / h)
            t.par.fontsizex = 100 * k
            t.par.linespacing = -14 * k
        t.nodeX, t.nodeY = x, -100 - i * 110
        t.outputConnectors[0].connect(lay)
    lay.nodeX, lay.nodeY = x + 200, -110
    return lay


def _text_atlases(scene, W):
    """phr: the 16 phrases in the phrase face. cards: four big Archivo Black phrase cards.
    pw: phrase widths. Each has Describe-mode twins (see DESCRIBE); the returned operators
    are Switches that pick the scene's own words, or the current take's describing words
    when the COMP's Describe toggle is on."""
    D = "parent().par.Describe"
    T = "int(op('shot')['take']) %% %d" % len(TAKES)
    phr, pw = _phrase_atlas(scene, "phr", W["PHRASES"])
    cards = _card_atlas(scene, "cards", W["CARDS"])
    phrsw = scene.create(td.switchTOP, "phr_sw")
    pwsw = scene.create(td.switchCHOP, "pw_sw")
    phr.outputConnectors[0].connect(phrsw)
    pw.outputConnectors[0].connect(pwsw)
    which = [0] * len(TAKES)                 # take -> input of the two switches
    k = 0
    for ti, row in enumerate(TAKES):
        words = DESCRIBE.get(row[0], {}).get("phrases")
        if not words:
            continue
        k += 1
        p, w = _phrase_atlas(scene, "phr_d%d" % ti, words, x=-1200 - k * 200, strict=True)
        p.outputConnectors[0].connect(phrsw)
        w.outputConnectors[0].connect(pwsw)
        which[ti] = k
    expr = "%r[%s] if %s else 0" % (tuple(which), T, D)
    phrsw.par.index.expr = expr
    pwsw.par.index.expr = expr
    cards_d = _card_atlas(scene, "cards_d", DESCRIBE["transplant"]["cards"], x=-1000 - 500, fit=(425, 205))
    cardsw = scene.create(td.switchTOP, "cards_sw")
    cards.outputConnectors[0].connect(cardsw)
    cards_d.outputConnectors[0].connect(cardsw)
    cardsw.par.index.expr = "1 if %s else 0" % D
    phrsw.nodeX, phrsw.nodeY = -600, 100
    pwsw.nodeX, pwsw.nodeY = -600, 0
    cardsw.nodeX, cardsw.nodeY = -600, -110
    for o in scene.findChildren(type=td.textTOP, maxDepth=1) + [cards, cards_d]:
        o.cook(force=True)                   # bake every version now: the toggle must not hitch
    return phrsw, cardsw, pwsw


def _describe_mask(scene, name, word, size, y, maxw=1024.0):
    """A Describe-mode stand-in for a wordmark mask: one big Archivo word (coverage in RGB)
    on the same 4:3 canvas as the wordmark art, spanning the same 80% of its width."""
    t = scene.create(td.textTOP, name)
    _archivo(t)
    t.par.text = word
    t.par.fontsizex = size
    t.par.linespacing = -int(size * 0.22)
    t.par.alignx = "center"
    t.par.aligny = "center"
    t.par.positiony = y
    t.par.outputresolution = "custom"
    t.par.resolutionw, t.par.resolutionh = 1280, 960
    t.par.bgalpha = 1
    t.cook(force=True)
    wid = float(t.evalTextSize(word)[0])
    if wid > maxw:
        t.par.fontsizex = size * maxw / wid
        t.par.linespacing = -int(size * maxw / wid * 0.22)
    t.cook(force=True)
    return t


def _label(scene):
    """Describe-mode corner label: two lines of 24 px Chicago per take in one atlas (32 px
    rows, set n at rows 2n and 2n+1), drawn at 1:1 by post.frag. Sets 0-6 are the takes'
    own labels; sets 7-13 are the labels used while an Input picture is given (the take's
    own words would then be untrue). Returns the atlas TOP and a table per set: on (0 none,
    1 bottom left, 2 top left) and the line widths in px."""
    spec = scene.create(td.tableDAT, "lab_spec")
    spec.clear()
    spec.appendRow(["x", "y", "text"])
    lab = scene.create(td.textTOP, "lab")
    lab.par.fontfile.expr = CHICAGO
    lab.par.fontsizex = 24
    lab.par.alignx = "left"
    lab.par.aligny = "bottom"
    lab.par.outputresolution = "custom"
    lab.par.resolutionw, lab.par.resolutionh = 1280, 64 * 2 * len(TAKES)
    lab.par.bgalpha = 1
    lab.par.specdat = spec.name
    wt = scene.create(td.tableDAT, "lab_w")
    wt.clear()
    wt.appendRow(["on", "w0", "w1"])
    lines = []
    for si in range(2 * len(TAKES)):
        row = TAKES[si % len(TAKES)]
        two = DESCRIBE.get(row[0], {}).get("label" if si < len(TAKES) else "label_input")
        lines.append(two)
        for j in range(2):
            if two:
                spec.appendRow([8, (si * 2 + j) * 32 + 7, two[j]])
    lab.cook(force=True)
    widest = max(float(lab.evalTextSize(s)[0]) for two in lines if two for s in two[:2])
    if widest > 1210.0:
        lab.par.fontsizex = 24 * 1200.0 / widest     # another pack's face can be wider than Chicago
        lab.cook(force=True)
    for two in lines:
        ws = [float(lab.evalTextSize(s)[0]) for s in two[:2]] if two else [0, 0]
        if max(ws) > 1210.0:
            raise ValueError("label too wide for the frame: %r" % (two,))
        wt.appendRow([(2 if two[2] == "top" else 1) if two else 0] + ws)
    for i, o in enumerate((spec, lab, wt)):
        o.nodeX, o.nodeY = 800 + i * 150, 300
    return lab, wt


def _world(scene, LIB, W):
    """The prop field: a grid of instanced library props standing on y = 0, repeating every
    PERIOD columns so a camera travelling along x can wrap without a seam."""
    rnd = random.Random(11)
    cells = [(c, r) for c in range(PERIOD) for r in range(-1, 8)]
    rnd.shuffle(cells)
    geos = []
    k = 0
    for row in W["WORLD"]:
        slug, scale, count, units, colour = row[:5]
        info = _paths(scene).asset("models/%s/info.json" % slug)
        if info:                # another pack's stand-in for this name has its own height
            units = float(json.load(open(info, encoding="utf-8")).get("size_units", [0, units])[1])
        height = units * scale
        geo = LIB["import_model"](scene, "w_" + slug, slug)
        _stand_in(scene, geo, slug, colour, base=units)
        tab = geo.create(td.tableDAT, "inst")
        tab.clear()
        tab.appendRow(["tx", "ty", "tz", "ry", "sc"])
        for c, r in cells[k:k + count]:
            ry = rnd.choice([0, 90, 180, 270]) + rnd.uniform(-25, 25)
            for cc in range(-9, 9):
                if cc % PERIOD == c:
                    tab.appendRow([(cc + 0.5) * PITCH, height / 2, (0.5 - r) * PITCH, ry, scale])
        k += count
        geo.par.instancing = True
        geo.par.instanceop = tab.path
        geo.par.instancetx, geo.par.instancety, geo.par.instancetz = "tx", "ty", "tz"
        geo.par.instancery = "ry"
        geo.par.instancesx, geo.par.instancesy, geo.par.instancesz = "sc", "sc", "sc"
        geo.op("mat").par.roughness = 0.5
        for name, value in (row[5] if len(row) > 5 else {}).items():
            geo.op("mat").par[name] = value
        geo.nodeX, geo.nodeY = -200 + len(geos) * 150, -900
        geos.append(geo)
    total = sum(g.op("inst").numRows - 1 for g in geos)
    if total != PROP_INSTANCES:              # the Describe words state this number
        raise ValueError("prop field has %d instances; DESCRIBE says %d" % (total, PROP_INSTANCES))
    S, H = "op('shot')", "op('hub')"
    wrap = "((%s['evolve'] * %%s * (1 if %s['seed'] < 0.5 else -1) + %s['seed'] * 160) %%%% 16) - 8" % (H, S, S)
    punch = "math.exp(-7 * %s['age'])" % S
    cam_a = scene.create(td.cameraCOMP, "cam_aisle")          # sideways tracking shot, low
    cam_a.par.tx.expr = wrap % "5.5"
    cam_a.par.ty.expr = "0.35 + 1.1 * ((%s['seed'] * 7.13) %% 1)" % S
    cam_a.par.tz.expr = "3.6 + 2.5 * " + punch                # the shot arrives on a fast push-in
    cam_a.par.rx = -4
    cam_a.par.ry.expr = "((int(%s['seed'] * 30) %% 3) - 1) * 20" % S
    cam_a.par.fov = 62
    cam_a.par.fog = "exp"
    cam_a.par.fogdensity = 0.06
    cam_a.par.fogcolorr, cam_a.par.fogcolorg, cam_a.par.fogcolorb = 0.705, 0.708, 0.554
    cam_b = scene.create(td.cameraCOMP, "cam_plan")           # straight down
    cam_b.par.tx.expr = wrap % "2.0"
    cam_b.par.ty.expr = "(9.5 + 5 * ((%s['seed'] * 3.31) %% 1)) * (1 - 0.06 * %s['pulse']) + 9 * %s" % (S, H, punch)
    cam_b.par.tz.expr = "-4.0 + 1.5 * math.sin(%s['evolve'] * 0.5)" % H
    cam_b.par.rx = -90
    cam_b.par.ry.expr = "(int(%s['seed'] * 40) %% 4) * 30 - 45 + 14 * math.sin(%s['beat_pos'] * math.pi / 4)" % (S, H)
    cam_b.par.fov = 50
    cam_a.nodeX, cam_a.nodeY = -200, -1050
    cam_b.nodeX, cam_b.nodeY = -50, -1050
    return geos, cam_a, cam_b


def build(debug=False):
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, 1750, -700)
    W = LIB["scene_words"](scene, DEFAULTS)     # the pack's own words and models, if it has them

    page = scene.customPages[0]
    page.appendFloat("Gain", label="Flow gain")[0].val = 1.3
    page.appendInt("Hold", label="Frames a full I-frame is held")[0].val = 2
    page.appendFloat("Ease", label="Seconds the rot takes to let go after an I-frame")[0].val = 0.13
    page.appendFloat("Bloom", label="Longest section-change bloom in seconds (0 = cut clean)")[0].val = 0.5
    page.appendFloat("Resid", label="Residual gain during a bloom")[0].val = 0.85

    tk = _takes(scene)
    phr, cards, pw = _text_atlases(scene, W)

    # ---- per-frame control state -------------------------------------------------
    ctl = scene.create(td.constantCHOP, "ctl")
    names = ["iframe", "full", "frame", "model", "seed", "since", "age", "ease", "dt60", "bloom", "resid"]
    ctl.seq.const.numBlocks = len(names)
    for i, n in enumerate(names):
        ctl.par["const%dname" % i] = n
    ctl.nodeX, ctl.nodeY = -400, -220
    scene.op("cook_driver").text = DRIVER

    # ---- 3D: four hero models, one shown at a time ---------------------------------
    geos = []
    for i, (slug, colour, look) in enumerate(W["HEROES"]):
        geo = LIB["import_model"](scene, "m_" + slug, slug)
        _stand_in(scene, geo, slug, colour)
        geo.par.render.expr = "int(op('ctl')['model']) == %d" % i
        geo.par.ry.expr = "op('hub')['beat_pos'] * 28 + 25 * math.sin(op('hub')['beat_pos'] * math.pi / 2) + 360 * op('shot')['seed']"
        geo.par.rx.expr = "14 * math.sin(op('hub')['beat_pos'] * math.pi / 4) + 8"
        geo.par.rz.expr = "8 * math.sin(op('hub')['beat_pos'] * math.pi / 8)"
        geo.par.scale.expr = "1 + 0.06 * op('hub')['pulse']"
        mat = geo.op("mat")
        mat.par.roughness = 0.45
        # a hot rim on every model: the silhouette has to survive being smeared
        mat.par.rimlight0enable = True
        mat.par.rimlight0colorr, mat.par.rimlight0colorg, mat.par.rimlight0colorb = 1.0, 0.82, 0.55
        mat.par.rimlight0strength = 1.4
        for name, value in look.items():     # this model's own look (metal needs the env map below)
            mat.par[name] = value
        geo.nodeX, geo.nodeY = -200 + i * 150, -400
        geos.append(geo)

    cam = scene.create(td.cameraCOMP, "cam")
    cam.par.tz = 3.1
    cam.par.fov = 28
    cam.nodeX, cam.nodeY = -200, -550

    def light(name, pos, colour, dim):
        l = scene.create(td.lightCOMP, name)
        l.par.tx, l.par.ty, l.par.tz = pos
        l.par.cr, l.par.cg, l.par.cb = colour
        l.par.dimmer = dim
        l.par.lookat = geos[0].path
        return l

    key = light("key", (-2.5, 3.0, 3.5), (1.0, 0.95, 0.85), 3.2)
    rim = light("rim", (3.0, 1.5, -2.5), (1.0, 0.45, 0.6), 2.2)
    fill = light("fill", (2.5, -1.5, 3.0), (0.35, 0.6, 0.8), 1.6)
    amb = scene.create(td.ambientlightCOMP, "amb")
    amb.par.dimmer = 0.45
    envmap = _glsl(scene, "envmap", "env.frag", 512, 256, "rgba16float")
    env = scene.create(td.environmentlightCOMP, "env")
    env.par.envlightmap = envmap.path
    env.par.dimmer = 0.9
    envmap.nodeX, envmap.nodeY = 600, -700
    lights = (key, rim, fill, amb, env)
    for i, l in enumerate(lights):
        l.nodeX, l.nodeY = 0 + i * 150, -550

    render = scene.create(td.renderTOP, "render")
    render.par.camera = cam.path
    render.par.geometry = " ".join(g.path for g in geos)
    render.par.lights = " ".join(l.path for l in lights)
    render.par.outputresolution = "custom"
    render.par.resolutionw, render.par.resolutionh = 720, 720
    render.par.antialias = "aa4"
    render.nodeX, render.nodeY = 0, -250

    # ---- 3D: the prop field (aisle and floor-plan takes) ----------------------------
    wgeos, cam_a, cam_b = _world(scene, LIB, W)
    wrender = scene.create(td.renderTOP, "wrender")
    wrender.par.camera.expr = "'cam_plan' if op('tk')['world'] > 1.5 else 'cam_aisle'"
    wrender.par.geometry = " ".join(g.path for g in wgeos)
    wrender.par.lights = " ".join(l.path for l in lights)
    wrender.par.outputresolution = "custom"
    wrender.par.resolutionw, wrender.par.resolutionh = 1280, 720
    wrender.par.antialias = "aa4"
    wrender.nodeX, wrender.nodeY = 0, -750
    r3d = scene.create(td.switchTOP, "r3d")          # only the render the take uses is cooked
    render.outputConnectors[0].connect(r3d)
    wrender.outputConnectors[0].connect(r3d)
    r3d.par.index.expr = "1 if op('tk')['world'] > 0.5 else 0"
    r3d.nodeX, r3d.nodeY = 150, -250

    # ---- wordmark masks (coverage in RGB), under the 1280 licence cap ---------------
    # With no wordmark art in <assets>, mask<i>_f stands in: the same word set in type.
    masks = []
    art = ["art/stack_rgb.png", "art/mark_rgb.png"]
    for i, f in enumerate(art):
        m = scene.create(td.moviefileinTOP, "mask%d" % i)
        # never empty (an empty Movie File In warns if anything cooks it); the Switch below skips it
        m.par.file.expr = "mod.paths.asset(%r) or mod.paths.samples() + '/Map/Black.tiff'" % f
        m.par.outputresolution = "custom"
        m.par.resolutionw, m.par.resolutionh = 1280, 960
        m.nodeX, m.nodeY = 0, -100 + i * 110
        masks.append(m)
    # Describe mode: the same canvases with a word that names the technique (takes 0 and 3)
    dmasks = [_describe_mask(scene, "mask0_d", DESCRIBE["poster"]["stack"], 330, 0, 800.0),
              _describe_mask(scene, "mask1_d", DESCRIBE["poster"]["mark"], 190, 0, 940.0)]
    fmasks = [_describe_mask(scene, "mask0_f", W["MARKS"][0], 330, 0, 1010.0),
              _describe_mask(scene, "mask1_f", W["MARKS"][1], 190, 0, 1010.0)]
    for i in range(2):
        sw = scene.create(td.switchTOP, "mask%d_sw" % i)
        masks[i].outputConnectors[0].connect(sw)
        dmasks[i].outputConnectors[0].connect(sw)
        fmasks[i].outputConnectors[0].connect(sw)
        sw.par.index.expr = "1 if parent().par.Describe else (0 if mod.paths.asset(%r) else 2)" % art[i]
        fmasks[i].nodeX, fmasks[i].nodeY = -140, -100 + i * 110
        sw.nodeX, sw.nodeY = 130, -100 + i * 110
        masks[i] = sw

    # ---- the clean source picture (and, for the transplant take, the card) -------------
    H, S, K = "op('hub')", "op('shot')", "op('tk')"
    T = "int(op('shot')['take']) %% %d" % len(TAKES)
    LS = "(%s + %d * int(op('inp_on')['on']))" % (T, len(TAKES))     # which label set
    C = "op('cam_plan' if op('tk')['world'] > 1.5 else 'cam_aisle')"

    def source(name, role, dat=None):
        g = _glsl(scene, name, "src.frag", fmt="rgba8fixed", multi=True, dat=dat)
        for o in (r3d, masks[0], masks[1], phr, cards):       # appended in order: inputs 0..4
            o.outputConnectors[0].connect(g)
        _uniforms(g, [
            ("uTime", ["%s['beat_pos']" % H, "%s['evolve']" % H, "%s['pulse']" % H, "%s['section']" % H]),
            ("uMod", ["%s['bar_pulse']" % H, "%s['energy']" % H, "%s['hit_low']" % H, role]),
            ("uShot", ["%s['smode']" % K, "%s['seed']" % S, "%s['age']" % S, "math.exp(-7 * %s['age'])" % S]),
            ("uCam", [C + ".par.tx", C + ".par.ty", C + ".par.tz", "math.radians(%s.par.rx)" % C]),
            ("uCam2", ["math.tan(math.radians(%s.par.fov) / 2)" % C, "math.radians(%s.par.ry)" % C,
                       "%s['hit_high']" % H, "1 if parent().par.Describe else 0"]),
        ])
        g.par.array0name = "uPW"
        g.par.array0type = "float"
        g.par.array0chop = pw.name
        g.par.array0arraytype = "uniformarray"
        return g

    src = source("src", 0)
    src.nodeX, src.nodeY = 250, 0
    cardsrc = source("cardsrc", 1, dat=scene.op("src_frag"))
    cardsrc.nodeX, cardsrc.nodeY = 250, 150

    # ---- Input: another scene's picture as the raw material -----------------------------
    # The COMP's Input parameter names a TOP. When it does, that picture takes the place of
    # this scene's clean source: it is what the kick shows clean and what its own motion then
    # drags apart. In the transplant take it replaces the type card instead (the motion still
    # comes from the hidden model). Blank, missing, not a TOP, or this scene's own output all
    # count as no input. inprep.frag fits it to 1280x720 and gives the 1-bit and void takes
    # a picture they can work on. Nothing upstream of msrc/isrc cooks unless it is selected.
    P = "parent().par.Input.eval().strip()"
    inon = scene.create(td.constantCHOP, "inp_on")
    inon.par.name0 = "on"
    inon.par.value0.expr = (
        "int((lambda o: o is not None and o.isTOP and not o.path.startswith(parent().path + '/'))"
        "(op(%s) if %s else None))" % (P, P))
    blank = scene.create(td.constantTOP, "inblank")
    blank.par.colorr, blank.par.colorg, blank.par.colorb = 0, 0, 0
    blank.par.outputresolution = "custom"
    blank.par.resolutionw, blank.par.resolutionh = 16, 16
    inp = scene.create(td.selectTOP, "inp")
    inp.par.top.expr = "%s if op('inp_on')['on'] else 'inblank'" % P
    inprep = _glsl(scene, "inprep", "inprep.frag", fmt="rgba8fixed")
    _wire(inp, inprep, 0)
    _uniforms(inprep, [("uI", ["%s['smode']" % K, "%s['seed']" % S, 0, 0])])
    msrc = scene.create(td.switchTOP, "msrc")        # the picture whose motion drives the mosh
    src.outputConnectors[0].connect(msrc)
    inprep.outputConnectors[0].connect(msrc)
    msrc.par.index.expr = "1 if op('inp_on')['on'] and %s['transplant'] < 0.5 else 0" % K
    isrc = scene.create(td.switchTOP, "isrc")        # the picture I-frames are made of
    src.outputConnectors[0].connect(isrc)
    cardsrc.outputConnectors[0].connect(isrc)
    inprep.outputConnectors[0].connect(isrc)
    isrc.par.index.expr = "2 if op('inp_on')['on'] else (1 if %s['transplant'] > 0.5 else 0)" % K
    isrc.nodeX, isrc.nodeY = 450, 150
    for i, o in enumerate((inon, blank, inp, inprep, msrc)):
        o.nodeX, o.nodeY = 250 + i * 130, 400
    src = msrc          # from here on "the source" is whichever picture is selected

    # ---- motion of the source (GLSL Lucas-Kanade at quarter size) ----------------------
    small = scene.create(td.resolutionTOP, "small")
    small.par.outputresolution = "custom"
    small.par.resolutionw, small.par.resolutionh = 320, 180
    _wire(src, small, 0)
    soft = scene.create(td.blurTOP, "soft")
    soft.par.size = 3
    soft.par.format = "rgba16float"
    _wire(small, soft, 0)
    prev = scene.create(td.feedbackTOP, "prev")     # last frame of 'soft'
    _wire(soft, prev, 0)
    prev.par.top = soft.name
    prev.par.format = "rgba16float"
    flow = _glsl(scene, "flow", "flow.frag", 320, 180, "rgba16float")
    _wire(soft, flow, 0)
    _wire(prev, flow, 1)
    _uniforms(flow, [("uF", [0.02, 0.0004, 0, 0])])
    flowsoft = scene.create(td.blurTOP, "flowsoft")
    flowsoft.par.size = 8
    _wire(flow, flowsoft, 0)
    for i, o in enumerate((small, soft, prev, flow, flowsoft)):
        o.nodeX, o.nodeY = 400 + i * 150, -200

    # ---- the mosh loop -------------------------------------------------------------------
    psrc = scene.create(td.feedbackTOP, "psrc")     # last frame of the motion source (for the residual)
    _wire(src, psrc, 0)
    psrc.par.top = src.name      # (msrc: a Feedback TOP targeting its own input = last frame)
    psrc.par.format = "rgba8fixed"
    psrc.nodeX, psrc.nodeY = 600, 220
    fb = scene.create(td.feedbackTOP, "fb")
    _wire(src, fb, 0)
    fb.par.format = "rgba8fixed"
    mosh = _glsl(scene, "mosh", "mosh.frag", fmt="rgba8fixed", multi=True)
    mosh.par.inputfiltertype = "nearest"
    for o in (fb, src, flowsoft, psrc, isrc):       # appended in order: inputs 0..4
        o.outputConnectors[0].connect(mosh)
    fb.par.top = mosh.name
    block = "min(96, %s['block'] * 2 ** min(3, int(%s['hit_mid'] * 4.5)))" % (K, H)
    _uniforms(mosh, [
        ("uA", [
            "parent().par.Gain * %s['gain'] * (0.5 + 1.8 * min(1.2, %s['energy'])) * (1 + %s['hit_low']) * op('ctl')['ease'] * (0 if op('ctl')['bloom'] == 0.5 else 1 - 0.3 * op('ctl')['bloom'])" % (K, H, H),
            block,
            "op('ctl')['iframe']",
            "op('ctl')['full']",
        ]),
        ("uB", [
            0,
            "max(%s['streak'] * (0.7 + 0.5 * min(1, %s['rms'])), min(1, max(0, %s['vocals'] - 0.25) * 1.5))" % (K, H, H),
            "op('ctl')['frame']",
            "(0.0003 + 0.0010 * min(1.2, %s['energy'])) * op('ctl')['dt60'] * op('ctl')['ease']" % H,
        ]),
        ("uC", ["%s['evolve']" % H, "op('ctl')['seed']", 0.0003,
                "parent().par.Resid * op('ctl')['resid']"]),
        ("uD", ["%s['reveal']" % K, "%s['updir']" % K, 0, 0]),
    ])
    fb.nodeX, fb.nodeY = 600, 100
    mosh.nodeX, mosh.nodeY = 800, 0

    post = _glsl(scene, "post", "post.frag", fmt="rgba8fixed")
    post.par.inputfiltertype = "nearest"
    _wire(mosh, post, 0)
    _wire(flowsoft, post, 1)
    _uniforms(post, [
        ("uP", ["min(1, max(0, %s['vocals'] - 0.15) * 1.3)" % H, "%s['hit_high']" % H, "%s['pulse']" % H,
                "%s['mono']" % K]),
        # the zoom arrives as a crash zoom over the first 0.4 s of the shot
        ("uZ", ["1 + (min(%s['zoom'], 2.2 if op('inp_on')['on'] else 99) - 1) * (lambda a: a * a * (3 - 2 * a))(min(1, %s['age'] / 0.4)) * (1 + 0.12 * %s['pulse'])" % (K, S, H),
                "0.5 + ((%s['seed'] * 5.3) %% 1 - 0.5) * 0.6 + 0.06 * math.sin(%s['evolve'] * 0.4)" % (S, H),
                "0.5 + ((%s['seed'] * 9.1) %% 1 - 0.5) * 0.4 + 0.05 * math.cos(%s['evolve'] * 0.31)" % (S, H),
                "%s['vectors']" % K]),
        ("uG", [block, 6.0, 0, 0]),
        # Describe mode: a two-line label (x: 0 none, 1 bottom left, 2 top left)
        ("uL", ["float(op('lab_w')[%s + 1, 'on']) if parent().par.Describe else 0" % LS,
                LS, "float(op('lab_w')[%s + 1, 'w0'])" % LS, "float(op('lab_w')[%s + 1, 'w1'])" % LS]),
    ])
    lab, lab_w = _label(scene)
    _wire(lab, post, 2)
    post.nodeX, post.nodeY = 1000, 0
    scene.op("out1").inputConnectors[0].connect(post)
    fb.par.resetpulse.pulse()
    psrc.par.resetpulse.pulse()
    prev.par.resetpulse.pulse()
    # cook everything a later take will need once now, so no take's first frame pays for a load
    for o in (phr, cards, wrender, render, cardsrc, inprep, lab):
        o.cook(force=True)
    scene.par.Preview = False       # leave it not cooking; turn Preview on to look at it
    if debug:
        debug_sheet(scene)
    return scene.path
