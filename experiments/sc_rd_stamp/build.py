# Builds /project1/sc_rd_stamp: Gray-Scott reaction-diffusion fed by stamped text,
# lit as wet enamel on a paper form. Idempotent: run it again to rebuild.
#
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open('<this file>', encoding='utf-8').read(), g); g['build']()
#
# see: experiments/sc_rd_stamp/NOTES.md (2026-11-10) for why each stage exists.
import td

SLUG = "sc_rd_stamp"
# Files are named only through the `paths` module the scaffold installs in the COMP
# (experiments/sw_hub/paths_module.py): every file parameter is an expression on it.
# see: experiments/sc_rd_stamp/NOTES.md "Assets" (2026-11-11) for what is used and the fallbacks.
ARCHIVO, BARLOW = "archivo", "barlow"           # names for mod.paths.font()

# Everything the scene says and shows that belongs to an asset pack: the stamped words,
# the papers, the models. build() reads it through scene_words(), so a pack that holds
# scenes/sc_rd_stamp/words.json replaces any of these names with its own (same shape).
# see: experiments/sc_rd_stamp/NOTES.md "Words and shapes" (2026-11-11)
DEFAULTS = {
    # What the framed stamp says. The takes pick from it by row number (`plist` in TAKES),
    # so a replacement needs the same number of rows.
    "PHRASES": [
        "REAL TIME.",                       # 0
        "DO NOT TOUCH",                     # 1
        "PLATE 07",                         # 2
        "THE SIGNAL:\nNOTHING STORED.",     # 3
        "NO RENDERING\nIN ADVANCE.",        # 4
        "HERE. NOW.\nREAL TIME.",           # 5
        "EVERY FRAME\nIS MADE NOW.",        # 6
        "THERE IS NO\nPLAYBACK.",           # 7
        "LOUD IS\nBRIGHT.",                 # 8
        "EXHIBIT 12-B",                     # 9
        "EVERYTHING\nIS LIVE",              # 10
        "OBJECT OF\nUNKNOWN USE",           # 11
        "LOOP. LOOP.\nLOOPLOOP.",           # 12
        "SOUND GOES IN.\nPICTURE OUT.",     # 13
        "LISTEN WITH\nYOUR EYES.",          # 14
        "FOUND, NOT MADE",                  # 15
        "SIGNAL IN\n....... LIVE",          # 16
        "SIXTY FRAMES EVERY\nSECOND",       # 17
        "FEEDBACK\nENGAGED...",             # 18
    ],
    # Short words for the tiled takes: 12 cells of the `atlas` (3 columns x 4 rows).
    "ATLAS": ["DO NOT\nTOUCH", "PLATE\n07", "LOOP", "NO\nPLAYBACK", "INK", "NOW.",
              "FRAME\n60", "NOT\nMADE", "SIGNAL", "IN.", "FEEDBACK", "OUT OF\nPHASE"],
    # What each take is called, in the order of TAKES: its name in the `takes` table (lower
    # case, no spaces) and the heading of its Describe caption.
    "LABELS": ["DESK", "MACRO", "FIELD", "APPROVALS", "CARBON", "TICKET", "RELIC"],
    # The papers on the `forms` Switch TOP, in this order (a take's `form` is a row here):
    # [flat sheet model whose picture is the page, share of the picture's height that fits
    # the 16:9 page (width / height * 9 / 16, at most 1)].
    "PAPERS": [["star_chart", 0.5625], ["blueprint", 0.75], ["ticket", 1.0]],
    # With no asset library a paper's picture is missing: each then shows a plain sheet
    # drawn here from text, 1024 x 1024 (the page shows the top of it).
    # [paper colour, print colour, headline, headline size, body]
    "BLANKS": [
        [[0.93, 0.90, 0.80], [0.20, 0.22, 0.26],
         "PLATE 07", 76,
         "CATALOGUE OF OBJECTS\n"
         "\n"
         "OBJECT  ____________________________      DATE  ______________\n"
         "\n"
         "ORIGIN  ____________________________      CASE  ______________\n"
         "\n"
         "USE  _______________________________________________________\n"
         "\n"
         "____________________________________________________________\n"
         "\n"
         "FOUND BY  __________________________      [   ]  INK HERE"],
        [[0.96, 0.95, 0.93], [0.10, 0.11, 0.14],
         "SHEET 12-B", 84,
         "MACHINE OF UNKNOWN USE, ELEVATION\n"
         "\n"
         "\n"
         "PART  ______________________________________________________\n"
         "\n"
         "DRAWN BY  __________________________________________________\n"
         "\n"
         "SCALE  _____________________________________________________\n"
         "\n"
         "[   ]  CHECKED         [   ]  TRACED          [   ]  FILED"],
        [[0.945, 0.718, 0.773], [0.60, 0.05, 0.12],
         "ADMIT\nONE", 104,
         "\n\n\n"
         "NO.  _________________________________\n"
         "\n"
         "[   ]  TODAY       [   ]  NOT TRANSFERABLE"],
    ],
    # The models the relic take wraps in ink; the seed picks one and all stay loaded.
    # [model, size (1 = its longest side is 1 unit), turn (degrees, added to the spin),
    #  lift (units up), 1 if it has a face wide enough to carry a word in Describe mode]
    "RELICS": [["amphora", 0.9, 0, 0.0, 1], ["pierced_stone", 0.9, 0, 0.0, 1], ["space_helmet", 1.0, 0, 0.0, 1]],
    # Numbers of a take that suit these papers and models and no others: take number (as
    # text) -> columns of TAKE_DEFAULTS. Applied on top of the take's row in TAKES.
    # Take 3: the blueprint is dark, and absorbing ink cannot be read on it.
    "TUNING": {"3": {"chalk": 1.0}},
}

SIM_W, SIM_H = 640, 360
SIM_PASSES = 10
NEAR_BLUR = 60   # px at sim resolution: how far from the letters the coral can ever get

# preset.json "as_processor" (written there by preset_words.py)
AS_PROCESSOR = ("Stamps the bright shapes of the picture into the simulation in place of the words, "
                "so its outlines stand up as gold, enamel or tar ink that follows the picture as it moves "
                "and grows and breaks up between kick drums; two takes also print the picture itself "
                "on the page underneath.")
# Describe mode with an Input: the second line of every take's caption
INPUT_CAPTION = "The bright shapes of another picture are the stamp. Each kick drum presses them again."

# One row per take. The cutter counts a scene's visits in the COMP's Take parameter;
# the row is Take % len(TAKES). Every value is a number except `plist`: the phrases the
# take may stamp (rows of DEFAULTS["PHRASES"]; Seed and, where psec is 1, the section pick one).
# Columns are read by the `tk` CHOP and reach the shaders as uniforms; nothing is loaded
# or re-wired at a cut.
TAKE_DEFAULTS = dict(
    cam=0,        # 0 desk dolly, 1 macro, 2 top-down, 3 raking
    smode=0,      # stamp: 0 one framed phrase, 1 tiles from the atlas, 2 scatter on kicks
    paper=0,      # 0 cream + print, 1 the form's own colours, 2 flat colour, 3 flat, no page edge
    form=0,       # row of DEFAULTS["PAPERS"]
    formv=0.5625, # share of the paper's height that fits the 16:9 page: filled in from PAPERS
    ink=-1,       # 0 gold leaf, 1 red enamel, 2 black tar, 3 white, 4 a different one per tile, -1 by section and seed
    cols=1, rows=1, frame=1,
    gshare=1.0,   # share of the tiles one kick presses
    jit=0.0,      # tile angle jitter (rad)
    alive=0.0,    # 1 lets the coral live anywhere, not just near the letters
    mbias=0.0,    # added to the kill margin outside the strokes
    sscale=1.0, spread=1.0, angs=1.0,   # stamp size, how far off centre, how crooked
    zoom=0.5,     # top-down: half the view height in page heights
    roll=0.0,
    dof=0.0, dofpx=0.0,
    light=1.0, expo=1.0, vig=0.42, onebit=0,
    imp=1.0,      # strength of the flat impression layer
    chalk=0.0,    # 1: the impression is a pale transfer, not absorbing ink (for a dark paper)
    pr=0.85, pg=0.77, pb=0.58,
    relic=0,      # 1 shows the chemistry wrapped on a library model instead of the page
    inpaper=0,    # 1: when the COMP's Input names a TOP, that picture is also printed on the page
    plist="0", psec=1,
    # Describe mode (the COMP's Describe toggle): `describe` is what the take stamps instead
    # of the pack's phrases (a list of phrases, or exactly 12 words for a take that uses the
    # atlas), `caption` the second line along the bottom of the frame (the first is
    # "REACTION-DIFFUSION / " and the take's label), and `dover` any numbers of the row
    # that differ while Describe is on (bigger words, so they can be read).
    describe=(), caption="", dover=None,
)
TEXT_COLS = ("plist", "describe", "caption", "dover")
TAKES = [
    # 0 DESK: the original picture. A tilted printed sheet, wide then dollying in; ink by section.
    dict(inpaper=1, plist="0 1 2 3 0 4 5 6 0 7 8 9 0 10 11 12 0 13 14 15",
         describe=["REACTION-\nDIFFUSION", "KICK DRUM =\nFRESH STAMP", "GRAY-SCOTT\nSIMULATION",
                   "THE LETTERS\nARE THE SEED", "ONE CHEMICAL\nEATS ANOTHER", "LOUD MUSIC\nSPREADS THE INK",
                   "SNARES BURN\nIT BACK", "10 SIM STEPS\nPER FRAME"],
         caption="Stamped letters seed a Gray-Scott simulation. Each kick drum presses them solid again."),
    # 1 MACRO: a few centimetres above the paper, shallow focus, the ink edge as landscape.
    dict(cam=1, dof=1.8, dofpx=16, light=1.15, vig=0.6, inpaper=1,
         plist="1 3 4 6 7 10 12 13 14",
         describe=["REACTION-\nDIFFUSION", "THE INK IS\nA HEIGHT MAP", "MACRO VIEW\nOF THE INK",
                   "SHALLOW\nFOCUS", "GRAY-SCOTT\nSIMULATION"],
         caption="The simulation is read as a height map, so the ink stands up and catches the light."),
    # 2 FIELD: no page. The whole frame is living letters, 1-bit black and white.
    dict(cam=2, smode=1, paper=3, ink=2, cols=3, rows=4, frame=0, gshare=0.45,
         alive=1.0, zoom=0.40, roll=0.0, onebit=1, imp=0.6, light=1.5, vig=0.15,
         pr=0.80, pg=0.80, pb=0.78,
         describe=["FEED", "KILL", "GROW", "WORMS", "SPOTS", "1-BIT",
                   "KICK", "INK", "GRAY-\nSCOTT", "640\nx 360", "SEED", "DITHER"],
         dover=dict(cols=3, rows=3, imp=1.0),
         caption="Short words dissolve into worms and spots, in 1-bit dither. Kick drums re-ink about half."),
    # 3 APPROVALS: the second paper from above, six small stamps in three inks; kicks re-stamp some.
    dict(cam=2, smode=1, paper=1, form=1, ink=4, cols=3, rows=2, frame=1,
         gshare=0.34, jit=0.5, zoom=0.56, roll=0.07, light=1.25, vig=0.3,
         describe=["KICK", "SNARE", "BASS", "HATS", "FEED", "KILL",
                   "SEED", "GROW", "BURN", "GLINT", "3 INKS", "STAMP"],
         caption="Six stamps in three inks, all one simulation. Each kick drum presses a third of them again."),
    # 4 CARBON: negative. White ink on carbon paper, raked from one end of an oversized phrase.
    dict(cam=3, paper=2, ink=3, frame=0, sscale=1.7, spread=0.4, angs=0.3,
         dof=1.5, dofpx=12, light=1.1, vig=0.5, pr=0.010, pg=0.013, pb=0.022,
         plist="12 3 16 13 7 18 4 6",
         describe=["WHITE INK\nON CARBON", "GRAY-SCOTT\nSIMULATION", "REACTION-\nDIFFUSION", "KICK DRUM =\nFRESH INK",
                   "THE SAME INK\nIN NEGATIVE"],
         dover=dict(sscale=1.25),
         caption="The same simulation as white ink on dark carbon paper, seen from one end of the phrase."),
    # 5 TICKET: the third paper from above; a small tar stamp lands somewhere new on every kick.
    dict(cam=2, smode=2, paper=1, form=2, ink=2, sscale=0.52,
         zoom=0.53, roll=0.12, light=1.2, vig=0.3, plist="1 9 15 2 8 10", psec=0,
         describe=["KICK = STAMP", "ONE PER KICK", "GRAY-SCOTT", "LIVING INK", "KICK DRUM"],
         caption="Every kick drum lands a new stamp. The black ink keeps growing; red marks are old stamps."),
    # 6 RELIC: no paper. The chemistry is the skin of a library model turning in the void.
    dict(relic=1, smode=1, cols=4, rows=5, frame=0, gshare=0.5, alive=1.0,
         vig=0.5, expo=1.1,
         describe=["TRI-\nPLANAR", "3D\nMODEL", "NO UVS", "GLSL\nMAT", "SAME\nINK", "GRAY-\nSCOTT",
                   "REACTION", "DIFFUSION", "KICK", "FEED", "KILL", "SKIN"],
         caption="The same living ink projected onto a 3D model from three sides. Kick drums re-ink it."),
]
TAKE_COLS = [k for k in TAKE_DEFAULTS if k not in TEXT_COLS]

# Describe mode: the printed sheet under the stamps, one per row of PAPERS. Each is
# (paper colour, print colour, headline, headline size, body).
SHEETS = [
    ((0.929, 0.890, 0.784), (0.13, 0.17, 0.23),
     "REACTION-DIFFUSION", 58,
     "Two simulated chemicals on a 640 x 360 grid. One feeds on the other, and both spread.\n"
     "\n"
     "1   The stamped letters are poured in as chemical.\n"
     "2   It grows outward from them as worms, beads and coral.\n"
     "3   Each kick drum presses the letters solid again.\n"
     "4   Snare hits burn the growth back.\n"
     "5   Louder, bassier music lets it spread further.\n"
     "\n"
     "Gray-Scott model, 10 steps per frame, in a GLSL shader. The pattern is lit as a height map."),
    ((0.961, 0.953, 0.929), (0.10, 0.11, 0.13),
     "SIX STAMPS, ONE SIMULATION", 46,
     "Every stamp is a seed for the same reaction-diffusion simulation.\n"
     "\n"
     "Gold leaf, red enamel and black tar are three ways of lighting one pattern.\n"
     "\n"
     "Each kick drum presses about a third of the stamps again.\n"
     "\n"
     "Snare hits burn the growth back. Hi-hats make the ink glint.\n"
     "\n"
     "Louder, bassier music lets the ink creep further from the letters."),
    ((0.945, 0.718, 0.773), (0.55, 0.05, 0.10),
     "ONE KICK, ONE STAMP", 58,
     "Every kick drum lands a new stamp in a new place.\n"
     "\n"
     "The black ink is a reaction-diffusion simulation:\n"
     "it keeps growing and breaking up after it lands.\n"
     "\n"
     "The red marks are where earlier stamps were pressed.\n"
     "\n"
     "Gray-Scott model on a 640 x 360 grid, 10 steps per frame."),
]


def _h(salt):
    # hash of the section and the shot seed, 0..1, as a parameter expression
    return ("((math.sin((op('hub')['section'] + op('tsel')['seed'] * 57.0) * %s) * 43758.5453) %% 1)" % salt)


def _tk(col):
    return "op('tk')['%s']" % col


def _here():
    # this experiment's folder: the repository is wherever the open project file is saved
    return td.project.folder.replace(chr(92), "/") + "/experiments/" + SLUG


def _shader(scene, name, ext="frag"):
    dat = scene.create(td.textDAT, name + "_" + ext)
    rel = "shaders/%s.%s" % (name, ext)
    dat.text = open(_here() + "/" + rel, encoding="utf-8").read()  # the file par loads a frame late
    dat.par.file.expr = "mod.paths.here(%r)" % rel
    dat.par.syncfile = True
    return dat


def _font(text, name, size=None):
    # The library face, or (no assets) TouchDesigner's default face. In place of Archivo
    # Black the default is set bold: the stamp needs heavy strokes for the chemistry to hold
    # on to. In place of Barlow Condensed it is set smaller, because it is much wider.
    have = "mod.paths.font(%r)" % name
    text.par.fontfile.expr = have
    if name == ARCHIVO:
        text.par.typeface.expr = "'Regular' if %s else 'Bold'" % have   # the Bold toggle does nothing here (2025.33230)
    if size is not None:
        if name == BARLOW:
            text.par.fontsizex.expr = "%r if %s else %r" % (size, have, round(size * 0.7))
        else:
            text.par.fontsizex = size


def _frag(scene, name, x, y):
    dat = _shader(scene, name)
    dat.nodeX, dat.nodeY = x, y - 130
    return dat


def _glsl(scene, name, x, y, w, h, fmt="rgba16float"):
    g = scene.create(td.glslTOP, name)
    # a new GLSL TOP arrives with docked default shader DATs; ours is the file-backed one.
    # <name>_info stays: it is where compile errors can be read.
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
    # indexed form: the appending form replaced input 0 on a GLSL TOP (2025.33230)
    for i, src in enumerate(srcs):
        src.outputConnectors[0].connect(dst.inputConnectors[i])


def _consts(chop, chans):
    chop.seq.const.numBlocks = len(chans)
    for i, (name, expr) in enumerate(chans):
        getattr(chop.par, "const%dname" % i).val = name
        p = getattr(chop.par, "const%dvalue" % i)
        if isinstance(expr, str):
            p.expr = expr
        else:
            p.val = expr


def _text(scene, name, x, y, w, h):
    text = scene.create(td.textTOP, name)
    _font(text, ARCHIVO)
    text.par.outputresolution = "custom"
    text.par.resolutionw, text.par.resolutionh = w, h
    text.par.fontautosize = "alwaysfit"
    text.par.fontsizex = 300
    text.par.alignx = "center"
    text.par.aligny = "center"
    text.par.linespacing = -8
    text.par.bgalpha = 1
    text.nodeX, text.nodeY = x, y
    return text


def _printed(scene, name, x, y, size, bg, ink, head, hsize, body, bsize, bfont, top, gap):
    # a sheet of paper drawn from text: a headline over body lines, on a flat colour
    sh = scene.create(td.textTOP, name + "_h")
    sb = scene.create(td.textTOP, name + "_b")
    for t, font, fsize, txt, ty in ((sh, ARCHIVO, hsize, head, top), (sb, bfont, bsize, body, top + gap)):
        t.par.outputresolution = "custom"
        t.par.resolutionw, t.par.resolutionh = size
        t.par.fontautosize = "none"
        _font(t, font, fsize)
        t.par.alignx = "left"
        t.par.aligny = "top"
        t.par.borderspace1, t.par.borderspace2 = 56, ty
        t.par.fontcolorr, t.par.fontcolorg, t.par.fontcolorb = ink
        t.par.wordwrap = True
        t.par.text = txt
    sh.par.bgcolorr, sh.par.bgcolorg, sh.par.bgcolorb = bg
    sh.par.bgalpha = 1
    sb.par.bgalpha = 0
    sb.par.linespacing = 9
    sheet = scene.create(td.overTOP, name)
    sb.outputConnectors[0].connect(sheet.inputConnectors[0])
    sh.outputConnectors[0].connect(sheet.inputConnectors[1])
    sh.nodeX, sh.nodeY = x, y
    sb.nodeX, sb.nodeY = x + 130, y
    sheet.nodeX, sheet.nodeY = x + 260, y
    return sheet


def take_rows(words):
    # TAKES as full rows for one set of words and shapes: defaults, the take, the pack's
    # tuning, the take's name and caption heading from its label, formv from its paper
    out = []
    for i, t in enumerate(TAKES):
        row = dict(TAKE_DEFAULTS, **t)
        row.update(words["TUNING"].get(str(i), {}))
        label = words["LABELS"][i]
        row["name"] = label.lower().replace(" ", "")
        row["caption"] = "REACTION-DIFFUSION / %s\n%s" % (label, row["caption"])
        row["formv"] = words["PAPERS"][int(row["form"])][1]
        out.append(row)
    return out


def build():
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, x=0, y=-700)
    paths = LIB["scene_paths"](scene)       # sees the COMP's Assets parameter
    W = LIB["scene_words"](scene, DEFAULTS)  # the pack's words and shapes, or the ones above
    PHRASES, ATLAS, PAPERS, RELICS = W["PHRASES"], W["ATLAS"], W["PAPERS"], W["RELICS"]

    # ---- the take: one row of TAKES, as channels ----
    takes = scene.create(td.tableDAT, "takes")
    takes.clear()
    takes.appendRow(["name"] + TAKE_COLS + ["plist", "atl", "caption"])
    rows = take_rows(W)
    for row in rows:
        takes.appendRow([row["name"]] + [row[c] for c in TAKE_COLS] + [row["plist"], 0, ""])
    # Describe mode reads the same table len(TAKES) rows further down: the take's numbers with
    # its `dover` applied, and its `describe` words in place of the pack's. A take with
    # phrases gets them appended to the `phrases` table (`plist` = their rows there); a take
    # that uses the atlas gets an atlas of its own (`atl` = which input of `atlsw`).
    dphrases, datlases = [], []
    for row in rows:
        row = dict(row, **(row["dover"] or {}))
        words = list(row["describe"])
        plist, atl = str(len(PHRASES)), 0
        if row["smode"] == 1:
            assert len(words) == len(ATLAS), row["name"]
            datlases.append(words)
            atl = len(datlases)
        else:
            plist = " ".join(str(len(PHRASES) + len(dphrases) + i) for i in range(len(words)))
            dphrases += words
        takes.appendRow([row["name"] + "_d"] + [row[c] for c in TAKE_COLS] + [plist, atl, row["caption"]])
    takes.nodeX, takes.nodeY = -400, 480

    # the two switches of the website round (2026-11-11), as channels: Describe, and whether
    # Input names a usable TOP (one outside this COMP: reading our own output is a cook loop)
    mode = scene.create(td.constantCHOP, "mode")
    mode.nodeX, mode.nodeY = -400, 620
    _consts(mode, [
        ("describe", "1 if parent().par.Describe else 0"),
        ("hasin", "(lambda p: 1 if p and op(p) is not None and op(p).isTOP"
                  " and not op(p).path.startswith(parent().path + '/') else 0)"
                  "(parent().par.Input.eval().strip())"),
    ])
    mdel = scene.create(td.delayCHOP, "mdel")
    mdel.par.delay = 0.05
    mode.outputConnectors[0].connect(mdel)
    mdel.nodeX, mdel.nodeY = -200, 620

    # take and seed without `age`, so what hangs off them cooks at a cut and not every frame
    tsel = scene.create(td.selectCHOP, "tsel")
    tsel.par.chop = "shot"
    tsel.par.channames = "take seed"
    tsel.nodeX, tsel.nodeY = -200, 330
    tdel = scene.create(td.delayCHOP, "tdel")
    tdel.par.delay = 0.05
    tsel.outputConnectors[0].connect(tdel)
    tdel.nodeX, tdel.nodeY = -50, 330

    row = "int(op('tsel')['take']) %% %d + 1 + %d * int(op('mode')['describe'])" % (len(TAKES), len(TAKES))
    tk = scene.create(td.constantCHOP, "tk")
    tk.nodeX, tk.nodeY = -200, 480
    _consts(tk, [(c, "float(op('takes')[%s, '%s'])" % (row, c)) for c in TAKE_COLS + ["atl"]])

    # ---- control: section change and kick, as inspectable channels ----
    sec = scene.create(td.selectCHOP, "sec")
    sec.par.chop = "hub"
    sec.par.channames = "section"
    sec.nodeX, sec.nodeY = -200, 200
    secdelay = scene.create(td.delayCHOP, "secdelay")
    secdelay.par.delay = 0.3
    sec.outputConnectors[0].connect(secdelay)
    secdelay.nodeX, secdelay.nodeY = -50, 200

    ctl = scene.create(td.constantCHOP, "ctl")
    ctl.nodeX, ctl.nodeY = 100, 200
    _consts(ctl, [
        # 1 for 0.3 s after every section change and for the first 0.22 s of a shot:
        # the phrase is held down, solid
        ("hold", "1 if abs(op('hub')['section'] - op('secdelay')['section']) > 0.5 or op('shot')['age'] < 0.22 else 0"),
        # 1 on the first frames of a shot (Take or Seed just changed) and after the scene was
        # not cooking: the loop then holds another take's ink or nothing, so inject starts
        # a clean sheet
        ("boot", "1 if absTime.frame - op('sim').cookAbsFrame > 3"
                 " or abs(op('tsel')['take'] - op('tdel')['take']) > 0.5"
                 " or abs(op('tsel')['seed'] - op('tdel')['seed']) > 1e-5"
                 " or abs(op('mode')['describe'] - op('mdel')['describe']) > 0.5"
                 " or abs(op('mode')['hasin'] - op('mdel')['hasin']) > 0.5 else 0"),
        # kick re-stamps, harder hits press harder
        ("kick", "min(1, max(0, op('hub')['hit_low'] - 0.06) * 2.6)"),
        ("ang", "(%s - 0.5) * 0.24 * %s" % (_h(12.9898), _tk("angs"))),
        ("ox", "(%s - 0.5) * 0.16 * %s" % (_h(39.346), _tk("spread"))),
        ("oy", "(%s - 0.5) * 0.14 * %s" % (_h(93.989), _tk("spread"))),
        ("scale", "(0.94 + 0.14 * %s) * %s" % (_h(5.631), _tk("sscale"))),
        # the living ink: the take's, or in turn by section and seed
        ("mat", "(int(op('hub')['section']) + int(op('tsel')['seed'] * 3)) %% 3 if %s < 0 else %s"
                % (_tk("ink"), _tk("ink"))),
    ])

    # which phrase: the take's list, picked by the seed and (if psec) the section
    pick = scene.create(td.constantCHOP, "pick")
    pick.nodeX, pick.nodeY = -50, 480
    _consts(pick, [("phrase",
                    "(lambda l: int(l[(int(op('sec')['section']) * int(%s) + int(op('tsel')['seed'] * 997)) %% len(l)]))"
                    "(op('takes')[%s, 'plist'].val.split())" % (_tk("psec"), row))])

    # ---- the stamp: phrase in a frame, or a sheet of tiles from the atlas ----
    phrases = scene.create(td.tableDAT, "phrases")
    phrases.clear()
    for p in PHRASES + dphrases:
        phrases.appendRow([p])
    phrases.nodeX, phrases.nodeY = -400, -300

    text = _text(scene, "phrase", -200, -300, 1152, 400)  # matches the stamp box inner aspect
    text.par.text.expr = "op('phrases')[int(op('pick')['phrase']) % op('phrases').numRows, 0].val"

    for i, word in enumerate(ATLAS):
        cell = _text(scene, "atl_%02d" % i, -600 + 130 * (i % 3), -500 - 110 * (i // 3), 426, 240)
        cell.par.text = word
    atlas = scene.create(td.layoutTOP, "atlas")
    atlas.par.tops = "atl_*"
    atlas.par.align = "gridrows"
    atlas.par.numcols = 3
    atlas.par.outputresolution = "custom"
    atlas.par.resolutionw, atlas.par.resolutionh = 1278, 960
    atlas.nodeX, atlas.nodeY = -200, -500

    # Describe mode: one more atlas per take that uses one, all drawn once at build time;
    # the toggle only moves this switch
    atlsw = scene.create(td.switchTOP, "atlsw")
    atlsw.nodeX, atlsw.nodeY = -50, -500
    atlas.outputConnectors[0].connect(atlsw)
    for a, words in enumerate(datlases):
        for i, word in enumerate(words):
            cell = _text(scene, "dat%d_%02d" % (a, i), -1100 + 130 * (i % 3), -500 - 110 * (i // 3) - 500 * a, 426, 240)
            cell.par.text = word
        datlas = scene.create(td.layoutTOP, "datlas%d" % a)
        datlas.par.tops = "dat%d_*" % a
        datlas.par.align = "gridrows"
        datlas.par.numcols = 3
        datlas.par.outputresolution = "custom"
        datlas.par.resolutionw, datlas.par.resolutionh = 1278, 960
        datlas.nodeX, datlas.nodeY = -700, -500 - 500 * a
        datlas.outputConnectors[0].connect(atlsw)
        datlas.cook(force=True)
    atlsw.par.index.expr = _tk("atl")

    # ---- Input: another scene's picture as the thing that is stamped ----
    # `inp` reads the TOP named by the COMP's Input parameter; `inmask` turns it into a stamp
    # mask (what is brighter than its surroundings). Behind a Switch, so with Input blank
    # none of this cooks.
    inp = scene.create(td.selectTOP, "inp")
    inp.par.top.expr = "parent().par.Input.eval().strip() if op('mode')['hasin'] > 0.5 else 'zero'"
    inp.par.outputresolution = "custom"
    inp.par.resolutionw, inp.par.resolutionh = 1280, 720
    inp.nodeX, inp.nodeY = -400, -1000
    inblur = scene.create(td.blurTOP, "inblur")
    inp.outputConnectors[0].connect(inblur)
    inblur.par.outputresolution = "custom"
    inblur.par.resolutionw, inblur.par.resolutionh = 320, 180
    inblur.par.size = 22
    inblur.par.dither = False
    inblur.nodeX, inblur.nodeY = -250, -1100
    inmask = _glsl(scene, "inmask", -100, -1000, 1280, 720, "rgba8fixed")
    _wire(inmask, inp, inblur)
    insw = scene.create(td.switchTOP, "insw")
    insw.nodeX, insw.nodeY = 50, -1000
    insw.par.index.expr = "op('mode')['hasin']"

    stamp = _glsl(scene, "stamp", 0, -300, 1280, 720, "rgba8fixed")
    _wire(stamp, text, atlsw, insw)
    _vecs(stamp, [
        ("uPose", ["op('ctl')['ang']", "op('ctl')['ox']", "op('ctl')['oy']", "op('ctl')['scale']"]),
        ("uBox", [0.64, 0.255, 0.022, 0.05]),
        ("uMode", [_tk("smode"), _tk("cols"), _tk("rows"), _tk("frame")]),
        ("uShot", ["op('tsel')['seed']", "op('hub')['hits_low']", _tk("gshare"), _tk("jit")]),
        ("uIn", ["op('mode')['hasin']", "op('mode')['describe']", 0, 0]),
    ])

    # ---- chemistry: feedback -> inject (once) -> sim (several passes) ----
    zero = scene.create(td.constantTOP, "zero")
    zero.par.colorr = zero.par.colorg = zero.par.colorb = 0
    zero.par.alpha = 0
    zero.par.outputresolution = "custom"
    zero.par.resolutionw, zero.par.resolutionh = SIM_W, SIM_H
    zero.par.format = "rgba16float"
    zero.nodeX, zero.nodeY = 0, 0
    zero.outputConnectors[0].connect(insw)      # index 0: no input
    inmask.outputConnectors[0].connect(insw)    # index 1

    fb = scene.create(td.feedbackTOP, "fb")
    fb.par.format = "rgba16float"
    zero.outputConnectors[0].connect(fb)
    fb.nodeX, fb.nodeY = 200, 0

    inject = _glsl(scene, "inject", 400, 0, SIM_W, SIM_H)
    _wire(inject, fb, stamp)
    _vecs(inject, [
        ("uStamp", ["op('ctl')['hold']", "op('ctl')['kick']", 0.985, 0.9982]),
        # y: with an Input the flat impression is re-inked every frame, so it follows the moving
        # picture (not on the scatter take, whose old impressions are the point of the take)
        ("uBoot", ["op('ctl')['boot']", "op('mode')['hasin'] if %s < 1.5 else 0" % _tk("smode"), 0, 0]),
    ])

    # a wide blur of the stamp is a cheap distance-to-letters field: sim.frag uses it to
    # keep the coral within reach of the phrase
    near = scene.create(td.blurTOP, "near")
    stamp.outputConnectors[0].connect(near)
    near.par.outputresolution = "custom"
    near.par.resolutionw, near.par.resolutionh = SIM_W, SIM_H
    near.par.size = NEAR_BLUR
    near.par.format = "rgba16float"
    near.par.dither = False
    near.nodeX, near.nodeY = 400, -300

    sim = _glsl(scene, "sim", 600, 0, SIM_W, SIM_H)
    sim.par.npasses = SIM_PASSES
    _wire(sim, inject, near, stamp)
    _vecs(sim, [
        ("uAudio", ["op('hub')['energy']", "op('hub')['bass']", "op('hub')['vocals']", "op('hub')['hit_mid']"]),
        ("uDrift", ["op('hub')['evolve']", "op('ctl')['hold']", "op('ctl')['kick']", 0]),
        ("uZone", [_tk("alive"), _tk("mbias"), 0, 0]),
    ])
    fb.par.top = sim.name
    fb.par.resetpulse.pulse()

    # ---- light it ----
    hmap = scene.create(td.blurTOP, "hmap")
    sim.outputConnectors[0].connect(hmap)
    hmap.par.outputresolution = "custom"
    hmap.par.resolutionw, hmap.par.resolutionh = 1280, 720
    hmap.par.size = 7   # 3 left the 640-wide texels visible as glitter on the beads (captures/r5_a.png)
    hmap.par.format = "rgba16float"
    hmap.par.dither = False   # dither noise in the height showed as dotted contour lines in every reflection
    hmap.nodeX, hmap.nodeY = 800, 100

    # every paper stays loaded; the take only moves the switch
    forms = scene.create(td.switchTOP, "forms")
    forms.nodeX, forms.nodeY = 800, -300
    for i, (slug, _share) in enumerate(PAPERS):
        form = scene.create(td.moviefileinTOP, "form%d" % i)
        form.par.file.expr = "mod.paths.model_texture(%r)" % slug
        form.nodeX, form.nodeY = 600, -300 - 110 * i
        # no library: `formsw` shows the plain form drawn from text instead, and the
        # Movie File In (which has no file) is never cooked
        bg, ink, head, hsize, body = W["BLANKS"][i]
        blank = _printed(scene, "blank%d" % i, -1500, -300 - 110 * i, (1024, 1024),
                         bg, ink, head, hsize, body, 22, BARLOW, 60, hsize * 1.25)
        formsw = scene.create(td.switchTOP, "formsw%d" % i)
        form.outputConnectors[0].connect(formsw)
        blank.outputConnectors[0].connect(formsw)
        formsw.par.index.expr = "0 if mod.paths.model_texture(%r) else 1" % slug
        formsw.nodeX, formsw.nodeY = 700, -300 - 110 * i
        formsw.outputConnectors[0].connect(forms)
        (form if paths.model_texture(slug) else blank).cook(force=True)
    # Describe mode: inputs 3..5 are printed sheets of explanation, one per paper, drawn once
    for i, (bg, ink, head, hsize, body) in enumerate(SHEETS):
        sheet = _printed(scene, "sheet%d" % i, 200, -700 - 110 * i, (1280, 720),
                         bg, ink, head, hsize, body, 31, BARLOW, 34, 84)
        sheet.outputConnectors[0].connect(forms)
        sheet.cook(force=True)
    # input 6: the Input picture, for the takes that print it on the page
    inp.outputConnectors[0].connect(forms)
    inpaper = "(op('mode')['hasin'] > 0.5 and op('tk')['inpaper'] > 0.5)"
    forms.par.index.expr = ("6 if %s else (3 + %s if op('mode')['describe'] > 0.5 else %s)"
                            % (inpaper, _tk("form"), _tk("form")))
    # a sheet or an input picture is shown whole and in its own colours
    whole = "(op('mode')['describe'] > 0.5 or %s)" % inpaper
    paper_mode = "1 if %s < 0.5 and %s else %s" % (_tk("paper"), whole, _tk("paper"))
    formv = "1.0 if %s else %s" % (whole, _tk("formv"))

    shade = _glsl(scene, "shade", 1000, 0, 1280, 720)
    _wire(shade, hmap, stamp, forms)  # a GLSL TOP has 3 input connectors
    _vecs(shade, [
        ("uCam", ["op('hub')['evolve']", "op('hub')['beat_pos']", "op('hub')['bar_pulse']", "op('hub')['pulse']"]),
        ("uHit", ["op('hub')['hit_low']", "op('hub')['hit_mid']", "op('hub')['hit_high']", "op('hub')['energy']"]),
        ("uSec", ["op('hub')['section']", "op('ctl')['kick']", "op('ctl')['hold']", "op('ctl')['mat']"]),
        ("uPose", ["op('ctl')['ang']", "op('ctl')['ox']", "op('ctl')['oy']", "op('hub')['section_pos']"]),
        ("uTake", [_tk("cam"), _tk("smode"), paper_mode, formv]),
        ("uShot", ["op('tsel')['seed']", "op('shot')['age']", _tk("cols"), _tk("rows")]),
        ("uPaper", [_tk("pr"), _tk("pg"), _tk("pb"), _tk("frame")]),
        ("uCamP", [_tk("zoom"), _tk("roll"), _tk("dof"), _tk("light")]),
        ("uInk", [_tk("imp"), _tk("chalk"), 0, 0]),
    ])

    # ---- the "relic" take: the same chemistry as the skin of a library model ----
    rv = _shader(scene, "relic", "vert")
    rf = _shader(scene, "relic", "frag")
    rv.nodeX, rv.nodeY = 1000, 270
    rf.nodeX, rf.nodeY = 1130, 270
    skinmat = scene.create(td.glslMAT, "skinmat")
    skinmat.par.vdat = rv.name
    skinmat.par.pdat = rf.name
    skinmat.seq.sampler.numBlocks = 1
    skinmat.par.sampler0name = "sSim"
    skinmat.par.sampler0top = hmap.path
    skinmat.par.sampler0extendu = "mirror"
    skinmat.par.sampler0extendv = "mirror"
    _vecs(skinmat, [
        ("uInk", ["op('ctl')['mat']", "op('ctl')['kick']", "op('hub')['hit_high']", "op('hub')['pulse']"]),
        ("uLight", ["op('hub')['beat_pos']", "op('hub')['evolve']", "op('tsel')['seed']",
                    "max(op('mode')['describe'], op('mode')['hasin'])"]),
    ])
    skinmat.nodeX, skinmat.nodeY = 1200, 400
    # Describe mode leaves out a model with no face wide enough to carry a word (the last
    # column of RELICS; captures/describe_6.png before this: fragments on a thin handle)
    wide = tuple(i for i, r in enumerate(RELICS) if r[4]) or tuple(range(len(RELICS)))
    which = ("(%r[int(op('tsel')['seed'] * 997) %% %d] if op('mode')['describe'] > 0.5"
             " else int(op('tsel')['seed'] * 997) %% %d)" % (wide, len(wide), len(RELICS)))
    arrive = "math.exp(-op('shot')['age'] * 6.0)"
    for i, (slug, size, turn, lift, _wide) in enumerate(RELICS):
        geo = scene.create(td.geometryCOMP, "relic%d" % i)
        for child in geo.children:
            child.destroy()
        mesh = geo.create(td.fileinPOP, "mesh")
        mesh.par.file.expr = "mod.paths.model_file(%r)" % slug
        mesh.render = False
        mesh.display = False
        mesh.cook(force=True)   # a model hidden by `render` loads on first show: a 25-50 ms hitch at the cut
        # A library model is centred with its longest side 1 unit; the stand-in (no library:
        # TouchDesigner's teapot) is not, so `fit` brings whatever was loaded to that size.
        # For a library model it does nothing.
        lib = "mod.paths.have('models/%s/model.obj')" % slug
        fit = geo.create(td.transformPOP, "fit")
        mesh.outputConnectors[0].connect(fit)
        for axis in "xyz":
            getattr(fit.par, "alignt" + axis).expr = "'off' if %s else 'origin'" % lib
        fit.par.alignscale.expr = "'peraxis' if %s else 'unity'" % lib   # per axis, with every axis off, is no scale
        # the teapot is squat (1 x 0.47 x 0.62 at unit size), so it is shown a little larger
        fit.par.alignxformorder = "aligntransform"
        fit.par.scale.expr = "1 if %s else 1.4" % lib
        fit.render = True
        fit.display = True
        fit.nodeX = 200
        fit.cook(force=True)
        geo.par.material = skinmat.path   # absolute: a relative path silently falls back to grey
        geo.par.render.expr = "%s == %d and op('tk')['relic'] > 0.5" % (which, i)
        geo.par.ry.expr = "%r + op('hub')['beat_pos'] * 11.25 + op('tsel')['seed'] * 360 + 200 * %s" % (turn, arrive)
        geo.par.rx.expr = "10 * math.sin(op('hub')['evolve'] * 0.35)"
        geo.par.ty = lift
        geo.par.scale.expr = "%r * (1.0 + 0.07 * op('ctl')['kick'])" % size
        geo.nodeX, geo.nodeY = 1000 + 130 * i, 560
    mcam = scene.create(td.cameraCOMP, "mcam")
    # fov is horizontal: 30 degrees at 3.5 units shows 1.9 x 1.05 units. The seed puts the
    # model left or right of centre and nearer or further (b6x.png: at 1.75 units it was a wall)
    mcam.par.fov = 30
    mcam.par.tz.expr = "3.5 + 1.0 * ((op('tsel')['seed'] * 31) %% 1) + 2.5 * %s" % arrive
    mcam.par.tx.expr = "0.42 * (1 if (op('tsel')['seed'] * 17) % 1 > 0.5 else -1)"
    mcam.nodeX, mcam.nodeY = 1400, 560
    mrend = scene.create(td.renderTOP, "mrend")
    mrend.par.camera = mcam.name
    mrend.par.geometry = "relic*"
    mrend.par.outputresolution = "custom"
    mrend.par.resolutionw, mrend.par.resolutionh = 1280, 720
    mrend.par.format = "rgba16float"
    mrend.par.bgcolora = 0
    mrend.nodeX, mrend.nodeY = 1400, 400
    mbg = _glsl(scene, "mbg", 1600, 400, 1280, 720)
    mrend.outputConnectors[0].connect(mbg)
    _vecs(mbg, [("uBg", ["op('hub')['evolve']", "op('ctl')['kick']", "op('tsel')['seed']", "op('hub')['pulse']"])])

    # the picture is the page or the relic; a Switch TOP cooks only the input it shows
    pic = scene.create(td.switchTOP, "pic")
    shade.outputConnectors[0].connect(pic)
    mbg.outputConnectors[0].connect(pic)
    pic.par.index.expr = _tk("relic")
    pic.nodeX, pic.nodeY = 1200, 0
    # the relic's shaders compile the first time it is drawn (14 ms measured at the first
    # cut to it): draw it once now, a few frames after the build
    td.run("o = op('%s'); o.cook(force=True) if o else None" % mbg.path, delayFrames=10)

    # ---- finish: glow from the HDR highlights only, then vignette and tonemap ----
    bright = _glsl(scene, "bright", 1200, -200, 320, 180)
    pic.outputConnectors[0].connect(bright)
    glow = scene.create(td.blurTOP, "glow")
    bright.outputConnectors[0].connect(glow)
    glow.par.size = 9
    glow.par.format = "rgba16float"
    glow.par.dither = False
    glow.nodeX, glow.nodeY = 1400, -200
    grade = _glsl(scene, "grade", 1600, 0, 1280, 720, "rgba8fixed")
    _wire(grade, pic, glow)
    _vecs(grade, [
        ("uGrade", [0.42, "op('ctl')['kick']", "op('hub')['hit_high']", "op('shot')['age']"]),
        ("uFx", [_tk("dofpx"), _tk("onebit"), _tk("expo"), _tk("vig")]),
    ])
    # ---- Describe mode: a caption along the bottom saying what this take is ----
    # `fin` passes `grade` straight through when Describe is off, so `label` never cooks then
    captext = scene.create(td.textTOP, "captext")
    captext.par.outputresolution = "custom"
    captext.par.resolutionw, captext.par.resolutionh = 1280, 720
    captext.par.fontautosize = "none"
    _font(captext, BARLOW, 27)
    captext.par.alignx = "left"
    captext.par.aligny = "bottom"
    captext.par.borderspace1, captext.par.borderspace2 = 40, 22
    captext.par.linespacing = 4
    captext.par.bgalpha = 0
    # with an Input the take's own second line would be untrue (no letters are stamped)
    captext.par.text.expr = ("(lambda c: c.split(chr(10))[0] + ' + INPUT' + chr(10) + %r"
                             " if op('mode')['hasin'] > 0.5 else c)(op('takes')[%s, 'caption'].val)"
                             % (INPUT_CAPTION, row))
    captext.nodeX, captext.nodeY = 1600, -200
    label = _glsl(scene, "label", 1750, -100, 1280, 720, "rgba8fixed")
    _wire(label, grade, captext)
    fin = scene.create(td.switchTOP, "fin")
    grade.outputConnectors[0].connect(fin)
    label.outputConnectors[0].connect(fin)
    fin.par.index.expr = "op('mode')['describe']"
    fin.nodeX, fin.nodeY = 1900, 0
    scene.op("out1").nodeX = 2050

    fin.outputConnectors[0].connect(scene.op("out1"))
    # the caption and input-mask shaders compile on their first cook (6.5 ms read on `label`
    # at the first Describe toggle after a build): draw each once now, like the relic
    for o in (label, inmask):
        td.run("o = op('%s'); o.cook(force=True) if o else None" % o.path, delayFrames=12)
    return scene.path
