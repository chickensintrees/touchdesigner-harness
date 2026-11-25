# Shared scaffolding for the image templates: networks that read a prepared image
# set (tools/imageprep/prepare.py writes one from any folder of pictures).
# Use from a template's build.py, which runs inside TouchDesigner:
#
#     LIB = {'op': op}
#     exec(open(td.project.folder + '/experiments/sw_images/image_lib.py', encoding='utf-8').read(), LIB)
#     comp, page = LIB['new_comp']('im_example', folder='image_sets/holiday')
#     LIB['clock'](comp)                       # which two pictures are up, and how far between them
#     a, b = LIB['pair'](comp, 'file')         # two Movie File In TOPs that take turns
import td

_REPO = td.project.folder.replace(chr(92), "/")
_SCENE = {"op": op}  # noqa: F821
exec(open(_REPO + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), _SCENE)

DRIVER = '''def onFrameStart(frame):
    if parent().par.Preview.eval():
        op('out1').cook(force=True)
    return
'''


def new_comp(slug, folder="", x=0, y=0, default=""):
    """Create (or recreate) /project1/<slug> with a Controls page, the set's table, out1 and a cook driver.

    The set is `folder`, else the one the COMP being replaced was showing, else `default`."""
    root = op("/project1")  # noqa: F821
    old = root.op(slug)
    kept = folder
    if old:
        if hasattr(old.par, "Folder") and not folder:
            kept = old.par.Folder.eval()
        old.destroy()
    kept = kept or default
    c = root.create(td.baseCOMP, slug)
    c.nodeX, c.nodeY = x, y
    _SCENE["add_paths"](c)
    dat = c.op("local/modules").create(td.textDAT, "imset")
    dat.par.file.expr = "project.folder.replace(chr(92), '/') + '/experiments/sw_images/imset_module.py'"
    dat.par.syncfile = True
    dat.par.loadonstartpulse.pulse()

    page = c.appendCustomPage("Controls")
    page.appendStr("Folder", label="Image Set Folder (made by tools/imageprep)")[0].val = kept
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = True

    table = c.create(td.tableDAT, "table")
    table.par.file.expr = "mod.imset.root('table.tsv')"
    table.par.syncfile = True
    table.par.loadonstartpulse.pulse()
    table.nodeX, table.nodeY = -400, 300

    out1 = c.create(td.outTOP, "out1")
    out1.nodeX, out1.nodeY = 1400, 0
    drv = c.create(td.executeDAT, "cook_driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True
    drv.nodeX, drv.nodeY = -400, -100
    return c, page


def slider(page, name, label, value, top=1.0, low=0.0):
    p = page.appendFloat(name, label=label)[0]
    p.normMin, p.normMax = low, top
    p.default = value
    p.val = value
    return p


def clock(comp, page, hold=6.0, travel=0.45):
    """Adds Hold and Travel controls and a `state` CHOP:

    i0, i1   which picture each of the two slots holds (they take turns, so a slot
             only changes its picture while the other one is fully on screen)
    mix      0 = slot 0 is up, 1 = slot 1 is up, in between = travelling
    idx      how many pictures have gone by;  phase = 0..1 through the current one
    """
    slider(page, "Hold", "Seconds Per Picture", hold, 20.0, 0.5)
    slider(page, "Travel", "Part Of That Spent Changing", travel, 1.0, 0.02)
    page.appendInt("Start", label="First Picture")[0].val = 0
    t = comp.create(td.constantCHOP, "clock")
    t.par.name0 = "p"
    t.par.value0.expr = "parent().par.Start + absTime.seconds / max(0.2, parent().par.Hold)"
    s = comp.create(td.constantCHOP, "state")
    s.seq.const.numBlocks = 5
    P = "op('clock')['p']"
    rows = [
        ("idx", "int(%s)" % P),
        ("phase", "%s %% 1" % P),
        ("i0", "2 * ((int(%s) + 1) // 2)" % P),
        ("i1", "2 * (int(%s) // 2) + 1" % P),
        ("mix", "(lambda p, tr: (lambda m: m if int(p) %% 2 == 0 else 1 - m)(min(1, max(0, ((p %% 1) - (1 - tr)) / tr))))(%s, max(0.02, parent().par.Travel))" % P),
    ]
    for i, (name, expr) in enumerate(rows):
        setattr(s.par, "const%dname" % i, name)
        getattr(s.par, "const%dvalue" % i).expr = expr
    t.nodeX, t.nodeY = -400, 180
    s.nodeX, s.nodeY = -250, 180
    return s


def movie(comp, name, expr, w=0, h=0):
    m = comp.create(td.moviefileinTOP, name)
    m.par.file.expr = expr
    if w:
        m.par.outputresolution = "custom"
        m.par.resolutionw, m.par.resolutionh = w, h
    return m


def pair(comp, col, prefix=None):
    """Two Movie File In TOPs showing column `col` ('file', 'depth', 'cutout') of pictures i0 and i1."""
    prefix = prefix or col
    a = movie(comp, prefix + "0", "mod.imset.path(op('state')['i0'], '%s')" % col)
    b = movie(comp, prefix + "1", "mod.imset.path(op('state')['i1'], '%s')" % col)
    return a, b


def shader_dat(comp, name, slug, rel):
    dat = comp.create(td.textDAT, name)
    dat.par.file.expr = "mod.paths.experiment('%s', '%s')" % (slug, rel)
    dat.par.syncfile = True
    dat.par.loadonstartpulse.pulse()
    return dat


def glsl_top(comp, name, slug, rel, fmt="rgba16float", w=1280, h=720):
    dat = shader_dat(comp, name + "_frag", slug, rel)
    g = comp.create(td.glslTOP, name)
    for d in list(g.docked):
        d.destroy()
    g.par.pixeldat = dat.name
    g.par.format = fmt
    g.par.outputresolution = "custom"
    g.par.resolutionw, g.par.resolutionh = w, h
    return g


def uniforms(node, rows):
    node.seq.vec.numBlocks = len(rows)
    for i, (name, exprs) in enumerate(rows):
        setattr(node.par, "vec%dname" % i, name)
        for axis, expr in zip("xyzw", exprs):
            getattr(node.par, "vec%dvalue%s" % (i, axis)).expr = str(expr)


def finish(comp, page, source, preset="film35"):
    """Re-photograph `source` through a private copy of the finish component, with a Finish menu on the page."""
    import json

    g = {"op": op, "td": td, "__name__": "build"}  # noqa: F821
    exec(open(_REPO + "/experiments/sw_finish/build.py", encoding="utf-8").read(), g)
    with open(_REPO + "/experiments/sw_finish/presets.json", encoding="utf-8") as fh:
        presets = json.load(fh)
    menu = page.appendMenu("Finish", label="Finish (film, tape, tube, 1-bit)")[0]
    menu.menuNames = list(presets)
    menu.menuLabels = [presets[k]["label"] for k in presets]
    menu.val = preset
    path = g["build"](name="finish", parent=comp.path, preset=preset)
    f = op(path)  # noqa: F821
    f.par.Input = ""
    source.outputConnectors[0].connect(f.inputConnectors[0])
    f.par.Preset.expr = "parent().par.Finish"
    f.par.Preview.expr = "parent().par.Preview"
    f.nodeX, f.nodeY = 1150, 0
    return f
