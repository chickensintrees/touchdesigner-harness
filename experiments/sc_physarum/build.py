# Builds /project1/sc_physarum: a Physarum (slime mould) agent simulation steered by phrases, 3D models and printed sheets.
# Idempotent: run it again to rebuild.
#
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open(project.folder + '/experiments/sc_physarum/build.py', encoding='utf-8').read(), g); g['build']()
#
# see: experiments/sc_physarum/NOTES.md (2026-11-10)
import json

import td

SLUG = "sc_physarum"
# No folder is named here: the repository is where the open project is saved, and every file
# parameter is an expression on the scene's paths module. see: experiments/sw_hub/SCENE_BRIEF.md "Portability"
HERE = td.project.folder.replace(chr(92), "/") + "/experiments/" + SLUG    # only for reading files at build time
FONTS = ("archivo", "chicago", "barlow")     # the 'font' / 'lfont' column of TAKES indexes this


def FONT(index_expr):
    """Expression for a font file parameter ('' = TouchDesigner's default face when the font is not in assets)."""
    return "mod.paths.font(" + repr(FONTS) + "[" + index_expr + "])"


# With no model library every prop is TouchDesigner's teapot (mod.paths.model_file). It is 1.96 units wide and
# sits on its base, so it is brought to the library's convention (centred, longest side 1), and each of the six
# slots holds it at a different tilt so a new section still brings a new silhouette.
TEAPOT = dict(scale=0.509, cy=0.458, tilt=[(0, 0), (0, 90), (180, 0), (-90, 0), (35, 25), (0, -60)])

SIDE = 480                # 480 x 480 = 230,400 agents (cap is 250k points)
W, H = 1280, 720          # trail map = output size, so one agent lands on one pixel

# Everything a pack may replace: the words the mould eats, and which models and sheets it grows on.
# build() reads it through LIB['scene_words'], so a pack's scenes/sc_physarum/words.json can give its own
# values under the same names. see: experiments/sw_hub/paths_module.py words()
DEFAULTS = {
    # one phrase per shot (bleed, dishes, rust), or nine of them run together as a wall (toner, crt)
    "PHRASES": [
        "THE ORIGIN:\nNOTHING ON RECORD.",
        "DO NOT TOUCH",
        "A FRAME IS ARRIVING.\nIT IS MADE NOW.",
        "NO PICTURE\nIS STORED.",
        "THERE IS NO\nRECORDING.",
        "SOUND IN.\nPICTURE OUT.",
        "OBJECT OF\nNO USE",
        "CATALOGUE 0047",
        "EVERY FRAME IS MADE\nWHILE YOU WATCH.",
        "THE PICTURE\nIS RUNNING\nRIGHT NOW",
        "THIS PICTURE\nIS MADE OF SOUND.",
        "LISTEN TO THIS\nWITH YOUR EYES.",
        "EVERYTHING\nIS NOW",
        "FOUND HERE,\nNOT MADE.",
        "OBJECT OF UNKNOWN\nPURPOSE",
        "ARCHIVE OF\nUNLABELLED\nARTEFACTS",
        "LOOP. LOOP.\nLOOPLOOP.",
        "SIGNAL\nRECEIVED...",
        "FEEDBACK\n....... LOOP",
        "HERE. NOW.\nREAL TIME.",
        "PLATE 047",
        "ITEM 12-B",
        "NO PICTURE\nBEFORE SOUND.",
    ],
    # a word bigger than the frame (onebit)
    "FRAGMENTS": ["LOOP", "NOW", "OUT.", "12-B", "KICK", "REAL\nTIME", "LOUD", "IN.", "0047", "NO", "NOISE", "FEED"],
    # typed out on cream paper when the pack has no picture for a sheet
    "STANDIN_SHEETS": [
        "PLATE 047\n"
        "------------------------------------\n"
        "1. OBJECT  .........................\n"
        "2. ORIGIN: UNRECORDED  .............\n"
        "3. FOUND  ........ / ......... / ...\n"
        "4. USE:       [ ] NOTHING ON RECORD\n"
        "5. HANDLING:  [X] WITH BOTH HANDS\n"
        "------------------------------------\n"
        "CATALOGUED BY  .....................\n"
        "DO NOT TOUCH",
        "ITEM 12-B\n"
        "====================================\n"
        "A FRAME IS ARRIVING.\n"
        "IT IS MADE FROM:  __________________\n"
        "____________________________________\n"
        "____________________________________\n"
        "[ ] SIGNAL       [ ] NOISE\n"
        "====================================\n"
        "OBJECT OF UNKNOWN PURPOSE\n"
        "X __________________________________",
        "OBJECT OF THE DAY\n"
        "\n"
        "FOUND:  HERE, NOT MADE\n"
        "HELD:  ARCHIVE OF UNLABELLED OBJECTS\n"
        "RE:  THE SOUND\n"
        "____________________________________\n"
        "SOUND IN. PICTURE OUT.\n"
        "____________________________________\n"
        "SEE CATALOGUE 0047\n"
        "####  ##  ######  ###  ##  #####  ##",
    ],
    # the six models of the X-ray and poster takes (seed + section picks one): model, scale, tilt (degrees
    # about x), lift. A library model is centred with its longest side 1; the row is on top of that.
    "PROPS": [
        ["gramophone", 0.84, 0, 0],
        ["astrolabe", 0.85, 0, 0],
        ["marble_bust", 0.85, 0, 0],
        ["lander", 0.8, 0, 0],
        ["hourglass", 0.85, 0, 0],
        ["wire_cage", 0.72, 0, 0],
    ],
    # the printed sheets of the sheet take (their basecolor.png): model, invert (1 = light lines on dark
    # paper), white (the brightness of the paper, which is brought up to white)
    "SHEETS": [
        ["star_chart", 0, 1.0],
        ["blueprint", 1, 0.8],
        ["ticket", 0, 1.0],
    ],
}

# One row per take. The cutter sets Take; take % len(TAKES) picks the row.
#   look     display look in shade.frag        src      attractant source in amap.frag
#   spawn    where agents start (agents.frag)  kick     what a kick does (0 scatter, 1 ring, 2 back onto shape, 3 burst)
#   sa/sd/ra/st  sensor angle (deg), sensor distance (px), turn (deg), step (px): the species at rest
#   sav/sdb/rao  how far vocals / bass / other push them
_BASE = dict(
    look=0, src=2, spawn=1, kick=1, kshare=0.05, sshare=0.5, ringr=6,
    sa=30, sav=30, sd=5, sdb=7, ra=26, rao=22, st=1.2,
    attr=5.0, wall=0, wander=0.25, dep=0.55, don=0.90, doff=0.72, dif=0.55, mem=0.985, boost=0.6,
    layout=0, font=0, fsize=300, fit="alwaysfit", wrap=0, ax="center", ay="center",
    tzoom=1.0, trot=0.0, toff=0.0,                    # text / sheet placement in amap: zoom, +-rotation, +-offset by seed
    mscale=1.35, mx=0.42, my=0.0, myj=0.0, scent=0.0, reach=0.2,   # the prop: size, side offset, height, far scent
    vzoom=1.0, vrot=0.0, vpan=0.0, vdrx=0.0, vdry=0.0, pitch=0.0, camh=0.4, inv=0,
    drift=0.0, drifta=0.0, recon=0.0, vzj=0.0,       # agents: pull toward a heading (+- seed), re-condense share; view zoom jitter
    flipk=0.4,                                        # how far a snare turns attraction into repulsion   # the display's view of the map
    # Describe mode (see SCENE_BRIEF "Describe mode and Input", 2026-11-11):
    #   describe  the words that replace the take's phrases (same slot, same font, picked by seed + section)
    #   label     a small caption card laid over the picture, for takes whose own text cannot be read ('' = none)
    #   lside     which bottom corner the card sits in: 'l', 'r', or 'auto' (the side away from the prop)
    #   dfsize    font size of the words when it must differ from fsize (None = fsize); dtz the same for tzoom;
    #             dvz scales the view's zoom jitter and pan, so a sentence is not cropped by a random close-up
    describe=[], label="", lside="l", lfont=2, lsize=24, dfsize=None, dtz=None, dvz=1.0,
    # Input: iscale is the size of the given picture where a prop used to be (1 = full frame)
    iscale=1.0)

NAME = "SLIME MOULD SIMULATION"


def _take(name, **kw):
    d = dict(_BASE)
    d.update(kw)
    d["name"] = name
    return d


TAKES = [
    # 0 big prop off-centre, fine lace, blue film
    _take("xray", dep=0.45, boost=0.2, doff=0.62, lside="auto",
          label=NAME + "\n230,400 agents sniff out the X-ray of a turning\n3D model and lay trails along it. A kick throws a ring."),
    # 1 no subject: an endless floor seen at a low angle, thick arteries, the camera travels
    _take("marble", flipk=1.0, look=1, src=0, spawn=0, kick=1, kshare=0.06, ringr=10,
          sa=40, sav=25, sd=16, sdb=16, ra=20, rao=15, st=2.0, attr=1.2, dep=0.6, don=0.93, doff=0.90, dif=0.75,
          pitch=0.27, camh=0.30, vpan=1.0, vdry=0.02, vrot=0.5,
          label=NAME + "\nNo subject: 230,400 agents follow each other's\ntrails over faint noise. Bass makes the mesh coarser."),
    # 2 top-down on a printed sheet: mould grows from a few blots along the printed lines
    _take("sheet", flipk=0.3, look=2, src=3, spawn=4, kick=1, kshare=0.03, sshare=0.25,
          sa=35, sav=25, sd=9, sdb=8, ra=30, rao=20, st=1.6, attr=3.5, wall=1, wander=0.5, doff=0.88, mem=0.997,
          tzoom=1.55, trot=0.10, toff=0.10, dtz=1.1,
          # printed on a blank sheet that replaces the printed one (the 'dsheet' Text TOP)
          describe=["HOW THIS PICTURE IS MADE\n\n1. 230,400 AGENTS START IN FIVE BLOTS.\n2. EACH ONE SNIFFS THREE POINTS AHEAD.\n"
                    "3. IT TURNS TOWARD THE STRONGEST SMELL,\n    STEPS, AND LEAVES A TRAIL.\n"
                    "4. PRINTED INK SMELLS LIKE FOOD,\n    SO THE MOULD FOLLOWS THESE LINES.\n5. TRAILS BLUR AND FADE."]),
    # 3 a cropped fragment of a word, letterforms bigger than the frame, 1-bit
    _take("onebit", flipk=1.0, look=3, src=1, spawn=1, kick=0, kshare=0.22,
          sa=22, sav=30, sd=12, sdb=10, ra=35, rao=20, st=2.0, attr=4.0,
          layout=2, font=1, tzoom=1.7, trot=0.12, toff=0.22,
          describe=["TRAIL", "AGENT", "SLIME", "MOULD", "SNIFF", "TURN", "STEP", "1-BIT"], lfont=1, lsize=18,
          label=NAME + "\nTrails of 230,400 agents, cut to pure\nblack or white by a 4x4 dither."),
    # 4 many subjects: a grid of culture dishes on a light table
    _take("dishes", flipk=0.0, look=4, src=4, spawn=1, kick=2, kshare=0.12, sshare=0.6,
          sa=45, sav=20, sd=8, sdb=8, ra=30, rao=20, st=1.3, attr=1.5, wall=1, doff=0.88, mem=0.995,
          layout=0, tzoom=1.0, vzoom=1.22, vrot=0.35, vpan=1.0,
          describe=["SLIME\nMOULD", "TRAIL\nMAP", "AGENTS", "WALLED\nIN"],
          label=NAME + "\nEvery dish is walled: agents cannot cross the glass.\nEach kick drops some of them back onto the food."),
    # 5 tiny subject in a big field: rivers converge on a small prop, flat poster colours
    _take("poster", look=5, src=2, spawn=3, kick=3, kshare=0.10, sshare=0.0, ringr=8,
          sa=20, sav=20, sd=14, sdb=10, ra=16, rao=12, st=2.4, attr=4.0, doff=0.80, flipk=0.0,
          mscale=0.42, mx=0.50, myj=0.5, scent=0.7, reach=0.30, lside="auto", iscale=0.62,
          label=NAME + "\n230,400 agents burst out of one small 3D model,\nthen crawl back to it along its scent."),
    # 6 a wall of small text on a CRT, eaten line by line
    _take("crt", flipk=0.6, look=6, src=1, spawn=6, kick=1, kshare=0.05,
          sa=30, sav=25, sd=6, sdb=6, ra=28, rao=20, st=1.4, attr=5.0,
          layout=1, font=1, fsize=58, fit="nofit", wrap=1, ax="left", ay="top",
          dfsize=54, dtz=0.92,
          describe=["THIS IS A SLIME MOULD SIMULATION. 230,400 AGENTS EACH SNIFF LEFT, AHEAD AND RIGHT, TURN TOWARD THE "
                    "STRONGEST SMELL, STEP, AND LEAVE A TRAIL. THIS TEXT IS THE FOOD, SO THE VEINS GATHER ON THE LETTERS.",
                    "NOBODY DREW THESE VEINS. 230,400 AGENTS START ON NINE ROWS AND MARCH UP AND DOWN. EACH ONE STEERS "
                    "TOWARD THE STRONGEST TRAIL. THESE WORDS ARE FOOD. A KICK THROWS RINGS. A SNARE MAKES THE MOULD FLEE."]),
    # 7 extreme close-up: rust under paint, a few letter edges crossing the frame
    _take("rust", look=7, src=1, spawn=1, kick=2, kshare=0.10,
          sa=50, sav=20, sd=10, sdb=10, ra=30, rao=15, st=1.0, attr=4.0, dep=0.6, don=0.95, doff=0.80, dif=0.9,
          layout=0, font=2, vzoom=3.0, vrot=0.5, vpan=0.5, vdrx=0.004,
          describe=["SLIME\nMOULD", "TRAIL\nMAP", "230,400\nAGENTS"],
          label=NAME + ", 3x CLOSE-UP\nThe trail map lit as a height field: thick trails\nread as rust, thin ones as blistered paint."),
    # 8 flow, not network: the ink of a notice runs down a coloured sheet in rivulets (seed: pink / goldenrod, slant)
    _take("bleed", look=8, src=1, spawn=1, kick=2, kshare=0.45, sshare=0.7, flipk=0.0,
          sa=22, sav=15, sd=13, sdb=8, ra=18, rao=10, st=2.4, attr=0.5, wander=0.18,
          dep=0.30, don=0.90, doff=0.955, dif=0.22, mem=0.99, boost=0.0,
          layout=0, font=0, ay="top", tzoom=0.86, trot=0.03, toff=0.05, drift=0.14, drifta=0.5,
          describe=["EVERY DRIP IS\nA TRAIL OF AGENTS.", "230,400 AGENTS,\nALL PULLED DOWNHILL.", "DRIPS MERGE WHERE\nTHEIR TRAILS MEET.",
                    "A KICK SENDS MANY\nBACK TO THE LETTERS.", "SLIME MOULD AGENTS\nWITH A DOWNHILL PULL.",
                    "OFF THE PAGE, THEY\nSTART AGAIN HERE."]),
    # 9 one symmetric thing: a folded inkblot on a card (seed: black or red ink, card angle); kicks spatter it
    _take("blot", look=9, src=5, spawn=3, kick=3, kshare=0.10, sshare=0.5, ringr=8, flipk=0.8,
          sa=45, sav=25, sd=13, sdb=10, ra=30, rao=20, st=1.6, attr=2.5, wall=1, wander=0.4,
          dep=0.6, don=0.94, doff=0.90, dif=0.8, mem=0.992, mx=0.0, vzoom=0.90, vrot=0.10,
          label=NAME + ", FOLDED\nOne half of the trail map is shown twice, like an\ninkblot. Kicks spatter it. A new section, a new blot."),
    # 10 no veins at all: the agents as toner grains on copier glass; every kick blows the page to dust
    _take("toner", look=10, src=1, spawn=0, kick=4, kshare=3.0, sshare=0.9, flipk=0.6,
          sa=45, sav=20, sd=6, sdb=4, ra=40, rao=20, st=2.0, attr=6.0, wander=1.4,
          dep=0.0, don=0.80, doff=0.60, dif=0.5, boost=0.0, recon=0.06, 
          layout=1, font=2, fsize=150, fit="nofit", wrap=1, ax="left", ay="top",
          tzoom=1.1, trot=0.07, toff=0.06, vzj=1.6, vpan=0.25, dfsize=68, dtz=0.9, dvz=0.0,
          describe=["EVERY SPECK IS ONE AGENT. 230,400 OF THEM SNIFF OUT THESE LETTERS AND CROWD ONTO THEM. NO TRAILS ARE DRAWN "
                    "HERE. A KICK BLOWS THEM LOOSE AND THEY SETTLE BACK.",
                    "A SLIME MOULD SIMULATION WITH THE TRAILS SWITCHED OFF. WHAT IS LEFT IS 230,400 GRAINS HUNTING FOR LETTERS. "
                    "THE SNARE LOOSENS THEM. THE BAR OF LIGHT CROSSES ONCE EVERY BAR."]),
]

# Play order: the cutter counts a scene's visits, so neighbours in this list should be as unlike as possible
# (network / flow / grains / blot, dark / light, one subject / many / none).
ORDER = ["xray", "bleed", "marble", "toner", "dishes", "blot", "sheet", "onebit", "poster", "crt", "rust"]
TAKES = [next(t for t in TAKES if t["name"] == n) for n in ORDER]


def T(key):
    """Expression that reads TAKES[take][key]."""
    return "(" + "".join(repr(t[key]) + "," for t in TAKES) + ")[int(op('shot')['take'])%" + str(len(TAKES)) + "]"


SEED = "op('shot')['seed']"
DESC = "parent().par.Describe"
TAKE = "int(op('shot')['take'])"
JS = "op('describe_json').text"
WJS = "op('words_json').text"
INP = "op('textlib').module.inp(parent())"      # '' unless Input names a TOP outside this scene
SEC = "int(op('hub')['section'])"
ENERGY = "min(1,max(0,(op('stems')['energy']-0.33)/0.32))"
# each musical section breeds a finer or a coarser network (scales the sensor distance): lace, normal, arteries
BREED = "(0.6,1.0,1.7)[(int(op('hub')['section'])+int(op('shot')['seed']*3))%3]"


def Tv(vals):
    """Expression that reads vals[take]."""
    return "(" + "".join(repr(v) + "," for v in vals) + ")[int(op('shot')['take'])%" + str(len(vals)) + "]"


def _h(salt):
    """0..1 hash of the shot seed."""
    return "((math.sin(" + SEED + "*%s+1.7)*43758.5453)%%1)" % salt


MY = "(" + T("my") + "+" + T("myj") + "*(" + _h(8.8) + "-0.5))"


# where the prop sits on screen (uv), from the camera in build(): 40 degree horizontal field at 3.04 units
CTRX = "0.5+0.5*(1 if " + SEED + "<0.5 else -1)*" + T("mx") + "/1.105"
CTRY = "0.5+0.5*(" + MY + ")/0.62"


def _dat(scene, name, rel, x, y):
    d = scene.create(td.textDAT, name)
    d.text = open(HERE + "/" + rel, encoding="utf-8").read()  # the file par loads a frame late
    d.par.file.expr = "mod.paths.here(%r)" % rel
    d.par.syncfile = True
    d.nodeX, d.nodeY = x, y
    return d


def _glsl(scene, name, x, y, w, h, fmt="rgba16float"):
    g = scene.create(td.glslTOP, name)
    for d in list(g.docked):
        if d.name in (name + "_pixel", name + "_compute"):
            d.destroy()
    g.par.pixeldat = _dat(scene, name + "_frag", "shaders/" + name + ".frag", x, y - 130).name
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


def _mat(scene, name, x, y):
    m = scene.create(td.glslMAT, name)
    for d in list(m.docked):
        d.destroy()
    m.par.vdat = _dat(scene, name + "_vertex", "shaders/" + name + "_vertex.glsl", x, y - 130).path
    m.par.pdat = _dat(scene, name + "_pixel", "shaders/" + name + "_pixel.glsl", x, y - 260).path
    # everything here is summed light: no depth, no culling
    m.par.blending = True
    m.par.srcblend = "one"
    m.par.destblend = "one"
    m.par.srcblenda = "one"
    m.par.destblenda = "one"
    m.par.depthtest = False
    m.par.depthwriting = False
    m.par.cullface = "neither"
    m.nodeX, m.nodeY = x, y
    return m


def _const(scene, name, w, h, fmt, x, y):
    z = scene.create(td.constantTOP, name)
    z.par.colorr = z.par.colorg = z.par.colorb = 0
    z.par.alpha = 0
    z.par.outputresolution = "custom"
    z.par.resolutionw, z.par.resolutionh = w, h
    z.par.format = fmt
    z.nodeX, z.nodeY = x, y
    return z


def build():
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, x=0, y=-1100)
    WORDS = LIB["scene_words"](scene, DEFAULTS)
    PROPS = [dict(zip(("model", "scale", "tilt", "lift"), row)) for row in WORDS["PROPS"]]
    SHEETS = [dict(zip(("model", "invert", "white"), row)) for row in WORDS["SHEETS"]]

    # ---- control ----
    stems_sel = scene.create(td.selectCHOP, "stems_sel")
    stems_sel.par.chop = "hub"
    stems_sel.par.channames = "bass drums vocals other energy"
    stems_sel.nodeX, stems_sel.nodeY = -200, 200
    stems = scene.create(td.lagCHOP, "stems")
    stems.par.lag1, stems.par.lag2 = 0.10, 0.30
    stems_sel.outputConnectors[0].connect(stems)
    stems.nodeX, stems.nodeY = -50, 200

    ev = scene.create(td.constantCHOP, "ev")
    ev.seq.const.numBlocks = 6
    for i, n in enumerate(["boot", "kick", "sec", "n", "fr", "flip"]):
        getattr(ev.par, "const%dname" % i).val = n
    ev.par.const0value = 1
    ev.nodeX, ev.nodeY = 100, 200
    events = scene.create(td.executeDAT, "events")
    events.text = open(HERE + "/events.py", encoding="utf-8").read()
    events.par.file.expr = "mod.paths.here('events.py')"
    events.par.syncfile = True
    events.par.framestart = True
    events.par.active = True
    events.nodeX, events.nodeY = 100, 330

    # ---- attractant sources ----
    textlib = _dat(scene, "textlib", "textlib.py", -1000, -500)
    text = scene.create(td.textTOP, "txt")
    # the words of every take, for Describe mode and the caption card (read by textlib.words / textlib.label)
    djson = scene.create(td.textDAT, "describe_json")
    djson.text = json.dumps([{"name": t["name"], "describe": t["describe"], "label": t["label"]} for t in TAKES])
    djson.nodeX, djson.nodeY = -1000, -370
    # the take's own phrases (DEFAULTS, or the pack's words.json), read by textlib.text / textlib.sheet
    wjson = scene.create(td.textDAT, "words_json")
    wjson.text = json.dumps({k: WORDS[k] for k in ("PHRASES", "FRAGMENTS", "STANDIN_SHEETS")})
    wjson.nodeX, wjson.nodeY = -1150, -370
    PICK = "int(" + SEED + "*23)+" + SEC
    text.par.text.expr = ("op('textlib').module.words(" + JS + ", " + TAKE + ", " + PICK + ") if " + DESC +
                          " else op('textlib').module.text(" + WJS + ", " + T("layout") + ", " + PICK + ")")
    text.par.fontfile.expr = FONT(T("font"))
    text.par.outputresolution = "custom"
    text.par.resolutionw, text.par.resolutionh = W, H
    text.par.fontautosize.expr = T("fit")
    text.par.fontsizex.expr = Tv([t["dfsize"] or t["fsize"] for t in TAKES]) + " if " + DESC + " else " + T("fsize")
    text.par.wordwrap.expr = T("wrap")
    text.par.alignx.expr = T("ax")
    text.par.aligny.expr = T("ay")
    text.par.linespacing = -6
    text.par.bgalpha = 1
    text.nodeX, text.nodeY = -800, -500

    xmat = _mat(scene, "xray", -1000, -900)
    prop_idx = "(int(" + SEED + "*%d)+%s)%%%d" % (len(PROPS), SEC, len(PROPS))
    geos = []
    for i, prop in enumerate(PROPS):
        slug = prop["model"]
        geo = scene.create(td.geometryCOMP, "m_" + slug)
        for c in geo.children:
            c.destroy()
        mesh = geo.create(td.fileinPOP, "mesh")
        mesh.par.file.expr = "mod.paths.model_file(%r)" % slug
        mesh.cook(force=True)      # a hidden geo would load its mesh at the first cut to it (TRAPS, sc_glyph_render)
        # the library model with its own row's scale, tilt and lift; the stand-in teapot scaled, centred and tilted (see TEAPOT)
        fit = geo.create(td.transformPOP, "fit")
        mesh.outputConnectors[0].connect(fit)
        have = "mod.paths.have('models/%s/model.obj')" % slug
        fit.par.scale.expr = "%r if " % prop["scale"] + have + " else %r" % TEAPOT["scale"]
        fit.par.py.expr = "0 if " + have + " else %r" % TEAPOT["cy"]
        fit.par.ty.expr = "%r if " % prop["lift"] + have + " else %r" % -TEAPOT["cy"]
        fit.par.rx.expr = "%r if " % prop["tilt"] + have + " else %r" % TEAPOT["tilt"][i][0]
        fit.par.rz.expr = "0 if " + have + " else %r" % TEAPOT["tilt"][i][1]
        fit.nodeX = 150
        fit.render = True
        fit.display = True
        fit.cook(force=True)
        geo.par.material = xmat.path
        geo.par.render.expr = "1 if " + prop_idx + "==%d else 0" % i
        geo.par.ry.expr = "op('hub')['evolve']*22+" + SEED + "*360"
        geo.par.scale.expr = T("mscale")
        geo.par.tx.expr = "(1 if " + SEED + "<0.5 else -1)*" + T("mx")
        geo.par.ty.expr = MY
        geo.nodeX, geo.nodeY = -800 + i * 130, -900
        geos.append(geo)
    look = scene.create(td.nullCOMP, "look")
    look.nodeX, look.nodeY = -800, -1030
    cam = scene.create(td.cameraCOMP, "cam")
    cam.par.tx, cam.par.ty, cam.par.tz = 0, 0.9, 2.9
    cam.par.lookat = look.path
    cam.par.fov = 40           # horizontal
    cam.nodeX, cam.nodeY = -670, -1030
    mrender = scene.create(td.renderTOP, "model_r")
    mrender.par.camera = cam.path
    mrender.par.geometry = " ".join(g.path for g in geos)
    mrender.par.lights = ""
    mrender.par.outputresolution = "custom"
    mrender.par.resolutionw, mrender.par.resolutionh = W, H
    mrender.par.format = "rgba16float"
    mrender.nodeX, mrender.nodeY = -540, -1030

    sheets = scene.create(td.switchTOP, "sheet")
    for i, row in enumerate(SHEETS):
        f = scene.create(td.moviefileinTOP, "f_" + row["model"])
        f.par.file.expr = "mod.paths.model_texture(%r)" % row["model"]
        f.nodeX, f.nodeY = -1000, -1250 - i * 130
        if row["invert"] or row["white"] != 1:
            # the mould eats dark ink on light paper: a light-on-dark print is turned over first, and
            # 'white' is the brightness of its paper, brought up to white
            lv = scene.create(td.levelTOP, "ink_" + row["model"])
            lv.par.invert = row["invert"]
            lv.par.inhigh = row["white"]
            lv.nodeX, lv.nodeY = -900, -1250 - i * 130
            f.outputConnectors[0].connect(lv)
            f = lv
        f.outputConnectors[0].connect(sheets)
    # Describe: a blank sheet with the explanation printed on it takes the printed sheet's place
    dsheet = scene.create(td.textTOP, "dsheet")
    dsheet.par.text.expr = "op('textlib').module.words(" + JS + ", %d, 0)" % ORDER.index("sheet")
    dsheet.par.fontfile.expr = "mod.paths.font('barlow')"
    dsheet.par.outputresolution = "custom"
    dsheet.par.resolutionw, dsheet.par.resolutionh = 1240, 960
    dsheet.par.fontautosize = "nofit"
    dsheet.par.fontsizex = 46
    dsheet.par.alignx, dsheet.par.aligny = "left", "center"
    dsheet.par.positionunit = "pixels"
    dsheet.par.positionx = 230
    dsheet.par.linespacing = 8
    dsheet.par.fontcolorr = dsheet.par.fontcolorg = dsheet.par.fontcolorb = 0
    dsheet.par.bgcolorr = dsheet.par.bgcolorg = dsheet.par.bgcolorb = 1
    dsheet.par.bgalpha = 1
    dsheet.nodeX, dsheet.nodeY = -1000, -1250 - len(SHEETS) * 130
    dsheet.outputConnectors[0].connect(sheets)
    # No sheet pictures in assets: a sheet typed out by a Text TOP stands in (textlib.sheet), one per slot,
    # so the Movie File In TOPs with nothing to load are never cooked.
    SHEET_I = "int(" + SEED + "*%d+%s)%%%d" % (len(SHEETS), SEC, len(SHEETS))
    ssheet = scene.create(td.textTOP, "ssheet")
    ssheet.par.text.expr = "op('textlib').module.sheet(" + WJS + ", " + SHEET_I + ")"
    ssheet.par.fontfile.expr = "mod.paths.font('chicago')"
    ssheet.par.outputresolution = "custom"
    ssheet.par.resolutionw, ssheet.par.resolutionh = 1240, 960
    ssheet.par.fontautosize = "nofit"
    ssheet.par.fontsizex = 44
    ssheet.par.alignx, ssheet.par.aligny = "left", "center"
    ssheet.par.positionunit = "pixels"
    ssheet.par.positionx = 90
    ssheet.par.linespacing = 10
    ssheet.par.fontcolorr = ssheet.par.fontcolorg = ssheet.par.fontcolorb = 0.05
    ssheet.par.bgcolorr, ssheet.par.bgcolorg, ssheet.par.bgcolorb = 0.93, 0.89, 0.78
    ssheet.par.bgalpha = 1
    ssheet.nodeX, ssheet.nodeY = -1000, -1250 - (len(SHEETS) + 1) * 130
    ssheet.outputConnectors[0].connect(sheets)
    HAVE_SHEET = "mod.paths.have('models/'+" + repr(tuple(r["model"] for r in SHEETS)) + "[" + SHEET_I + "]+'/basecolor.png')"
    sheets.par.index.expr = ("%d if " % len(SHEETS) + DESC + " else (" + SHEET_I + " if " + HAVE_SHEET +
                             " else %d)" % (len(SHEETS) + 1))
    sheets.nodeX, sheets.nodeY = -800, -1250

    amap = _glsl(scene, "amap", -300, -700, W, H)
    amap.par.inputextenduv = "zero"
    # Input: the picture named by the scene's Input parameter takes the place of the take's own food
    # (amap.frag reads it from slot 0 when uIn.x is 1). Blank Input: slot 0 is the text, as before.
    in_sel = scene.create(td.selectTOP, "in_sel")
    in_sel.par.top.expr = INP + " or 'zero_t'"
    in_sel.nodeX, in_sel.nodeY = -800, -370
    src0 = scene.create(td.switchTOP, "src0")
    text.outputConnectors[0].connect(src0)
    in_sel.outputConnectors[0].connect(src0)
    src0.par.index.expr = "1 if " + INP + " else 0"
    src0.nodeX, src0.nodeY = -600, -500
    _wire(amap, src0, mrender, sheets)
    _vecs(amap, [
        ("uMap", [T("src"), "op('hub')['evolve']", SEED, SEC]),
        ("uCtr", [CTRX, CTRY, T("scent"), T("reach")]),
        ("uXf", [Tv([t["dtz"] or t["tzoom"] for t in TAKES]) + " if " + DESC + " else " + T("tzoom"), T("trot") + "*2*(" + _h(9.3) + "-0.5)",
                 T("toff") + "*(" + _h(3.1) + "-0.5)", T("toff") + "*(" + _h(4.7) + "-0.5)"]),
        ("uIn", ["1 if " + INP + " else 0", T("iscale"), 0, 0]),
    ])

    # ---- the simulation: agents -> deposit -> trail, each closed by a Feedback TOP ----
    zero_a = _const(scene, "zero_a", SIDE, SIDE, "rgba32float", 0, 0)
    fb_a = scene.create(td.feedbackTOP, "fb_a")
    fb_a.par.format = "rgba32float"
    zero_a.outputConnectors[0].connect(fb_a)
    fb_a.nodeX, fb_a.nodeY = 150, 0
    zero_t = _const(scene, "zero_t", W, H, "rgba16float", 0, -400)
    fb_t = scene.create(td.feedbackTOP, "fb_t")
    fb_t.par.format = "rgba16float"
    zero_t.outputConnectors[0].connect(fb_t)
    fb_t.nodeX, fb_t.nodeY = 150, -400

    agents = _glsl(scene, "agents", 350, 0, SIDE, SIDE, "rgba32float")
    agents.par.inputextenduv = "repeat"
    _wire(agents, fb_a, fb_t, amap)
    S = "op('stems')"
    _vecs(agents, [
        ("uSpecies", ["math.radians(" + T("sa") + "+" + T("sav") + "*min(1.2," + S + "['vocals']))",
                      "(" + T("sd") + "+" + T("sdb") + "*min(1.6," + S + "['bass']))*" + BREED,
                      "math.radians(" + T("ra") + "+" + T("rao") + "*min(1.2," + S + "['other']))",
                      T("st") + "*(0.7+0.5*" + ENERGY + "+0.35*min(1.2," + S + "['drums']))"]),
        ("uField", [T("attr"), T("wall"), T("wander"), T("kick")]),
        ("uEvent", ["op('ev')['boot']", "op('ev')['kick']*" + T("kshare"), "op('ev')['sec']*" + T("sshare"),
                    "op('ev')['n']"]),
        ("uShot", [SEED, "op('ev')['fr']", T("spawn"), "op('ev')['flip']*" + T("flipk")]),
        ("uCtr", [CTRX, CTRY, 0, 0]),
        ("uExtra", [T("drift"), "-math.pi/2+" + T("drifta") + "*(" + _h(1.9) + "-0.5)", T("recon"), 0]),
        ("uRes", [W, H, 2.4, T("ringr")]),
    ])
    fb_a.par.top = agents.name

    dgeo = scene.create(td.geometryCOMP, "dots")
    for c in dgeo.children:
        c.destroy()
    grid = dgeo.create(td.gridPOP, "grid")
    grid.par.surftype = "points"
    grid.par.cols = SIDE
    grid.par.rows = SIDE
    grid.par.normal = "none"
    grid.par.texture = "none"
    grid.render = True
    grid.display = True
    dgeo.nodeX, dgeo.nodeY = 350, -260
    dmat = _mat(scene, "deposit", 350, -1000)
    dmat.seq.sampler.numBlocks = 1
    dmat.par.sampler0name = "sAgents"
    dmat.par.sampler0top = agents.path
    dmat.par.sampler0filter = "nearest"
    dgeo.par.material = dmat.path
    dcam = scene.create(td.cameraCOMP, "dcam")   # unused by the shader, but a Render TOP needs one
    dcam.nodeX, dcam.nodeY = 480, -260
    deposit = scene.create(td.renderTOP, "deposit_r")
    deposit.par.camera = dcam.path
    deposit.par.geometry = dgeo.path
    deposit.par.lights = ""
    deposit.par.outputresolution = "custom"
    deposit.par.resolutionw, deposit.par.resolutionh = W, H
    deposit.par.format = "rgba16float"
    deposit.par.antialias = "1x"
    deposit.nodeX, deposit.nodeY = 610, -260

    trail = _glsl(scene, "trail", 800, -400, W, H)
    trail.par.inputextenduv = "repeat"
    _wire(trail, fb_t, deposit, amap)
    _vecs(trail, [
        ("uTrail", [T("dif"), T("don"), T("dep"), T("doff")]),
        ("uTrail2", [T("mem"), "op('ev')['boot']", T("boost"), T("wall")]),
    ])
    fb_t.par.top = trail.name

    # ---- display ----
    small = scene.create(td.resolutionTOP, "soft_small")
    small.par.outputresolution = "custom"
    small.par.resolutionw, small.par.resolutionh = W // 4, H // 4
    trail.outputConnectors[0].connect(small)
    small.nodeX, small.nodeY = 950, -550
    soft = scene.create(td.blurTOP, "soft")
    soft.par.size = 6
    soft.par.format = "rgba16float"
    soft.par.dither = False
    small.outputConnectors[0].connect(soft)
    soft.nodeX, soft.nodeY = 1080, -550

    shade = _glsl(scene, "shade", 1250, -400, W, H, "rgba8fixed")
    shade.par.inputextenduv = "repeat"
    _wire(shade, trail, amap, soft)
    HUB = "op('hub')"
    DVZ = "(" + T("dvz") + " if " + DESC + " else 1)"
    _vecs(shade, [
        ("uLook", [T("look"), HUB + "['evolve']", SEED, "op('shot')['age']"]),
        ("uAudio", [HUB + "['pulse']", "min(1.2," + HUB + "['hit_low'])", "min(1.2," + HUB + "['hit_high'])", ENERGY]),
        ("uAudio2", [HUB + "['beat_pos']", "op('ev')['flip']", "min(1.6," + S + "['bass'])", "min(1.2," + S + "['vocals'])"]),
        ("uView", [T("vzoom") + "*(1+" + T("vzj") + "*" + DVZ + "*" + _h(12.1) + "**2)", T("vrot") + "*2*(" + _h(6.3) + "-0.5)",
                   T("vpan") + "*" + DVZ + "*(" + _h(5.1) + "-0.5)+" + T("vdrx") + "*" + HUB + "['evolve']",
                   T("vpan") + "*" + DVZ + "*(" + _h(7.7) + "-0.5)+" + T("vdry") + "*" + HUB + "['evolve']"]),
        ("uView2", [T("pitch"), T("camh"), "abs(" + T("inv") + "-(1 if " + _h(2.2) + "<0.5 else 0))",
                    "1 if " + DESC + " else 0"]),     # w: Describe keeps the words readable (shade.frag)
    ])
    out1 = scene.op("out1")
    out1.nodeX, out1.nodeY = 1450, -400

    # ---- Describe: a caption card over the picture, only for takes that have a label ----
    LBL = "op('textlib').module.label(" + JS + ", " + TAKE + ")"
    label = scene.create(td.textTOP, "label")
    label.par.text.expr = LBL
    label.par.fontfile.expr = FONT(T("lfont"))
    label.par.outputresolution = "custom"
    label.par.resolutionw, label.par.resolutionh = 640, 132
    label.par.fontautosize = "nofit"
    label.par.fontsizex.expr = T("lsize")
    label.par.alignx, label.par.aligny = "left", "center"
    label.par.positionunit = "pixels"
    label.par.positionx = 18
    label.par.linespacing = 2
    one_bit = T("look") + "==3"
    label.par.fontcolorr.expr = "1 if " + one_bit + " else 0.93"
    label.par.fontcolorg.expr = "1 if " + one_bit + " else 0.89"
    label.par.fontcolorb.expr = "1 if " + one_bit + " else 0.80"
    label.par.bgcolorr.expr = "0 if " + one_bit + " else 0.035"
    label.par.bgcolorg.expr = "0 if " + one_bit + " else 0.055"
    label.par.bgcolorb.expr = "0 if " + one_bit + " else 0.075"
    label.par.bgalpha.expr = "1 if " + one_bit + " else 0.86"
    label.nodeX, label.nodeY = 1250, -700
    # 'auto' puts the card on the side away from the prop (the prop is on the right when seed < 0.5)
    RIGHT = "(" + Tv([{"l": 0, "r": 1, "auto": 2}[t["lside"]] for t in TAKES]) + "+(0 if " + SEED + "<0.5 else 1))%2==1"
    cap = scene.create(td.overTOP, "cap")
    _wire(cap, label, shade)
    cap.par.size = "input2"
    cap.par.prefit = "nativeres"
    cap.par.justifyv = "bottom"
    cap.par.justifyh.expr = "'right' if " + RIGHT + " else 'left'"
    cap.par.tunit = "pixels"
    cap.par.tx.expr = "-30 if " + RIGHT + " else 30"
    cap.par.ty = 26
    cap.nodeX, cap.nodeY = 1450, -700
    fin = scene.create(td.switchTOP, "fin")
    shade.outputConnectors[0].connect(fin)
    cap.outputConnectors[0].connect(fin)
    fin.par.index.expr = "1 if " + DESC + " and " + LBL + " else 0"
    fin.nodeX, fin.nodeY = 1450, -400
    out1.nodeX, out1.nodeY = 1650, -400
    fin.outputConnectors[0].connect(out1)
    fb_a.par.resetpulse.pulse()
    fb_t.par.resetpulse.pulse()
    return scene.path
