# Builds /project1/id_title_card: a title card. A phrase from a control is set on a
# 12-column grid, a different way on every take (typeset.py: poster, bleed, credit,
# system, rows), each in two or three colours and at most two type sizes. The layout
# is a table (the Script DAT `runs`): one row per line of lettering with its face,
# size, letterspacing, position and the box its ink fills. Eight Text TOPs draw the
# rows and shaders/card.frag composes them, bringing lines in and out by masks, wipes
# and cuts counted in beats of the music. Every take has different words.
#
# Run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/id_title_card/build.py', encoding='utf-8').read(), g)
#     g['build']()
import td

SLUG = "id_title_card"
RUNS = 8

# take name (the order of typeset.TAKES), finish preset (experiments/sw_finish/presets.json)
FINISH = ("clean", "clean", "film35", "clean", "clean")

DRIVER = '''def onFrameStart(frame):
    if parent().par.Preview.eval():
        op('out1').cook(force=True)
    return
'''

# Beats are counted from the bar line (four to a bar), so a cycle starts on a bar. The feed's own
# beat count is not used: it need not start on a downbeat.
BEAT = "(op('hub')['bar_pos'] * 4 if op('hub').numChans else absTime.seconds * 2)"


def build():
    repo = td.project.folder.replace(chr(92), "/")
    LIB = {"op": op}  # noqa: F821
    exec(open(repo + "/experiments/sw_images/image_lib.py", encoding="utf-8").read(), LIB)
    SCENE = {"op": op}  # noqa: F821
    exec(open(repo + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), SCENE)
    root = op("/project1")  # noqa: F821
    old = root.op(SLUG)
    if old:
        old.destroy()
    c = root.create(td.baseCOMP, SLUG)
    c.nodeX, c.nodeY = 1050, -1700
    SCENE["add_paths"](c)

    page = c.appendCustomPage("Controls")
    page.appendStr("Title", label="Titles (one per take, separated by |)")[0].val = (
        "OPEN STUDIO|NIGHT SIGNAL|THE LONG EXPOSURE|FIELD NOTES|LOUDER COLOURS"
    )
    page.appendStr("Line", label="Small Lines (up to three, separated by /)")[0].val = "REEL 04 / A LIVE SESSION / 2026"
    take = page.appendInt("Take", label="Take (which layout and which title)")[0]
    take.val = 0
    take.normMin, take.normMax = 0, 4
    cycle = page.appendInt("Cycle", label="Bars Until The Card Clears And Builds Again (0 = hold still)")[0]
    cycle.val = 4
    cycle.normMin, cycle.normMax = 0, 8
    LIB["slider"](page, "Margin", "Margin (px, all four sides)", 64.0, 160.0, 16.0)
    LIB["slider"](page, "Tracking", "Small Line Letter Spacing (em)", 0.16, 0.5)
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = True

    for name in ("typeset", "layout_td"):
        dat = c.create(td.textDAT, name)
        dat.par.file.expr = "mod.paths.here('%s.py')" % name
        dat.par.syncfile = True
        dat.par.loadonstartpulse.pulse()

    hub = c.create(td.selectCHOP, "hub")
    hub.par.chop = "/project1/sw_hub/feed"

    # one small Text TOP per face, only to ask how wide a text comes out (kerning included)
    for n, key in enumerate(("bold", "medium", "system")):
        m = c.create(td.textTOP, "m_" + key)
        m.par.fontfile.expr = "mod('layout_td').font_path('%s')" % key
        m.par.fontautosize = "nofit"
        m.par.fontsizexunit = "pixels"
        m.par.fontsizex = 100
        m.par.wordwrap = False
        m.par.text = ""
        m.par.outputresolution = "custom"
        m.par.resolutionw, m.par.resolutionh = 16, 16
        m.nodeX, m.nodeY = -400, 320 - 110 * n

    runs = c.create(td.scriptDAT, "runs")
    for d in list(runs.docked):
        d.destroy()
    runs.par.callbacks = "layout_td"
    runs.nodeX, runs.nodeY = -200, 460

    mo = c.create(td.constantCHOP, "motion")
    mo.seq.const.numBlocks = 5
    rows = [
        ("cb", "mod('typeset').cycle_beats(%s, parent().par.Cycle)" % BEAT),
        ("total", "4 * max(0, parent().par.Cycle)"),
        ("beat", "%s if parent().par.Cycle > 0 else 0" % BEAT),
        ("m", "mod('typeset').motion(mod('typeset').take_name(parent().par.Take), %s, parent().par.Cycle, float(op('runs')[1, 'span']))" % BEAT),
        ("chars", "mod('typeset').typed_chars(mod('typeset').cycle_beats(%s, parent().par.Cycle), 4 * max(0, parent().par.Cycle))" % BEAT),
    ]
    for i, (name, expr) in enumerate(rows):
        setattr(mo.par, "const%dname" % i, name)
        getattr(mo.par, "const%dvalue" % i).expr = expr
    mo.nodeX, mo.nodeY = -400, -100

    # one Text TOP per run, drawn full frame where the layout puts it. A run that does not
    # move never looks at `motion`, so it is drawn once and not again.
    tops = []
    for i in range(RUNS):
        n = i + 1
        cell = "op('runs')[%d, '%%s']" % n
        t = c.create(td.textTOP, "run%d" % i)
        t.par.text.expr = ("(lambda t, s: t if s < 0 else mod('typeset').typed(t, s, op('motion')['chars']))(%s.val, int(%s))"
                           % (cell % "text", cell % "typeon"))
        t.par.fontfile.expr = "mod('layout_td').font_path(%s.val)" % (cell % "font")
        t.par.fontautosize = "nofit"
        t.par.wordwrap = False
        t.par.fontsizexunit = "pixels"
        t.par.fontsizex.expr = "max(1, float(%s))" % (cell % "size")
        t.par.trackingx.expr = "float(%s) + (float(%s) and float(%s) * op('motion')['m'])" % (cell % "track", cell % "dtr", cell % "dtr")
        t.par.positionunit = "pixels"
        t.par.positionx.expr = "float(%s) + (float(%s) and float(%s) * op('motion')['m'])" % (cell % "px", cell % "dx", cell % "dx")
        t.par.positiony.expr = "float(%s)" % (cell % "py")
        t.par.alignx, t.par.aligny = "left", "bottom"
        t.par.outputresolution = "custom"
        t.par.resolutionw, t.par.resolutionh = 1280, 720
        t.par.bgalpha = 0
        t.nodeX, t.nodeY = 0, 460 - 110 * i
        tops.append(t)

    card = LIB["glsl_top"](c, "card", SLUG, "shaders/card.frag", fmt="rgba16float")
    card.par.tops = " ".join(t.name for t in tops)   # run i is input i
    NAME = "mod('typeset').take_name(parent().par.Take)"
    vecs = [
        ("uCard", ["int(parent().par.Take) % 5", "op('motion')['cb']", "op('motion')['total']", "op('motion')['beat']"]),
        ("uGrid", ["parent().par.Margin", "0", "0", "0"]),
    ]
    for k in range(3):
        vecs.append(("uCol%d" % k, ["mod('typeset').PALETTES[%s][%d][%d]" % (NAME, k, ch) for ch in range(3)] + ["1"]))
    for i in range(RUNS):
        vecs.append(("uRect%d" % i, ["float(op('runs')[%d, '%s'])" % (i + 1, col) for col in ("x0", "y0", "x1", "y1")]))
    for i in range(RUNS):
        vecs.append(("uRole%d" % i, ["float(op('runs')[%d, '%s'])" % (i + 1, col) for col in ("kind", "col", "order", "line")]))
    LIB["uniforms"](card, vecs)

    g = {"op": op, "td": td, "__name__": "build"}  # noqa: F821
    exec(open(repo + "/experiments/sw_finish/build.py", encoding="utf-8").read(), g)
    f = op(g["build"](name="finish", parent=c.path, preset=FINISH[0]))  # noqa: F821
    card.outputConnectors[0].connect(f.inputConnectors[0])
    f.par.Preset.expr = "%r[int(parent().par.Take) %% %d]" % (FINISH, len(FINISH))
    f.par.Preview.expr = "parent().par.Preview"
    out1 = c.create(td.outTOP, "out1")
    f.outputConnectors[0].connect(out1)

    drv = c.create(td.executeDAT, "cook_driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True
    for i, o in enumerate([card, f, out1]):
        o.nodeX, o.nodeY = 250 + i * 200, 0
    hub.nodeX, hub.nodeY = -400, -200
    return c.path
