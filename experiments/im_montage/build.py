# Builds /project1/im_montage: the cut-outs of a prepared image set as paper cards
# in front of a printed two-colour ground, moved by the music. Eight takes, each a
# different layout, ground and finish (see layouts.py, which holds all the motion).
#
# Prepare a set first, outside TouchDesigner:
#     python tools/imageprep/prepare.py <folder of pictures>
# then run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/im_montage/build.py', encoding='utf-8').read(), g)
#     g['build'](folder='image_sets/<name>')
import td

SLUG = "im_montage"
CARDS = 12
DEFAULT_SET = "assets/image_sets/generated_cutouts"  # tools/imageprep/prepare.py <stills> --cutouts-from <cut-outs>
MIN_COVER = 0.03  # a cut-out that covers less of its picture than this is left out

LAYOUT = '''# Where every card is on this frame. The motion itself is in layouts.py.
CARD = ("x", "y", "z", "s", "sx", "rz", "pic")
ONE = ("camx", "camy", "camz", "roll", "mode", "ar", "ag", "ab", "br", "bg", "bb", "beat", "kick", "bass", "finish")


def onCook(scriptOp):
    comp = parent()
    lay = op('layouts').module
    feed = op('hub')
    react = comp.par.React.eval()
    f = {}
    for name in lay.FEED:
        ch = feed[name] if feed is not None else None
        v = ch.eval() if ch is not None else 0.0
        if name not in ("beat_pos", "bar_pos", "hits_low"):
            v *= react
        f[name] = v
    shot = op('shot')
    out = lay.frame(shot['take'].eval(), shot['seed'].eval(), shot['age'].eval(), f, %d)
    table = op('table')
    good = [r - 1 for r in range(1, table.numRows) if float(table[r, 'cutout_cover'].val or 0) >= %s] or [0]
    size = comp.par.Size.eval()
    dealer = comp.fetch('deal', None, search=False)
    if dealer is None:
        dealer = lay.new_deal()
    dealt = lay.deal(dealer, shot['take'].eval(), [c["pic"] for c in out["cards"]], len(good))
    comp.store('deal', dealer)
    scriptOp.clear()
    scriptOp.isTimeSlice = False
    scriptOp.numSamples = len(out["cards"])
    rows = {k: [] for k in CARD}
    for c, d in zip(out["cards"], dealt):
        pic = good[d]
        aspect = float(table[pic + 1, 'aspect'].val or 1) if table.numRows > 1 else 1.0
        rows["x"].append(c["x"]); rows["y"].append(c["y"]); rows["z"].append(c["z"])
        rows["s"].append(c["s"] * size); rows["sx"].append(c["s"] * size * aspect)
        rows["rz"].append(c["rz"]); rows["pic"].append(pic)
    for k in CARD:
        scriptOp.appendChan(k).vals = rows[k]
    cam, g = out["cam"], out["ground"]
    one = [cam["x"], cam["y"], cam["z"], cam["roll"], g["mode"], *g["a"], *g["b"], g["beat"], g["kick"], g["bass"], out["finish"]]
    for k, v in zip(ONE, one):
        scriptOp.appendChan(k).vals = [v] * scriptOp.numSamples
    return
''' % (CARDS, MIN_COVER)


def build(folder=""):
    LIB = {"op": op}  # noqa: F821
    exec(open(td.project.folder.replace(chr(92), "/") + "/experiments/sw_images/image_lib.py", encoding="utf-8").read(), LIB)
    c, page = LIB["new_comp"](SLUG, folder, x=850, y=-1700, default=DEFAULT_SET)
    # the cutter (or you) sets these before a shot, as it does for a hub scene
    page.appendInt("Take", label="Take (which layout, 0-7)")[0].val = 0
    page.appendFloat("Seed", label="Shot Seed (0-1: which pictures)")[0].val = 0
    page.appendFloat("Shotstart", label="Shot Start (absTime s)")[0].val = 0
    LIB["slider"](page, "React", "How Hard It Follows The Music", 1.0, 2.0)
    LIB["slider"](page, "Size", "Card Size", 1.0, 2.0, 0.3)
    LIB["slider"](page, "Rays", "Sunburst Rays", 14, 40, 2)
    page.appendToggle("Finishtake", label="Finish Follows The Take")[0].val = True

    hub = c.create(td.selectCHOP, "hub")
    hub.par.chop = "/project1/sw_hub/feed"
    shot = c.create(td.constantCHOP, "shot")
    shot.par.name0, shot.par.name1, shot.par.name2 = "take", "seed", "age"
    shot.par.value0.expr = "parent().par.Take"
    shot.par.value1.expr = "parent().par.Seed"
    shot.par.value2.expr = "max(0, absTime.seconds - parent().par.Shotstart)"
    layouts = c.create(td.textDAT, "layouts")
    layouts.par.file.expr = "mod.paths.experiment('%s', 'layouts.py')" % SLUG
    layouts.par.syncfile = True
    layouts.par.loadonstartpulse.pulse()
    lay = c.create(td.scriptCHOP, "lay")
    for d in list(lay.docked):
        d.destroy()
    code = c.create(td.textDAT, "lay_code")
    code.text = LAYOUT
    lay.par.callbacks = code.name
    hub.outputConnectors[0].connect(lay)
    shot.outputConnectors[0].connect(lay)
    hub.nodeX, hub.nodeY = -400, 60
    shot.nodeX, shot.nodeY = -400, -40
    layouts.nodeX, layouts.nodeY = -250, -160
    code.nodeX, code.nodeY = -250, -260
    lay.nodeX, lay.nodeY = -250, 0

    ground = LIB["glsl_top"](c, "ground", SLUG, "shaders/ground.frag", fmt="rgba8fixed")
    L = "op('lay')['%s'][0]"
    LIB["uniforms"](ground, [
        ("uA", [L % "ar", L % "ag", L % "ab", L % "mode"]),
        ("uB", [L % "br", L % "bg", L % "bb", L % "beat"]),
        ("uAim", [L % "kick", L % "bass", "absTime.seconds % 3600", "parent().par.Rays"]),
    ])

    # every cut-out of the set stays loaded, so a card can change its picture on a beat without a hitch
    table = c.op("table")
    count = max(1, table.numRows - 1)
    for i in range(count):
        tex = LIB["movie"](c, "pic%d" % i, "mod.imset.path(%d, 'cutout')" % i)
        tex.nodeX, tex.nodeY = 0 + 130 * (i % 5), 700 + 110 * (i // 5)
        tex.cook(force=True)  # load now, not on the beat that first shows it

    cards = []
    for i in range(CARDS):
        mat = c.create(td.constantMAT, "mat%d" % i)
        mat.par.colormap.expr = "'pic%%d' %% int(op('lay')['pic'][%d])" % i
        mat.par.alphatest = True          # hard paper edges, and no sorting problems
        mat.par.alphafunc = "greater"
        mat.par.alphathreshold = 0.5
        geo = c.create(td.geometryCOMP, "card%d" % i)
        for child in geo.children:
            child.destroy()
        rect = geo.create(td.rectangleSOP, "rect")
        rect.par.sizex, rect.par.sizey = 1, 1
        rect.par.texture = "face"
        rect.render = True
        rect.display = True
        geo.par.material = mat.path
        for par, chan in (("tx", "x"), ("ty", "y"), ("tz", "z"), ("rz", "rz"), ("sx", "sx"), ("sy", "s")):
            getattr(geo.par, par).expr = "op('lay')['%s'][%d]" % (chan, i)
        mat.nodeX, mat.nodeY = 170, 300 - i * 110
        geo.nodeX, geo.nodeY = 340, 300 - i * 110
        cards.append(geo)

    cam = c.create(td.cameraCOMP, "cam")
    for par, chan in (("tx", "camx"), ("ty", "camy"), ("tz", "camz"), ("rz", "roll")):
        getattr(cam.par, par).expr = L % chan
    cam.par.fov = 46
    cam.par.near, cam.par.far = 0.05, 60

    render = c.create(td.renderTOP, "render")
    render.par.camera = cam.path
    render.par.geometry = " ".join(g.path for g in cards)
    render.par.lights = ""
    render.par.outputresolution = "custom"
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.bgcolorr, render.par.bgcolorg, render.par.bgcolorb, render.par.bgcolora = 0, 0, 0, 0

    over = c.create(td.overTOP, "over")
    render.outputConnectors[0].connect(over.inputConnectors[0])
    ground.outputConnectors[0].connect(over.inputConnectors[1])

    fin = LIB["finish"](c, page, over, preset="film35")
    fin.par.Preset.expr = "op('layouts').module.FINISHES[int(op('lay')['finish'][0])] if parent().par.Finishtake else parent().par.Finish"
    fin.outputConnectors[0].connect(c.op("out1"))

    ground.nodeX, ground.nodeY = 600, -200
    cam.nodeX, cam.nodeY = 600, 300
    render.nodeX, render.nodeY = 800, 100
    over.nodeX, over.nodeY = 980, 0
    return c.path
