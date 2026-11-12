# Builds /project1/sc_fluid_ink: a stable-fluids simulation used as ink in water.
# Idempotent: run it again to rebuild.
#
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open('<this file>', encoding='utf-8').read(), g); g['build']()
#
# see: experiments/sc_fluid_ink/NOTES.md (2026-11-10) for why each stage exists.
import td

SLUG = "sc_fluid_ink"
# Every file parameter is an expression on mod.paths (the scaffold's local/modules/paths), so nothing
# saved names a folder. Assets are optional: see "Assets" in NOTES.md for what each falls back to.
CHICAGO = "mod.paths.font('chicago')"
FONT_BY_TAKE = "mod.paths.font(('archivo', 'chicago', 'barlow')[int(op('tk')['font'])])"
VEL_W, VEL_H = 320, 180      # velocity and pressure
DYE_W, DYE_H = 1280, 720     # dye: four times finer, so the ink stays sharp
JACOBI = 22

# Everything on screen that is content and not technique: the words, which models, which sheet.
# build() reads it through LIB['scene_words'], so an asset pack may replace any of these names with
# its own scenes/sc_fluid_ink/words.json (same names, same kinds of value).
DEFAULTS = {
    # the poster phrases (takes phrase, oil, macro, and the small stamp on the sheet take)
    "PHRASES": [
        "REAL TIME.",
        "DO NOT\nTOUCH",
        "EXHIBIT 12-B:\nUSE UNKNOWN.",
        "EVERY FRAME\nIS MADE NOW.",
        "PLATE 07",
        "SOUND IN.\nPICTURE OUT.",
        "NOTHING IS\nPRERENDERED.",
        "HERE. NOW.",
        "OBJECT\nNO. 0047",
        "EVERYTHING\nIS SIGNAL",
        "ORIGIN:\nUNRECORDED",
        "SIXTY FRAMES\nA SECOND.",
        "PAST. PRESENT.\nLATER.",
        "LISTEN WITH\nYOUR EYES.",
        "LOUD IS\nBRIGHT",
        "FOUND,\nNOT MADE",
        "FEEDBACK\n....... LOOP",
        "HANDLE THIS OBJECT\nWITH BOTH HANDS.",
        "MADE OF\nSOUND.",
    ],
    # the page take's small print (repeated to fill 26 lines)
    "PAGE_LINES": [
        "CATALOGUE OF UNEXPLAINED OBJECTS  PLATE 07  REV. 3  DO NOT TOUCH",
        "SIGNAL RECEIVED...  FEEDBACK LOOP ....... OPEN",
        "ORIGIN: UNRECORDED.  A PICTURE IS FORMING. IT HAS NO NAME YET.",
        "NOTHING HERE IS PRERENDERED.  EVERY FRAME IS MADE NOW.",
        "SOUND IN. PICTURE OUT.  LOUD IS BRIGHT.  HANDLE WITH BOTH HANDS",
        "OBJECT OF THE DAY: EXHIBIT 12-B.  CATALOGUE NO. 0047",
        "SIXTY FRAMES A SECOND, EVERY SECOND.",
        "THE KICK MOVES THE WATER.  THE PICTURE IS MADE OF SOUND AND INK.",
        "LISTEN WITH YOUR EYES.  EVERYTHING IS SIGNAL",
        "FOUND BY: ____________  DATE: ____________  PAST. PRESENT. LATER.",
        "AMPHORA  ASTROLABE  HOURGLASS  GRAMOPHONE  LANDER",
        "HERE. NOW. IN REAL TIME.",
    ],
    # the inkblot take's typed caption, after "PLATE <n>."
    "CAPTIONS": [
        "OBJECT OF UNKNOWN USE. DO NOT TOUCH.",
        "ORIGIN: UNRECORDED. ____________",
        "CATALOGUE OF UNEXPLAINED OBJECTS",
        "FOUND, NOT MADE. UNDATED.",
        "HANDLE WITH BOTH HANDS.",
        "EXHIBIT 12-B",
    ],
    # the sheet take's sheet when the pack has no picture for SHEET["model"]
    "SHEET_STANDIN": [
        "CATALOGUE OF UNEXPLAINED OBJECTS",
        "PLATE 07",
        "",
        "OBJECT  __________________________",
        "ORIGIN  __________________________",
        "PERIOD  __________________________",
        "USE  _____________________________",
        "DATE  ____________________________",
        "",
        "PLATE 07  REV. 3  DO NOT TOUCH",
    ],
    # the six silhouettes (night, sinking, survey): model name, tilt (rx, rz), extra turn (ry) and size
    "MODELS": [
        {"model": "gramophone", "rx": 10, "rz": 0, "ry": 0, "scale": 1.0},
        {"model": "amphora", "rx": 8, "rz": 0, "ry": 0, "scale": 0.92},
        {"model": "lander", "rx": 14, "rz": 0, "ry": 0, "scale": 0.9},
        {"model": "skeleton_key", "rx": 6, "rz": -24, "ry": 0, "scale": 1.1},
        {"model": "rubber_duck", "rx": 10, "rz": 0, "ry": 0, "scale": 0.8},
        {"model": "hourglass", "rx": 10, "rz": 0, "ry": 0, "scale": 0.85},
    ],
    # the sheet under the water in the sheet take: a flat-sheet model (its basecolor.png is used),
    # its width / height and its height in frame heights; the other keys replace that take's numbers
    # (where the stamp lands on this sheet, and the view)
    "SHEET": {"model": "star_chart", "aspect": 1.0, "size": 1.62,
              "scale": 0.36, "px": 0.42, "py": -0.1, "rot": -0.2, "zoom": 1.15, "vx": 0.1},
}

# Describe mode (the COMP's Describe toggle): every word on screen explains the technique.
# The page take prints these sentences instead of its small print.
PAGE_DESCRIBE = [
    "THIS PAGE IS INK IN A SIMULATED TANK OF WATER.",
    "THE WATER IS A GRID OF 320 X 180 ARROWS THAT SAY",
    "HOW FAST IT MOVES AT EACH POINT.",
    "EVERY FRAME THE ARROWS CARRY THEMSELVES ALONG,",
    "THEN A SOLVER RUNS 22 PASSES SO THAT WATER",
    "NEVER PILES UP ANYWHERE.",
    "THE INK IS A 1280 X 720 PICTURE THAT THE",
    "ARROWS DRAG ALONG.",
    "A KICK DRUM FIRES A STAR OF JETS AND A DROP OF INK.",
    "A SNARE SPINS TWO VORTICES IN OPPOSITE WAYS.",
    "A HI-HAT ADDS ONE FINE DROPLET.",
    "THE BASS SLOWLY STIRS THE WHOLE TANK.",
    "THE VOICE IS A NOZZLE: A HIGHER NOTE SITS HIGHER UP.",
    "EVERY BAR OF THE SONG PRINTS THIS PAGE AGAIN.",
    "THE PICTURE IS ONLY BLACK AND WHITE DOTS.",
    "NOTHING HERE IS VIDEO. NINE SHADERS RUN EVERY FRAME.",
]

# ... and the sheet take lies this sheet under the water instead of its own.
SHEET_DESCRIBE = [
    "INK IN WATER",
    "TECHNIQUE:  2D FLUID SIMULATION",
    "WATER:  320 X 180 VELOCITY GRID",
    "INK:  1280 X 720, THREE INKS",
    "SOLVER:  22 PASSES A FRAME",
    "",
    "KICK:  JETS + INK",
    "SNARE:  TWO VORTICES",
    "HI-HAT:  A DROPLET",
    "BASS:  STIRS THE TANK",
    "VOICE:  A NOZZLE",
]


def _rgb(hexs):
    hexs = hexs.lstrip("#")
    return [int(hexs[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


# paper, then the colour of a thick layer of each of the three inks
PALETTES = {
    "cream": ["#EDE3C8", "#11151B", "#C7281C", "#287E9B"],    # black and one red in cream water
    "ident": ["#EEE4CC", "#CC2914", "#EBB20D", "#0D5C8C"],    # ident red, yellow, blue: they mix subtractively
    "night": ["#0B1620", "#EEE4CC", "#DCB53D", "#E0608F"],    # luminous inks in dark water (style 1)
    "pond": ["#DCE4C6", "#2A3526", "#9A6B1F", "#A8322B"],     # pale green water, moss, brass and red inks
    "onebit": ["#FFFFFF", "#000000", "#000000", "#000000"],
    "putty": ["#CFC6AC", "#B32E61", "#192B3B", "#73941F"],    # pink, navy, green on putty steel
    "neon": ["#05070A", "#FF4A2E", "#27B6E0", "#F2D23C"],     # luminous (style 1) on black
    "sheet": ["#F1ECDD", "#A8190F", "#11151B", "#287E9B"],    # stamp red on the sheet
    "card": ["#F3EEE0", "#0E1014", "#B3261C", "#0E1014"],     # inkblot plate: black and one red on card
    "oil": ["#090B0F", "#FFFFFF", "#FFFFFF", "#FFFFFF"],      # style 3 takes its colour from thickness
    "survey": ["#E4E9D4", "#A8322B", "#B5701E", "#1F4E79"],   # draughtsman inks on green graph paper
}

# Every key is a channel of the 'tk' CHOP. A take overrides what it needs.
TAKE_DEFAULTS = dict(
    # what is laid down (src.frag): mode 0 phrase, 1 models, 2 page, 3 marbling bands, 4 nothing, 5 halftone
    src=0, shape=0, font=0, scale=1.0, px=0.0, py=0.0, rot=0.0, jit=0.2, rotj=0.12, copies=1,
    inka=0, inkb=1, restamp=1, hold=0.3,
    # the view (shade.frag)
    zoom=1.0, vx=0.0, vy=0.0, vrot=0.0, drift=0.015,
    style=0, paper=0, refr=0.012, bump=5.0, sharp=0.7, inv=0, glow=0.2, glowth=0.72,
    mirror=0, bands=6.0, caption=0,
    # the tank (vstep.frag)
    stir=0.6, buoy=0.0, vort=0.3, damp=0.25, diss=0.04, arr=1.0,
    kmode=0, kgain=1.0, sgain=1.0, ngain=1.0,
    # which ink the drums and the voice carry, and how much (dye.frag)
    kink=1, sink=0, nink=1, hink=0, kamt=0.5, samt=0.3, hamt=0.4,
    # Describe mode: 1 = this take carries a caption line (CAPS below); dfeed = share of the take's own
    # shape pressed in again every frame (the page take: its sentences keep re-forming so they can be read)
    dcap=1, dfeed=0.0,
    # Input (another scene's picture): inmode 0 ignore, 1 the picture is laid down as ink and fed in
    # again on every beat, 2 the picture is the paper under the water. infeed = share of the picture
    # pressed in per frame all the time, inbeat = the extra share on the beat (it decays through the beat,
    # so the water has the rest of the beat to carry the print off), incol = how far its hues split across
    # the three inks, ingain = ink amount, inlo..inhi = tone range, inrefr = refraction when it is the paper.
    inmode=1, infeed=0.012, inbeat=0.6, incol=0.7, ingain=1.0, inlo=0.06, inhi=0.6, inrefr=0.1,
)

# Keys of a TAKES row that are words, not numbers: "describe" = what the take's own text says in Describe
# mode (in the order used: phrase index counts up section by section), "caps" = caption lines.
WORD_KEYS = ("name", "pal", "describe", "caps")

# Each take is a different picture from the same tank. The cutter picks take % len(TAKES).
TAKES = [
    # 0 a poster phrase in black ink, off-centre in cream water; kicks are red stars
    dict(name="phrase", pal="cream", scale=0.62, px=-0.12, py=0.05, jit=0.4, inka=0, inkb=0, stir=0.8, diss=0.1,
         describe=["FLUID\nSIMULATION", "INK IN\nWATER", "KICKS FIRE\nJETS", "SNARES SPIN\nVORTICES",
                   "BASS STIRS\nTHE TANK"],
         caps=["THE WORDS ARE INK IN A FLUID SIMULATION MADE OF SHADERS.",
               "EACH KICK DRUM FIRES A RED STAR OF JETS INTO THE WATER."]),
    # 1 marbling: the whole frame in bands of three inks, combed by jets from the edges
    dict(name="marbling", pal="ident", src=3, shape=0, scale=1.0, jit=0.0, rotj=3.0, restamp=0, hold=0.12,
         kmode=1, kgain=1.6, sgain=1.5, kink=-1, sink=-1, nink=-1, hink=-1, diss=0.0, stir=0.8, bump=3.5, vort=0.1,
         describe=[],
         caps=["THIS IS MARBLING: THREE INKS IN ONE SIMULATED FLUID.",
               "EVERY KICK DRUM COMBS THE BANDS WITH A JET FROM THE EDGE.",
               "WHERE TWO INKS OVERLAP, THE COLOUR GOES DARKER."]),
    # 2 night: one model as luminous ink in dark water, jets from the frame edges
    dict(name="night", pal="night", style=1, src=1, shape=1, scale=0.8, px=0.3, jit=0.5, inka=0, inkb=0,
         kmode=1, kink=2, sink=1, nink=1, hink=0, kamt=0.8, samt=0.5, stir=0.9, bump=4.0,
         glow=0.55, glowth=0.55,
         describe=[],
         caps=["A 3D MODEL IS POURED INTO A FLUID SIMULATION AS GLOWING INK.",
               "KICKS ARE PINK JETS. SNARES ARE YELLOW VORTEX PAIRS."]),
    # 3 inkblot: the tank folded down the middle like a test plate, black blots and one red, a typed caption
    dict(name="inkblot", pal="card", src=6, mirror=1, caption=1, hold=0.35, inka=0, inkb=1, jit=0.0, rotj=0.0,
         kink=0, sink=1, nink=0, hink=0, kamt=0.9, samt=0.6, hamt=0.5, stir=0.5, drift=0.004, diss=0.1, bump=6.0,
         describe=[],
         caps=["THIS IS HALF A TANK OF SIMULATED INK, MIRRORED DOWN THE FOLD.",
               "DRUM HITS DROP INK ON THE LEFT. THE RIGHT IS A REFLECTION.",
               "KICKS ARE BLACK STARS. SNARES ARE RED VORTEX PAIRS."]),
    # 4 the bleeding page: small print in the typewriter face, 1-bit dither (white on black for half the seeds),
    #   printed again on every bar line
    dict(name="page", pal="onebit", style=2, src=2, shape=2, scale=1.06, rot=-0.05, jit=0.06, inka=0, inkb=0,
         kink=0, sink=0, nink=0, hink=0, kamt=0.7, stir=0.45, hold=0.45, inv=1, diss=0.3, sharp=1.0, glow=0.0,
         restamp=2, dcap=0, dfeed=0.07, describe=[], caps=[], infeed=0.004, inbeat=0.0),   # its words are PAGE_DESCRIBE
    # 5 oil: a condensed phrase bigger than the frame as an oil film on black water; colour is thickness
    dict(name="oil", pal="oil", style=3, font=2, scale=1.5, rot=0.12, jit=0.7, rotj=0.5, inka=0, inkb=2,
         sharp=0.0, bands=0.85, kmode=1, kgain=1.3, kink=4, sink=1, nink=2, hink=0, kamt=1.0, samt=0.7, hamt=0.8,
         stir=0.9, diss=0.03, glow=0.5, glowth=0.6, bump=6.0, refr=0.01,
         describe=["OIL FILM", "COLOUR IS\nTHICKNESS", "THIN FILM", "INK IN\nWATER"],
         caps=["THIS IS AN OIL FILM: ITS COLOUR COMES FROM HOW THICK IT IS.",
               "THE LETTERS CHANGE COLOUR AS THE FLUID STRETCHES THEM."]),
    # 6 side-on: a row of small models at the top sinks as plumes; kicks are drops from above
    dict(name="sinking", pal="pond", src=1, shape=1, scale=0.34, py=0.27, jit=0.25, copies=3, inka=0, inkb=1,
         buoy=1.0, stir=0.1, kmode=2, kink=2, sink=1, nink=0, hink=0, kamt=0.9, diss=0.02, hold=0.5, arr=0.0,
         describe=[],
         caps=["THIS IS A SIDE VIEW: THE INK IS HEAVIER THAN WATER AND SINKS.",
               "EACH KICK DRUM IS A RED DROP FALLING FROM THE TOP."]),
    # 7 survey: one model drawn as contour lines of ink thickness on graph paper, no fill, no gloss
    dict(name="survey", pal="survey", style=4, paper=2, src=1, shape=1, scale=1.15, px=-0.25, jit=0.5, inka=2, inkb=2,
         sharp=0.0, bands=7.0, kink=0, sink=1, nink=2, hink=1, kamt=0.9, samt=0.6, stir=0.7, diss=0.03,
         bump=0.0, refr=0.0, glow=0.0,
         describe=[],
         caps=["THE SAME FLUID IS DRAWN AS A MAP OF INK THICKNESS.",
               "EVERY LINE JOINS POINTS HOLDING THE SAME AMOUNT OF INK."]),
    # 8 macro: letters bigger than the frame, thick ident colours, strong surface
    dict(name="macro", pal="ident", scale=3.0, jit=1.2, rotj=0.6, zoom=1.35, drift=0.05, inka=0, inkb=2,
         kink=1, sink=2, nink=1, hink=0, kamt=0.9, samt=0.6, bump=8.0, refr=0.02, stir=1.0,
         describe=["FLUID", "INK", "FLOW", "VORTEX", "JET"],
         caps=["UP CLOSE, THE THREE INKS MIX LIKE COLOURED FILTERS.",
               "THE GLOSS IS LIGHT ON THE SLOPES OF THE THICK INK."]),
    # 9 the sheet: a small red stamp on a printed sheet seen through the water. Where the stamp lands
    #   and the view (scale, px, py, rot, zoom, vx) come from DEFAULTS["SHEET"]: they suit one sheet
    dict(name="sheet", pal="sheet", paper=1, font=2, jit=0.08,
         inka=0, inkb=0, refr=0.03, kink=1, sink=2, nink=2, hink=1, kamt=0.4, stir=0.4,
         inmode=2,
         describe=["SIMULATED\nINK", "FLUID\nSOLVER", "INK IN\nWATER"],
         caps=["THE SHEET LIES UNDER SIMULATED WATER, AND RIPPLES BEND IT."]),
]

_HUB = "op('hub')['%s']"


def _h(chan, salt):
    """Hash of a hub counter and the shot seed, 0..1, as a parameter expression."""
    return "((math.sin((op('hub')['%s'] + op('shot')['seed'] * 61.7) * %s) * 43758.5453) %% 1)" % (chan, salt)


def _frag(scene, name, x, y):
    dat = scene.create(td.textDAT, name + "_frag")
    rel = "shaders/" + name + ".frag"
    path = td.project.folder + "/experiments/" + SLUG + "/" + rel
    dat.text = open(path, encoding="utf-8").read()  # the file par loads a frame late
    dat.par.file.expr = "mod.paths.here(%r)" % rel
    dat.par.syncfile = True
    dat.nodeX, dat.nodeY = x, y - 130
    return dat


def _glsl(scene, name, x, y, w, h, fmt="rgba16float"):
    g = scene.create(td.glslTOP, name)
    for d in list(g.docked):
        if d.name in (name + "_pixel", name + "_compute"):
            d.destroy()
    g.par.pixeldat = _frag(scene, name, x, y).name
    g.par.outputresolution = "custom"
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    g.nodeX, g.nodeY = x, y
    return g


def _vecs(g, items):
    g.seq.vec.numBlocks = len(items)
    for i, (name, vals) in enumerate(items):
        getattr(g.par, "vec%dname" % i).val = name
        for comp, v in zip("xyzw", vals):
            p = getattr(g.par, "vec%dvalue%s" % (i, comp))
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _wire(dst, *srcs):
    for i, src in enumerate(srcs):
        src.outputConnectors[0].connect(dst.inputConnectors[i])


def _const(scene, name, chans, x, y):
    c = scene.create(td.constantCHOP, name)
    c.seq.const.numBlocks = len(chans)
    for i, (cn, expr) in enumerate(chans):
        getattr(c.par, "const%dname" % i).val = cn
        p = getattr(c.par, "const%dvalue" % i)
        if isinstance(expr, str):
            p.expr = expr
        else:
            p.val = expr
    c.nodeX, c.nodeY = x, y
    return c


def _feedback(scene, name, w, h, fmt, x, y):
    zero = scene.create(td.constantTOP, name + "_zero")
    zero.par.colorr = zero.par.colorg = zero.par.colorb = 0
    zero.par.alpha = 0
    zero.par.outputresolution = "custom"
    zero.par.resolutionw, zero.par.resolutionh = w, h
    zero.par.format = fmt
    zero.nodeX, zero.nodeY = x - 200, y
    fb = scene.create(td.feedbackTOP, name)
    fb.par.format = fmt
    zero.outputConnectors[0].connect(fb)
    fb.nodeX, fb.nodeY = x, y
    return fb


def _fit_unit(geo, i):
    """No model library: the mesh is TouchDesigner's teapot, which is not the library's size.
    Centre it and make its longest side 1 unit, as the library models are, and give each of the
    six a different tilt so they are not six identical pictures."""
    b = geo.op("mesh").computeBounds()
    size = max(b.size.x, b.size.y, b.size.z) or 1.0
    geo.par.scale = 1.0 / size
    geo.par.px, geo.par.py, geo.par.pz = b.center.x, b.center.y, b.center.z
    geo.par.tx, geo.par.ty, geo.par.tz = -b.center.x, -b.center.y, -b.center.z
    geo.par.rx = (12, 24, 4, 30, 16, 8)[i % 6]
    geo.par.rz = (0, 14, -18, 8, -10, 22)[i % 6]


def build():
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, x=250, y=-1100)
    # the installed module, not LIB's copy: only it sees the COMP's Assets parameter
    paths = LIB["scene_paths"](scene)
    W = LIB["scene_words"](scene, DEFAULTS)
    models = W["MODELS"]
    sheet = W["SHEET"]

    # ------------------------------------------------------------------ takes
    cols = list(TAKE_DEFAULTS.keys()) + ["p_r", "p_g", "p_b", "a_r", "a_g", "a_b", "b_r", "b_g", "b_b", "c_r", "c_g", "c_b"]
    takes = scene.create(td.tableDAT, "takes")
    takes.clear()
    takes.appendRow(["name"] + cols)
    for t in TAKES:
        row = dict(TAKE_DEFAULTS)
        row.update({k: v for k, v in t.items() if k not in WORD_KEYS})
        if t["name"] == "sheet":
            row.update({k: v for k, v in sheet.items() if k in TAKE_DEFAULTS})
        pal = PALETTES[t.get("pal", "cream")]
        for pre, hx in zip("pabc", pal):
            for comp, v in zip("rgb", _rgb(hx)):
                row[pre + "_" + comp] = round(v, 4)
        takes.appendRow([t["name"]] + [row[c] for c in cols])
    takes.nodeX, takes.nodeY = -400, 500

    tk = _const(scene, "tk", [
        (c, "float(op('takes')[int(op('shot')['take']) %% %d + 1, '%s'])" % (len(TAKES), c)) for c in cols
    ], -200, 500)

    # ------------------------------------------------------------------ control
    sec = scene.create(td.selectCHOP, "sec")
    sec.par.chop = "hub"
    sec.par.channames = "section"
    sec.nodeX, sec.nodeY = -200, 200
    secdelay = scene.create(td.delayCHOP, "secdelay")
    secdelay.par.delay = 0.25
    sec.outputConnectors[0].connect(secdelay)
    secdelay.nodeX, secdelay.nodeY = -50, 200

    # vocal pitch: hold the last sung note through rests, then glide (pitch is 0 most of the time)
    psel = scene.create(td.selectCHOP, "pitch")
    psel.par.chop = "hub"
    psel.par.channames = "pitch"
    psel.nodeX, psel.nodeY = -200, 60
    gate = scene.create(td.logicCHOP, "pitch_gate")
    # "pitch > 0" is not enough: the feed ramps between 0 and the note, and the hold then keeps
    # a ramp value (15 was seen). Only sung notes count.
    gate.par.convert = "bound"
    gate.par.boundmin, gate.par.boundmax = 36, 90
    psel.outputConnectors[0].connect(gate)
    gate.nodeX, gate.nodeY = -50, 0
    hold = scene.create(td.holdCHOP, "pitch_hold")
    hold.par.sample = "whileon"
    psel.outputConnectors[0].connect(hold.inputConnectors[0])
    gate.outputConnectors[0].connect(hold.inputConnectors[1])
    hold.nodeX, hold.nodeY = 100, 60
    tune = scene.create(td.lagCHOP, "tune")
    tune.par.lag1, tune.par.lag2 = 0.25, 0.25
    hold.outputConnectors[0].connect(tune)
    tune.nodeX, tune.nodeY = 250, 60

    seed = "op('shot')['seed']"
    desc = "parent().par.Describe"
    take_i = "int(op('shot')['take']) %% %d" % len(TAKES)
    inpath = "parent().par.Input.eval()"
    # the inkblot take shows only the left half of the tank (folded), so everything lands there
    half = "(0.5 if op('tk')['mirror'] > 0.5 else 1)"
    nx = "(1.7778 * %s * (0.5 + 0.36 * math.sin(op('hub')['beat_pos'] * 0.39 + %s * 6.283)))" % (half, seed)
    ny = "(0.15 + 0.7 * min(1, max(0, (op('tune')['pitch'] - 40) / 24)))"
    ctl = _const(scene, "ctl", [
        # a number that changes when the shot changes: the feedback loops compare it with the one
        # stored in their own alpha and start clean when it differs
        ("id", "(%s * 0.618 + op('shot')['take'] * 0.137 + parent().par.Shotstart * 0.0137) %% 1" % seed),
        # (a "was not cooking" test on cookAbsFrame was tried here and removed: one long frame, such
        # as a capture or another scene's rebuild, tripped it and wiped the tank mid-shot)
        ("boot", 0),
        # 1 while the shape is pressed into the water: at the cut, and for a moment at each new section
        ("stamp", "1 if (op('shot')['age'] < op('tk')['hold'] or (op('tk')['restamp'] > 0.5 and "
                  "abs(op('hub')['section'] - op('secdelay')['section']) > 0.5) or "
                  "(op('tk')['restamp'] > 1.5 and op('hub')['bar'] < 0.05)) else 0"),
        ("phrase", "int(%s * 97) + int(op('hub')['section'])" % seed),
        ("model", "(int(%s * 53) + int(op('hub')['section'])) %% %d" % (seed, len(models))),
        # where the shape lands: a new place for each seed and each section, so a restamp does not
        # print the next phrase on top of the wreck of the last one
        ("px", "op('tk')['px'] + (((%s + int(op('hub')['section']) * 0.37) * 7.13) %% 1 - 0.5) * op('tk')['jit']" % seed),
        ("py", "op('tk')['py'] + (((%s + int(op('hub')['section']) * 0.37) * 3.71) %% 1 - 0.5) * op('tk')['jit'] * 0.5" % seed),
        ("rot", "op('tk')['rot'] + (((%s + int(op('hub')['section']) * 0.37) * 5.37) %% 1 - 0.5) * op('tk')['rotj']" % seed),
        ("k1", _h("hits_low", 12.9898) + " * " + half), ("k2", _h("hits_low", 78.233)), ("k3", _h("hits_low", 39.346)),
        ("s1", _h("hits_mid", 45.164) + " * " + half), ("s2", _h("hits_mid", 94.673)), ("s3", _h("hits_mid", 27.719)),
        ("h1", _h("hits_high", 63.726) + " * " + half), ("h2", _h("hits_high", 10.873)), ("h3", _h("hits_high", 51.031)),
        ("nx", nx), ("ny", ny),
        ("ns", "min(1.2, max(0, op('hub')['vocals'] - 0.15) * 1.4) * op('tk')['ngain']"),
        ("na", "math.atan2(0.5 - %s, 0.8889 - %s) + 0.7 * math.sin(op('hub')['beat_pos'] * 0.8)" % (ny, nx)),
        # the view punches in at the cut and settles within half a second
        ("zoom", "op('tk')['zoom'] * (1 + 0.22 * math.exp(-op('shot')['age'] * 8))"),
        ("inv", "1 if (op('tk')['inv'] > 0.5 and (%s * 11.3) %% 1 > 0.5) else 0" % seed),
        ("vx", "op('tk')['vx'] + op('tk')['drift'] * math.sin(op('hub')['evolve'] * 0.11 + %s * 6.283)" % seed),
        ("vy", "op('tk')['vy'] + op('tk')['drift'] * math.cos(op('hub')['evolve'] * 0.09 + %s * 4.1)" % seed),
        ("vrot", "op('tk')['vrot'] + 0.02 * math.sin(op('hub')['evolve'] * 0.07 + %s * 9.0)" % seed),
        # Input: 1 when the COMP's Input names a TOP that exists (and is not this scene's own output)
        ("hasin", "1 if (%s and op(%s) is not None and op(%s).isTOP and op(%s).path != op('out1').path) else 0"
                  % (inpath, inpath, inpath, inpath)),
        # Describe: a caption line; light on the dark takes
        ("cap", "1 if (op('tk')['caption'] > 0.5 or (%s and op('tk')['dcap'] > 0.5)) else 0" % desc),
        # ... on a strip: 1 = dark type on a pale strip, 2 = pale type on a dark strip (the dark takes)
        ("capl", "(2 if op('tk')['style'] in (1, 3) else 1) if %s else 0" % desc),
    ], 100, 200)
    # (separate from ctl: a Constant CHOP expression that reads its own channels is a cook loop)
    inp_on = "(op('ctl')['hasin'] > 0.5 and op('tk')['inmode'] == %d)"
    ctl2 = _const(scene, "ctl2", [
        ("inink", "1 if %s else 0" % (inp_on % 1)),
        ("infeed", "(op('tk')['infeed'] + op('tk')['inbeat'] * math.exp(-12 * op('hub')['beat'])) if %s else "
                   "(op('tk')['dfeed'] if %s else 0)" % (inp_on % 1, desc)),
        ("refr", "op('tk')['inrefr'] if %s else op('tk')['refr']" % (inp_on % 2)),
        ("paper", "3 if %s else op('tk')['paper']" % (inp_on % 2)),
        # Describe, page take: each reprint replaces the bled page (a clean page to read on every bar line)
        ("clean", "1 if ((%s or %s) and op('tk')['restamp'] > 1.5) else 0" % (desc, inp_on % 1)),
        # the sheet under the water: its width / height and its height in frame heights. The pack's
        # sheet has its own; the typed stand-in and the Describe sheet are 1.29 : 1, laid 1.25 high
        ("shasp", "%r if (mod.paths.model_texture(%r) and not %s) else 1.29"
                  % (float(sheet.get("aspect", 1.29)), sheet["model"], desc)),
        ("shsize", "%r if (mod.paths.model_texture(%r) and not %s) else 1.25"
                   % (float(sheet.get("size", 1.25)), sheet["model"], desc)),
    ], 250, 200)

    # ------------------------------------------------------------------ shapes
    phrases = scene.create(td.tableDAT, "phrases")
    phrases.clear()
    for p in W["PHRASES"]:
        phrases.appendRow([p])
    phrases.nodeX, phrases.nodeY = -400, -300

    captions = scene.create(td.tableDAT, "captions")
    captions.clear()
    for p in W["CAPTIONS"]:
        captions.appendRow([p])
    captions.nodeX, captions.nodeY = -400, -450

    # Describe words: one row per take, padded by repeating so every row has the same length
    def _wordtable(name, key, y):
        n = max(1, max(len(t.get(key, [])) for t in TAKES))
        tab = scene.create(td.tableDAT, name)
        tab.clear()
        for t in TAKES:
            w = t.get(key, []) or [""]
            tab.appendRow([w[i % len(w)] for i in range(n)])
        tab.nodeX, tab.nodeY = -600, y
        return tab
    _wordtable("dwords", "describe", -300)
    _wordtable("dcaps", "caps", -450)

    text = scene.create(td.textTOP, "phrase")
    text.par.text.expr = ("op('dwords')[%s, int(op('ctl')['phrase']) %% op('dwords').numCols].val if %s else "
                          "op('phrases')[int(op('ctl')['phrase']) %% op('phrases').numRows, 0].val" % (take_i, desc))
    text.par.fontfile.expr = FONT_BY_TAKE
    text.par.bold.expr = "not %s" % FONT_BY_TAKE   # the default face is thin for ink: embolden it
    text.par.outputresolution = "custom"
    text.par.resolutionw, text.par.resolutionh = 1280, 720
    text.par.fontautosize = "fitiffat"
    text.par.fontsizex = 230
    text.par.alignx = "center"
    text.par.aligny = "center"
    text.par.linespacing = -10
    text.par.bgalpha = 1
    text.nodeX, text.nodeY = -200, -300

    page = scene.create(td.textTOP, "page")
    page.par.text = "\n".join((W["PAGE_LINES"] * 3)[:26])
    page.par.fontfile.expr = CHICAGO
    page.par.outputresolution = "custom"
    page.par.resolutionw, page.par.resolutionh = 1280, 720
    page.par.fontsizex = 24
    page.par.alignx = "left"
    page.par.aligny = "top"
    page.par.bgalpha = 1
    page.nodeX, page.nodeY = -200, -450
    # the same page with the Describe sentences: a second TOP, so the toggle is only a switch
    page_d = scene.create(td.textTOP, "page_d")
    page_d.par.text = "\n".join(PAGE_DESCRIBE)
    page_d.par.fontfile.expr = CHICAGO
    page_d.par.outputresolution = "custom"
    page_d.par.resolutionw, page_d.par.resolutionh = 1280, 720
    # the default face is wider and sets its lines tighter than Chicago
    page_d.par.fontsizex.expr = "27 if %s else 23" % CHICAGO
    page_d.par.linespacing.expr = "-10 if %s else -1" % CHICAGO
    page_d.par.borderspace1, page_d.par.borderspace2 = 98, 60
    page_d.par.alignx = "left"
    page_d.par.aligny = "top"
    page_d.par.bgalpha = 1
    page_d.nodeX, page_d.nodeY = -200, -560

    # model silhouettes: one lit render, one model visible at a time
    cam = scene.create(td.cameraCOMP, "cam")
    cam.par.tz = 2.7
    cam.par.fov = 30
    cam.nodeX, cam.nodeY = -400, -620
    light = scene.create(td.lightCOMP, "light")
    light.par.tx, light.par.ty, light.par.tz = -2.5, 3, 3
    light.par.dimmer = 1.6
    light.nodeX, light.nodeY = -400, -740
    geos = []
    for i, row in enumerate(models):
        m = row["model"]
        geo = LIB["import_model"](scene, "m_" + m, m)
        geo.par.render.expr = "int(op('ctl')['model']) == %d" % i
        geo.par.ry.expr = "op('shot')['seed'] * 360 + op('hub')['section'] * 47 + %r" % float(row.get("ry", 0))
        geo.par.rx, geo.par.rz = row.get("rx", 12), row.get("rz", 0)
        geo.par.scale = row.get("scale", 1.0)
        geo.nodeX, geo.nodeY = -200 + 130 * i, -740
        geo.op("mesh").cook(force=True)   # a hidden Geometry COMP loads on first show: a 25-50 ms hitch
        if paths.have("models/%s/basecolor.png" % m):
            geo.op("tex").cook(force=True)
        else:
            geo.op("mat").par.basecolormap = ""   # no library: a plain material, no empty Movie File In
        if not paths.have("models/%s/model.obj" % m):
            _fit_unit(geo, i)
        geos.append(geo)
    render = scene.create(td.renderTOP, "model")
    render.par.camera = cam.path
    render.par.lights = light.path
    render.par.geometry = " ".join(g.path for g in geos)
    render.par.outputresolution = "custom"
    render.par.resolutionw, render.par.resolutionh = 640, 640
    render.nodeX, render.nodeY = -200, -620

    shape = scene.create(td.switchTOP, "shape")
    _wire(shape, text)
    render.outputConnectors[0].connect(shape)
    page.outputConnectors[0].connect(shape)
    page_d.outputConnectors[0].connect(shape)
    shape.par.index.expr = "3 if (op('tk')['shape'] == 2 and %s) else op('tk')['shape']" % desc
    shape.nodeX, shape.nodeY = 0, -450

    # Input: another scene's picture (the COMP's Input parameter). Blank or unknown = a black constant,
    # and then nothing downstream uses it (ctl/hasin is 0).
    inp_none = scene.create(td.constantTOP, "inp_none")
    inp_none.par.colorr = inp_none.par.colorg = inp_none.par.colorb = 0
    inp_none.par.outputresolution = "custom"
    inp_none.par.resolutionw, inp_none.par.resolutionh = 16, 16
    inp_none.nodeX, inp_none.nodeY = -200, -900
    inp = scene.create(td.selectTOP, "inp")
    inp.par.top.expr = "%s if op('ctl')['hasin'] > 0.5 else 'inp_none'" % inpath
    inp.nodeX, inp.nodeY = 0, -900
    # its average colour (two mipmapped reductions), so src can tell subject from background
    insmall = scene.create(td.resolutionTOP, "insmall")
    insmall.par.outputresolution = "custom"
    insmall.par.resolutionw, insmall.par.resolutionh = 64, 36
    insmall.par.inputfiltertype = "mipmap"
    inp.outputConnectors[0].connect(insmall)
    insmall.nodeX, insmall.nodeY = 150, -1000
    inmean = scene.create(td.resolutionTOP, "inmean")
    inmean.par.outputresolution = "custom"
    inmean.par.resolutionw, inmean.par.resolutionh = 1, 1
    inmean.par.inputfiltertype = "mipmap"
    insmall.outputConnectors[0].connect(inmean)
    inmean.nodeX, inmean.nodeY = 300, -1000

    src = _glsl(scene, "src", 200, -450, DYE_W, DYE_H, "rgba8fixed")
    _wire(src, shape, inp, inmean)
    _vecs(src, [
        ("uSrc", ["op('tk')['src']", "op('tk')['scale']", "op('ctl')['rot']", "op('tk')['copies']"]),
        ("uPos", ["op('ctl')['px']", "op('ctl')['py']", seed, "op('hub')['section']"]),
        ("uSel", ["op('tk')['inka']", "op('tk')['inkb']", "op('hub')['evolve'] % 1000", 0]),
        ("uIn", ["op('ctl2')['inink']", "op('tk')['incol']", "op('tk')['ingain']", 0]),
        ("uInR", ["op('tk')['inlo']", "op('tk')['inhi']", 0, 0]),
    ])

    # ------------------------------------------------------------------ fluid
    u_time = ["op('hub')['evolve'] % 1000", "op('shot')['age']", "op('ctl')['id']", "op('ctl')['boot']"]
    u_hits = ["op('hub')['hit_low']", "op('hub')['hit_mid']", "op('hub')['hit_high']", "op('hub')['bass']"]
    u_k = ["op('ctl')['k1']", "op('ctl')['k2']", "op('ctl')['k3']", "op('tk')['kmode']"]
    u_s = ["op('ctl')['s1']", "op('ctl')['s2']", "op('ctl')['s3']", "op('hub')['vocals']"]
    u_noz = ["op('ctl')['nx']", "op('ctl')['ny']", "op('ctl')['ns']", "op('ctl')['na']"]

    fbv = _feedback(scene, "fbv", VEL_W, VEL_H, "rgba32float", 200, 0)
    fbd = _feedback(scene, "fbd", DYE_W, DYE_H, "rgba16float", 200, -220)

    vstep = _glsl(scene, "vstep", 400, 0, VEL_W, VEL_H, "rgba32float")
    _wire(vstep, fbv, fbd)
    _vecs(vstep, [
        ("uTime", u_time), ("uHits", u_hits), ("uK", u_k), ("uS", u_s), ("uNoz", u_noz),
        ("uTake", ["op('tk')['stir']", "op('tk')['buoy']", "op('tk')['vort']", "op('tk')['damp']"]),
        ("uGain", ["op('tk')['kgain']", "op('tk')['sgain']", 1, "op('tk')['arr']"]),
    ])
    diverge = _glsl(scene, "diverge", 600, 0, VEL_W, VEL_H, "rgba32float")
    _wire(diverge, vstep)
    jacobi = _glsl(scene, "jacobi", 800, 0, VEL_W, VEL_H, "rgba32float")
    jacobi.par.npasses = JACOBI
    _wire(jacobi, diverge)
    proj = _glsl(scene, "proj", 1000, 0, VEL_W, VEL_H, "rgba32float")
    _wire(proj, vstep, jacobi)
    _vecs(proj, [("uTime", u_time)])
    for g in (vstep, diverge, jacobi, proj):
        g.par.inputextenduv = "hold"
    fbv.par.top = proj.name
    fbv.par.resetpulse.pulse()

    dye = _glsl(scene, "dye", 1200, -220, DYE_W, DYE_H, "rgba16float")
    _wire(dye, fbd, proj, src)
    dye.par.inputextenduv = "hold"
    _vecs(dye, [
        ("uTime", u_time),
        ("uStamp", ["op('ctl')['stamp']", "op('tk')['diss']", "op('tk')['kamt']", "op('tk')['hamt']"]),
        ("uHits", u_hits), ("uK", u_k), ("uS", u_s), ("uNoz", u_noz),
        ("uInk", ["op('tk')['kink']", "op('tk')['sink']", "op('tk')['nink']", "op('tk')['hink']"]),
        ("uH", ["op('ctl')['h1']", "op('ctl')['h2']", "op('ctl')['h3']", "op('tk')['samt']"]),
        ("uIn", ["op('ctl2')['infeed']", "op('ctl2')['clean']", 0, 0]),
    ])
    fbd.par.top = dye.name
    fbd.par.resetpulse.pulse()

    # ------------------------------------------------------------------ light it
    # the inkblot take's caption, as on a test plate
    caption = scene.create(td.textTOP, "caption")
    caption.par.text.expr = ("op('dcaps')[%s, (int(op('shot')['seed'] * 31) + int(op('hub')['section'])) %% "
                             "op('dcaps').numCols].val if %s else "
                             "'PLATE %%d.   ' %% (1 + int(op('shot')['seed'] * 89) %% 12) + op('captions')"
                             "[(int(op('shot')['seed'] * 31) + int(op('hub')['section'])) %% op('captions').numRows, 0].val"
                             % (take_i, desc))
    caption.par.fontfile.expr = CHICAGO
    caption.par.outputresolution = "custom"
    caption.par.resolutionw, caption.par.resolutionh = 1280, 720
    caption.par.fontsizex = 24
    caption.par.alignx = "center"
    caption.par.aligny = "bottom"
    caption.par.bgalpha = 1
    caption.par.positiony.expr = "11 if %s else 0" % desc
    caption.nodeX, caption.nodeY = 1800, -450

    form_file = scene.create(td.moviefileinTOP, "form_file")
    form_file.par.file.expr = "mod.paths.model_texture(%r)" % sheet["model"]
    form_file.nodeX, form_file.nodeY = 1050, -340
    # with no assets: a sheet typed here, so the take still has one under the water
    form_gen = scene.create(td.textTOP, "form_gen")
    form_gen.par.text = "\n".join(W["SHEET_STANDIN"])
    form_gen.par.fontfile.expr = CHICAGO
    form_gen.par.outputresolution = "custom"
    form_gen.par.resolutionw, form_gen.par.resolutionh = 1032, 800
    form_gen.par.fontsizex = 30
    form_gen.par.linespacing = 14
    form_gen.par.alignx = "left"
    form_gen.par.aligny = "top"
    form_gen.par.borderspace1, form_gen.par.borderspace2 = 60, 130
    form_gen.par.fontcolorr = form_gen.par.fontcolorg = form_gen.par.fontcolorb = 0.12
    form_gen.par.bgcolorr = form_gen.par.bgcolorg = form_gen.par.bgcolorb = 0.955
    form_gen.par.bgalpha = 1
    form_gen.nodeX, form_gen.nodeY = 1050, -450
    form = scene.create(td.switchTOP, "form")
    _wire(form, form_file)
    form_gen.outputConnectors[0].connect(form)
    form.par.index.expr = "0 if mod.paths.model_texture(%r) else 1" % sheet["model"]
    form.nodeX, form.nodeY = 1200, -450
    # what lies under the water: the sheet, the Describe sheet, or the Input picture
    form_d = scene.create(td.textTOP, "form_d")
    form_d.par.text = "\n".join(SHEET_DESCRIBE)
    form_d.par.fontfile.expr = CHICAGO
    form_d.par.outputresolution = "custom"
    form_d.par.resolutionw, form_d.par.resolutionh = 1032, 800
    form_d.par.fontsizex = 25
    form_d.par.alignx = "left"
    form_d.par.aligny = "top"
    form_d.par.borderspace1, form_d.par.borderspace2 = 195, 150
    form_d.par.fontcolorr = form_d.par.fontcolorg = form_d.par.fontcolorb = 0.12
    form_d.par.bgcolorr = form_d.par.bgcolorg = form_d.par.bgcolorb = 0.955
    form_d.par.bgalpha = 1
    form_d.nodeX, form_d.nodeY = 1200, -560
    paper = scene.create(td.switchTOP, "paper")
    _wire(paper, form)
    form_d.outputConnectors[0].connect(paper)
    inp.outputConnectors[0].connect(paper)
    paper.par.index.expr = "2 if op('ctl2')['paper'] > 2.5 else (1 if %s else 0)" % desc
    paper.nodeX, paper.nodeY = 1350, -450

    shade = _glsl(scene, "shade", 1400, 0, 1280, 720, "rgba8fixed")
    _wire(shade, dye, proj, paper)
    shade.par.inputextenduv = "hold"
    _vecs(shade, [
        ("uView", ["op('ctl')['zoom']", "op('ctl')['vx']", "op('ctl')['vy']", "op('ctl')['vrot']"]),
        ("uStyle", ["op('tk')['style']", "op('ctl2')['paper']", "op('ctl2')['refr']", "op('tk')['bump']"]),
        # w: the sheet's width / height, and its height in frame heights
        ("uPaper", ["op('tk')['p_r']", "op('tk')['p_g']", "op('tk')['p_b']", "op('ctl2')['shasp']"]),
        ("uInk0", ["op('tk')['a_r']", "op('tk')['a_g']", "op('tk')['a_b']", "op('ctl2')['shsize']"]),
        ("uInk1", ["op('tk')['b_r']", "op('tk')['b_g']", "op('tk')['b_b']", 1]),
        ("uInk2", ["op('tk')['c_r']", "op('tk')['c_g']", "op('tk')['c_b']", 1]),
        ("uMore", ["op('ctl')['inv']", "op('tk')['sharp']", "op('tk')['mirror']", "op('tk')['bands']"]),
        ("uFx", ["op('hub')['pulse']", "op('hub')['hit_low']", "op('hub')['hit_high']", "op('hub')['energy']"]),
        ("uTime", ["op('hub')['evolve'] % 1000", "op('shot')['age']", "op('hub')['beat_pos']", seed]),
    ])

    # glow from the highlights (the luminous takes lean on it; the 1-bit take turns it off)
    u_glow = ["op('tk')['glow']", "op('tk')['glowth']", "op('ctl')['cap']", "op('ctl')['capl']"]
    bright = _glsl(scene, "bright", 1600, -220, 320, 180)
    _wire(bright, shade)
    _vecs(bright, [("uGlow", u_glow)])
    glow = scene.create(td.blurTOP, "glow")
    bright.outputConnectors[0].connect(glow)
    glow.par.size = 10
    glow.par.format = "rgba16float"
    glow.par.dither = False
    glow.nodeX, glow.nodeY = 1800, -220
    grade = _glsl(scene, "grade", 2000, 0, 1280, 720, "rgba8fixed")
    _wire(grade, shade, glow, caption)
    _vecs(grade, [("uGlow", u_glow)])

    out1 = scene.op("out1")
    out1.nodeX = 2200
    grade.outputConnectors[0].connect(out1)
    return scene.path
