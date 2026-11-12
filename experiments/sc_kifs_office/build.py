# Builder for /project1/sc_kifs_office ("Ray-marched letter architecture, seven takes").
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md):
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/sc_kifs_office/build.py', encoding='utf-8').read(), g)
#     path = g['build']()
# Idempotent: destroys and rebuilds the whole scene.
import td

# No folder is named here: the repository is td.project.folder, and every file parameter is an expression on
# mod.paths (the module the scaffold installs at local/modules/paths). Fonts are keys of mod.paths.font;
# with no assets folder it returns an empty string and the Text TOPs draw the system face named in STANDIN.
SLUG = "sc_kifs_office"
ARCHIVO = "archivo"

# The scene's own words (2026-11-11). A pack may replace either list with its scenes/sc_kifs_office/words.json
# (build() reads them through LIB['scene_words']); the counts are fixed, because the shader reads 4 and 8 rows.
#   ROWS: the text wall, top to bottom, one Archivo Black Text TOP each, [text, is_red]. The shader's frieze
#         row numbers follow this order: row 0 is the word the frieze shows most, row 1 the red one.
#   PHRASES: the second atlas, eight lines in a condensed face, [text, is_red].
DEFAULTS = {
    "ROWS": [
        ["REAL TIME", False],
        ["DO NOT TOUCH", True],
        ["PLATE 07", False],
        ["EXHIBIT 12", False],
    ],
    "PHRASES": [
        ["LISTEN WITH YOUR EYES.", False],
        ["NOTHING IS PRERENDERED.", True],
        ["KICK MOVES THE CAMERA.", False],
        ["FOUND, NOT MADE.", False],
        ["EACH FRAME IS MADE NOW.", False],
        ["LOUD IS BRIGHT.", True],
        ["PAST. PRESENT. LATER.", False],
        ["SIGNAL AND NOISE", False],
    ],
}
NROWS, NPHR = 4, 8
TEX = 1024
BARLOW = "barlow"
PTEX = 1280

# One row per take. The cutter counts this scene's visits in the COMP's Take parameter; the shader gets
# row (take % len(TAKES)) through the uTakeA..D uniforms, so a cut only changes numbers: nothing loads.
# arch / cam / light / grade are the mode numbers listed at the top of shaders/kifs.frag.
TAKE_COLS = ["name", "arch", "cam", "light", "grade", "folda", "foldb", "atlas", "relief",
             "speed", "focal", "fog", "tscale", "iters", "shrink"]
TAKES = [
    # name       arch cam light grade folda foldb atlas relief speed focal fog    tscale iters shrink
    ("nave",      0,  0,  0,    0,    0.0,  0.0,  0,    1.0,   1.0,  0.72, 0.16,  1.0,   4, 0.0),
    ("block",     2,  2,  2,    2,    0.0,  0.0,  0,    1.6,   1.0,  1.15, 0.007, 0.5,   3, 0.22),
    ("shaft",     1,  1,  1,    1,    0.0,  0.0,  1,    2.0,   1.8,  0.55, 0.10,  0.5,   2, 0.0),
    ("macro",     3,  3,  2,    3,    0.0,  0.0,  1,    2.5,   1.0,  0.80, 0.25,  0.5,   2, 0.0),
    ("rotunda",   4,  4,  3,    4,    0.25, 0.15, 0,    1.5,   1.0,  0.60, 0.10,  1.0,   4, 0.0),
    ("cut",       5,  5,  4,    5,    0.0,  0.0,  1,    2.0,   1.0,  1.00, 0.60,  0.25,  4, 0.0),
    ("strafe",    0,  6,  0,    6,    0.0,  0.0,  1,    1.3,   2.2,  0.72, 0.16,  1.0,   4, 0.0),
]

# Describe mode (2026-11-11): the words each take shows when the COMP's Describe toggle is on, in TAKES order.
# Every line must be true of the scene as built. A take keeps the atlas shape it already uses: the wall takes
# (atlas 0) get 4 short rows in Archivo Black, the phrase takes (atlas 1) get 8 rows in Barlow Condensed.
# (text, is_red). Each take's sheet is built once here and picked by a Switch TOP, so the toggle loads nothing.
DESCRIBE = [
    # nave: the frieze shows rows 0-2 whole, mostly row 0; the lattice carries all four as fragments
    [("RAY MARCHING", False), ("NO POLYGONS", True), ("ONE SHADER", False), ("80 STEPS MAX", False)],
    # block: all four rows print as a list on the paper floor and emboss the block
    [("FRACTAL BLOCK", False), ("SOFT SHADOW", True), ("FOLDED 3 TIMES", False), ("RAY MARCHED", False)],
    # shaft: huge fragments on the shaft walls, 1-bit
    # (the frame only ever holds five or six letters, so each row is one short label repeated)
    [("1-BIT 1-BIT 1-BIT 1-BIT", False), ("DITHER DITHER DITHER", True), ("RAY MARCH RAY MARCH", False),
     ("BLACK WHITE BLACK WHITE", False), ("1-BIT 1-BIT 1-BIT 1-BIT", False), ("NO GREY NO GREY NO GREY", True),
     ("DITHER DITHER DITHER", False), ("SNARE = NEGATIVE", False)],
    # macro: a window about ten letters wide over raised type, so again short labels repeated
    [("RAISED TYPE  RAISED TYPE  RAISED TYPE", False), ("HEIGHT MAP  HEIGHT MAP  HEIGHT MAP", True),
     ("SIDE LIGHT  SIDE LIGHT  SIDE LIGHT", False), ("NO MESH  NO MESH  NO MESH  NO MESH", False),
     ("RAISED TYPE  RAISED TYPE  RAISED TYPE", False), ("RAY MARCH  RAY MARCH  RAY MARCH", True),
     ("RAKING SUN  RAKING SUN  RAKING SUN", False), ("MACRO  MACRO  MACRO  MACRO  MACRO", False)],
    # rotunda: a dome of small repeated words
    [("CARVED SPHERE", False), ("ONE ORB LIGHT", True), ("FOLDED 4 TIMES", False), ("RAY MARCHED", False)],
    # cut: the eight rows lie on the cut face as one paragraph, top to bottom
    [("THIS IS NOT A 3D MODEL.", False), ("ONE SHADER MEASURES THE", True), ("DISTANCE TO A FOLDED BOX", False),
     ("FOR EVERY PIXEL.", False), ("THIS IS A FLAT SLICE", False), ("THROUGH THAT FRACTAL.", True),
     ("EACH KICK DRUM PUSHES", False), ("THE SLICE DEEPER.", False)],
    # strafe: one whole line at a time on the frieze, picked at random
    # (kept short: the frame holds about twenty letters of the belt)
    [("ONE SHADER.", False), ("NO POLYGONS.", True), ("UP TO 80 STEPS.", False),
     ("NOTES BEND WALLS.", False), ("KICK FIRES TUBES.", False), ("BEAT SWAPS LIGHTS.", True),
     ("TEXT IS THE WALL.", False), ("EMERGENCY RED.", False)],
]
# Font size (pixels on the sheet) where a Describe sheet wants smaller type than the phrase sheet (128):
# the strafe frame holds about 2.5 units of a 4.3-unit belt stretch, so its lines are set smaller to fit whole.
DESCRIBE_SIZE = {3: 90, 6: 100}
# A caption drawn over the frame in Describe mode, for takes whose own lettering cannot be read whole.
# The shaft shows letters so large and so dithered that no word survives, so it gets a 1-bit caption panel.
CHICAGO = "chicago"
# With no font file a Text TOP draws its `font` parameter (a system face by name; ignored while a file is set).
# The lettering is relief, so the stand-in must be heavy: Impact ships with Windows and macOS. Where it is
# missing too, TouchDesigner draws its own default face. The caption keeps the default face (None).
STANDIN = {"archivo": "Impact", "barlow": "Impact", "chicago": None}
DESCRIBE_LABEL = {
    # (Chicago at this size draws V like U and X like H, so the caption avoids both letters where it can)
    2: ["1-BIT RAY MARCH", "EACH DOT IS BLACK OR WHITE.", "4 BY 4 ORDERED DITHER, DOTS DOUBLED.",
        "THE SNARE SWAPS BLACK AND WHITE."],
}

# Input (2026-11-11): the COMP's Input parameter names a TOP (another scene's out1). When it resolves to a TOP
# outside this scene, that picture replaces the text sheets as the thing the building is embossed and painted
# with (shader uniform uIn.x = 1). Blank, missing or one of this scene's own TOPs = the scene's own text.
INPUT_OK = ("(lambda p: bool(p) and op(p) is not None and op(p).isTOP "
            "and not op(p).path.startswith(parent().path + '/'))(parent().par.Input.eval().strip())")


def _font(t, key):
    """Font file as an expression; when the assets folder has no such font, the stand-in system face."""
    t.par.fontfile.expr = "mod.paths.font(%r)" % key
    if STANDIN[key] and STANDIN[key] in t.par.font.menuNames:
        t.par.font = STANDIN[key]


def _text_row(scene, i, txt, red, name="row", font=ARCHIVO, w=TEX, h=TEX // NROWS, size=110, fit="nofit",
              maxfrac=None):
    t = scene.create(td.textTOP, "%s%d" % (name, i))
    t.par.text = txt
    _font(t, font)
    t.par.fontautosize = fit
    t.par.fontsizexunit = "pixels"                     # the default unit (points) renders a quarter of this size
    t.par.fontsizex = size
    t.par.wordwrap = False
    t.par.alignx = "center"
    t.par.aligny = "center"
    t.par.outputresolution = "custom"
    t.par.resolutionw, t.par.resolutionh = w, h
    t.par.fontcolorr, t.par.fontcolorg, t.par.fontcolorb = (1, 0, 0) if red else (1, 1, 1)
    t.par.bgalpha = 0
    t.nodeX, t.nodeY = (-300 if name == "row" else -520), 420 - 110 * i
    if maxfrac:                                        # keep a margin, so repeats of the sheet do not run together
        wd = t.evalTextSize(txt)[0]
        if wd > maxfrac * w:
            t.par.fontsizex = size * maxfrac * w / wd
    return t


def _wall(scene, name, pattern, res, y):
    comp = scene.create(td.layoutTOP, name + "_comp")    # stack the rows, top to bottom
    comp.par.tops = pattern
    comp.par.align = "verttb"
    comp.par.fit = "fill"                                # the default (fitbest) squeezes each row to a square cell
    comp.par.bgcolorr, comp.par.bgcolorg, comp.par.bgcolorb, comp.par.bgcolora = 0, 0, 0, 1
    comp.par.outputresolution = "custom"
    comp.par.resolutionw, comp.par.resolutionh = res, res
    comp.nodeX, comp.nodeY = 100, y
    wall = scene.create(td.blurTOP, name)
    wall.par.size = 5
    wall.par.extend = "repeat"
    wall.par.filtertype = "mipmap"
    wall.inputConnectors[0].connect(comp)
    wall.nodeX, wall.nodeY = 280, y
    return wall


def build():
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, 1000, -700)

    W = LIB["scene_words"](scene, DEFAULTS)
    assert len(W["ROWS"]) == NROWS and len(W["PHRASES"]) == NPHR, "the shader reads 4 wall rows and 8 phrases"

    # --- the text walls: height in red, "red ink" where green is missing ---
    for i, (txt, red) in enumerate(W["ROWS"]):
        _text_row(scene, i, txt, red)
    wall = _wall(scene, "wall", "row[0-9]", TEX, 180)
    for i, (txt, red) in enumerate(W["PHRASES"]):
        _text_row(scene, i, txt, red, name="phr", font=BARLOW, w=PTEX, h=PTEX // NPHR, size=128, fit="fitiffat")
    wall2 = _wall(scene, "phrases", "phr[0-9]", PTEX, 320)

    # --- Describe mode: one more sheet per take, same shape as the atlas that take uses ---
    wall_sw = scene.create(td.switchTOP, "wall_sw")
    phr_sw = scene.create(td.switchTOP, "phr_sw")
    wall_sw.inputConnectors[0].connect(wall)
    phr_sw.inputConnectors[0].connect(wall2)
    slot = []                                            # per take: its index on the switch it feeds
    for ti, rows in enumerate(DESCRIBE):
        phr = TAKES[ti][TAKE_COLS.index("atlas")] == 1
        assert len(rows) == (NPHR if phr else NROWS), "describe rows must match the take's atlas"
        for i, (txt, red) in enumerate(rows):
            if phr:
                t = _text_row(scene, i, txt, red, name="d%dr" % ti, font=BARLOW, w=PTEX, h=PTEX // NPHR,
                              size=DESCRIBE_SIZE.get(ti, 128), maxfrac=0.95)
            else:
                t = _text_row(scene, i, txt, red, name="d%dr" % ti, maxfrac=0.86)
            t.nodeX, t.nodeY = -2200 + 220 * ti, 1500 - 110 * i
        dw = _wall(scene, "d%d" % ti, "d%dr[0-9]" % ti, PTEX if phr else TEX, 0)
        scene.op("d%d_comp" % ti).nodeX, scene.op("d%d_comp" % ti).nodeY = -2200 + 220 * ti, 560
        dw.nodeX, dw.nodeY = -2200 + 220 * ti, 450
        sw = phr_sw if phr else wall_sw
        slot.append((phr, len(sw.inputs)))
        dw.outputConnectors[0].connect(sw)               # appends an input
        dw.cook(force=True)                              # built now, so the first Describe cut loads nothing
    for sw, y in ((wall_sw, 180), (phr_sw, 320)):
        idx = tuple(n if phr == (sw is phr_sw) else 0 for phr, n in slot)
        sw.par.index.expr = "%s[int(op('shot')['take']) %% %d] if parent().par.Describe else 0" % (idx, len(TAKES))
        sw.par.filtertype = "mipmap"
        sw.nodeX, sw.nodeY = 400, y

    # --- Input: another scene's picture, or a black stand-in when Input is blank ---
    blank = scene.create(td.constantTOP, "in_blank")
    blank.par.colorr, blank.par.colorg, blank.par.colorb, blank.par.alpha = 0, 0, 0, 1
    blank.par.outputresolution = "custom"
    blank.par.resolutionw, blank.par.resolutionh = 16, 9
    insel = scene.create(td.selectTOP, "in_sel")
    insel.par.top.expr = "parent().par.Input.eval().strip() if %s else 'in_blank'" % INPUT_OK
    insel.par.filtertype = "mipmap"
    blank.nodeX, blank.nodeY = 100, 460
    insel.nodeX, insel.nodeY = 280, 460

    # --- the takes ---
    takes = scene.create(td.tableDAT, "takes")
    takes.clear()
    takes.appendRow(TAKE_COLS)
    for row in TAKES:
        takes.appendRow(list(row))
    takes.nodeX, takes.nodeY = -400, 460

    # --- control channels: held and smoothed pitches, and the kick's travelling ring ---
    sel = scene.create(td.selectCHOP, "sel_pitch")
    sel.par.chop = "hub"
    sel.par.channames = "bass_pitch pitch"
    gate = scene.create(td.logicCHOP, "pitch_gate")      # 1 while a note is sounding
    gate.inputConnectors[0].connect(sel)
    hold = scene.create(td.holdCHOP, "pitch_hold")       # keep the last note through silences
    hold.par.sample = "whileon"
    hold.inputConnectors[0].connect(sel)
    hold.inputConnectors[1].connect(gate)
    lag = scene.create(td.lagCHOP, "tune")               # glide between notes
    lag.par.lag1, lag.par.lag2 = 0.18, 0.18
    lag.inputConnectors[0].connect(hold)
    selk = scene.create(td.selectCHOP, "sel_kick")
    selk.par.chop = "hub"
    selk.par.channames = "hit_low"
    ring = scene.create(td.triggerCHOP, "ring")          # 1 at each kick, falling to 0 in 0.45 s
    ring.par.threshold = True                              # 'threshold' is the Specify Threshold toggle
    ring.par.threshup, ring.par.threshdown = 0.12, 0.06
    ring.par.peaklen = 0
    ring.par.dshape = "linear"
    ring.par.attack, ring.par.peak, ring.par.decay, ring.par.sustain, ring.par.release = 0, 1, 0.45, 0, 0
    ring.inputConnectors[0].connect(selk)
    for i, o in enumerate((sel, gate, hold, lag, selk, ring)):
        o.nodeX, o.nodeY = -100 + 160 * i, -200 if i < 4 else -320
    selk.nodeX, ring.nodeX = -100, 60

    # --- the shader ---
    frag = scene.create(td.textDAT, "kifs_frag")
    frag.par.file.expr = "mod.paths.here('shaders/kifs.frag')"
    frag.par.syncfile = True
    frag.par.loadonstartpulse.pulse()
    frag.nodeX, frag.nodeY = 280, 40
    glsl = scene.create(td.glslTOP, "kifs")
    glsl.par.pixeldat = frag.name
    glsl.par.outputresolution = "custom"
    glsl.par.resolutionw, glsl.par.resolutionh = 1280, 720
    glsl.par.format = "rgba16float"
    glsl.par.inputextenduv = "repeat"
    glsl.par.inputfiltertype = "mipmap" if "mipmap" in glsl.par.inputfiltertype.menuNames else "linear"
    glsl.inputConnectors[0].connect(wall_sw)
    glsl.inputConnectors[1].connect(phr_sw)
    glsl.inputConnectors[2].connect(insel)
    glsl.seq.vec.numBlocks = 9

    def T(col):
        return "float(op('takes')[int(op('shot')['take']) %% %d + 1, '%s'])" % (len(TAKES), col)

    uniforms = [
        ("uCam", ["op('hub')['evolve']", "op('hub')['beat_pos']", "op('hub')['section']", "op('hub')['energy']"]),
        ("uFold", [
            "0.16 * math.sin(op('tune')['bass_pitch'] * math.pi / 6)",
            "0.11 * math.sin(op('tune')['pitch'] * math.pi / 6)",
            "op('hub')['bar_pulse']",
            "op('hub')['pulse']",
        ]),
        ("uHit", ["1 - op('ring')[0]", "op('ring')[0]", "op('hub')['hit_mid']", "op('hub')['hit_high']"]),
        ("uShot", ["op('shot')['seed']", "op('shot')['age']", "op('shot')['take']",
                   "max(0, 1 - op('shot')['age'] / 0.5)"]),
        ("uTakeA", [T("arch"), T("cam"), T("light"), T("grade")]),
        ("uTakeB", [T("folda"), T("foldb"), T("atlas"), T("relief")]),
        ("uTakeC", [T("speed"), T("focal"), T("fog"), T("tscale")]),
        ("uTakeD", [T("iters"), T("shrink"), "0", "0"]),
        ("uIn", ["1 if %s else 0" % INPUT_OK, "int(parent().par.Describe)", "0", "0"]),
    ]
    for i, (name, exprs) in enumerate(uniforms):
        getattr(glsl.par, "vec%dname" % i).val = name
        for axis, e in zip("xyzw", exprs):
            getattr(glsl.par, "vec%dvalue%s" % (i, axis)).expr = e
    glsl.nodeX, glsl.nodeY = 500, 100

    # --- Describe captions: a panel laid over the frame for the takes named in DESCRIBE_LABEL ---
    post = scene.create(td.switchTOP, "post_sw")         # index 0 = the shader untouched
    post.inputConnectors[0].connect(glsl)
    lab_idx = [0] * len(TAKES)
    for n, (ti, txt) in enumerate(sorted(DESCRIBE_LABEL.items())):
        lab = scene.create(td.textTOP, "label%d" % ti)
        lab.par.text = chr(10).join(txt)
        _font(lab, CHICAGO)
        lab.par.fontautosize = "nofit"
        lab.par.fontsizexunit = "pixels"
        lab.par.fontsizex = 24                             # Chicago's 12 px bitmap, doubled like the dither
        lab.par.wordwrap = False
        lab.par.alignx, lab.par.aligny = "center", "center"
        lab.par.outputresolution = "custom"
        lab.par.resolutionw, lab.par.resolutionh = 600, 148
        lab.par.fontcolorr, lab.par.fontcolorg, lab.par.fontcolorb = 1, 1, 1
        lab.par.bgcolorr, lab.par.bgcolorg, lab.par.bgcolorb, lab.par.bgalpha = 0, 0, 0, 1
        wd = max(lab.evalTextSize(line)[0] for line in txt)   # a wider stand-in face must still fit the panel
        if wd > 580:
            lab.par.fontsizex = 24 * 580 / wd
        over = scene.create(td.overTOP, "label%d_over" % ti)
        over.inputConnectors[0].connect(lab)
        over.inputConnectors[1].connect(glsl)
        over.par.size = "input2"
        over.par.prefit = "nativeres"
        over.par.justifyh, over.par.justifyv = "left", "bottom"
        over.par.tunit = "pixels"
        over.par.tx, over.par.ty = 40, 40
        over.outputConnectors[0].connect(post)             # appends an input
        lab_idx[ti] = n + 1
        lab.nodeX, lab.nodeY = 500, -60 - 240 * n
        over.nodeX, over.nodeY = 680, -60 - 240 * n
        over.cook(force=True)
    post.par.index.expr = "%s[int(op('shot')['take']) %% %d] if parent().par.Describe else 0" % (tuple(lab_idx), len(TAKES))
    post.nodeX, post.nodeY = 860, 100
    post.outputConnectors[0].connect(scene.op("out1").inputConnectors[0])
    return scene.path
