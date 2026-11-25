# Builds /project1/im_depth_relief: each photograph of a prepared image set becomes
# a relief of points pushed out by its depth map, and the points stream from one
# photograph into the next, in time with the music: a new photograph every few bars,
# relief that breathes with the bass, kicks that throw the near parts at the lens.
# Six takes differ in camera and look (TAKES). Re-photographed through the finish.
#
# Prepare a set first, outside TouchDesigner:
#     python tools/imageprep/prepare.py <folder of pictures>
# then run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/im_depth_relief/build.py', encoding='utf-8').read(), g)
#     g['build'](folder='image_sets/<name>')
import td

SLUG = "im_depth_relief"
COLS, ROWS = 480, 270  # 129,600 points
DEFAULT_SET = "assets/image_sets/generated_depth"  # tools/imageprep/prepare.py <stills> --depth-from <depth maps>

# name, camera angle round the picture (degrees), height (degrees), distance x, swing with the bar (degrees),
# relief x, look (0 natural, 1 depth contours, 2 scan lines), kicks blow it apart (0..1)
TAKES = [
    ("Front", 0, 0, 1.0, 10, 1.0, 0, 0.0),
    ("Raking side", 52, 6, 1.05, 8, 2.0, 0, 0.0),
    ("Macro", -18, -8, 0.5, 14, 1.4, 0, 0.0),
    ("Contours", 24, 14, 0.95, 16, 1.6, 1, 0.0),
    ("Scan lines", -34, 20, 0.9, 12, 2.2, 2, 0.0),
    ("Burst", 0, 4, 1.1, 24, 1.2, 0, 1.0),
]


def build(folder=""):
    LIB = {"op": op}  # noqa: F821
    exec(open(td.project.folder.replace(chr(92), "/") + "/experiments/sw_images/image_lib.py", encoding="utf-8").read(), LIB)
    c, page = LIB["new_comp"](SLUG, folder, x=650, y=-1700, default=DEFAULT_SET)
    LIB["clock"](c, page, hold=7.0, travel=0.3)  # a change is close to snow halfway through: keep it short
    page.appendInt("Take", label="Take (camera and look, 0-5)")[0].val = 0
    LIB["slider"](page, "Bars", "Bars Per Picture (when music plays)", 2.0, 8.0, 0.5)
    LIB["slider"](page, "React", "How Hard It Follows The Music", 1.0, 2.0)
    hub = c.create(td.selectCHOP, "hub")
    hub.par.chop = "/project1/sw_hub/feed"
    hub.nodeX, hub.nodeY = -400, 60
    # with music the pictures change on bars; without it, every Hold seconds as before
    c.op("clock").par.value0.expr = (
        "parent().par.Start + (op('hub')['bar_pos'] / max(0.5, parent().par.Bars) if op('hub').numChans else absTime.seconds / max(0.2, parent().par.Hold))"
    )
    take = c.create(td.constantCHOP, "take")
    take.seq.const.numBlocks = 7
    for i, name in enumerate(("az", "el", "dist", "swing", "relief", "look", "burst")):
        setattr(take.par, "const%dname" % i, name)
        getattr(take.par, "const%dvalue" % i).expr = "%r[int(parent().par.Take) %% %d]" % (tuple(t[i + 1] for t in TAKES), len(TAKES))
    take.nodeX, take.nodeY = -400, -40
    LIB["slider"](page, "Relief", "Relief Depth", 0.4, 1.5)
    LIB["slider"](page, "Depthcurve", "Depth Curve (below 1 spreads the far distance)", 0.6, 2.0, 0.2)
    LIB["slider"](page, "Wander", "Wind On The Stream", 1.0, 3.0)
    LIB["slider"](page, "Pointsize", "Point Size", 1.25, 3.0, 0.3)
    LIB["slider"](page, "Dust", "Dust In Front", 1.0, 3.0)
    LIB["slider"](page, "Drift", "Camera Drift", 1.0, 3.0)
    LIB["slider"](page, "Distance", "Camera Distance", 1.75, 4.0, 0.8)

    pa, pb = LIB["pair"](c, "file")
    da, db = LIB["pair"](c, "depth")

    geo = c.create(td.geometryCOMP, "cloud")
    for child in geo.children:
        child.destroy()
    grid = geo.create(td.gridPOP, "grid")
    grid.par.surftype = "points"
    grid.par.cols, grid.par.rows = COLS, ROWS
    grid.par.normal = "none"
    grid.par.texture = "none"
    grid.render = True
    grid.display = True

    vert = LIB["shader_dat"](c, "cloud_vertex", SLUG, "shaders/cloud_vertex.glsl")
    pix = LIB["shader_dat"](c, "cloud_pixel", SLUG, "shaders/cloud_pixel.glsl")
    mat = c.create(td.glslMAT, "cloud_mat")
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = vert.path
    mat.par.pdat = pix.path
    mat.seq.sampler.numBlocks = 4
    for i, (name, top) in enumerate([("sA", pa), ("sB", pb), ("sDA", da), ("sDB", db)]):
        getattr(mat.par, "sampler%dname" % i).val = name
        getattr(mat.par, "sampler%dtop" % i).val = top.path
    S = "op('state')"
    M = "parent().par.React * (op('hub')['%s'] if op('hub').numChans else 0)"
    FOCAL = "640 / math.tan(math.radians(25))"  # the camera's 50 degree horizontal view at 1280 px
    LIB["uniforms"](mat, [
        ("uMorph", [S + "['mix']", "absTime.seconds % 3600", "parent().par.Relief * op('take')['relief']", "parent().par.Wander"]),
        ("uShape", ["mod.imset.number(%s['i0'], 'aspect')" % S, "mod.imset.number(%s['i1'], 'aspect')" % S, "parent().par.Pointsize", FOCAL]),
        ("uGrid", [COLS, ROWS, "parent().par.Dust", 0.9]),
        ("uMusic", [M % "hit_low", M % "bass", M % "hit_mid", M % "hit_high"]),
        ("uLook", ["op('take')['look']", "op('take')['burst']", "op('hub')['beat_pos'] if op('hub').numChans else absTime.seconds * 2",
                   "parent().par.Depthcurve"]),
    ])
    geo.par.material = mat.path

    target = c.create(td.nullCOMP, "target")
    cam = c.create(td.cameraCOMP, "cam")
    # the take places the camera on a sphere round the picture; it swings with the bar and steps in on kicks
    AZ = "math.radians(op('take')['az'] + op('take')['swing'] * parent().par.Drift * math.sin((op('hub')['bar_pos'] if op('hub').numChans else absTime.seconds * 0.4) * math.pi * 0.5))"
    EL = "math.radians(op('take')['el'] + 4 * parent().par.Drift * math.sin(absTime.seconds * 0.071 + 1.3))"
    D = "(parent().par.Distance * op('take')['dist'] * (1 - 0.07 * %s))" % (M % "hit_low")
    cam.par.tx.expr = "%s * math.sin(%s) * math.cos(%s)" % (D, AZ, EL)
    cam.par.ty.expr = "%s * math.sin(%s)" % (D, EL)
    cam.par.tz.expr = "%s * math.cos(%s) * math.cos(%s)" % (D, AZ, EL)
    cam.par.lookat = target.path
    cam.par.fov = 50
    cam.par.near, cam.par.far = 0.05, 50

    render = c.create(td.renderTOP, "render")
    render.par.camera = cam.path
    render.par.geometry = geo.path
    render.par.lights = ""
    render.par.outputresolution = "custom"
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = "rgba16float"
    render.par.bgcolorr, render.par.bgcolorg, render.par.bgcolorb, render.par.bgcolora = 0.004, 0.02, 0.018, 1

    fin = LIB["finish"](c, page, render, preset="film35")
    fin.outputConnectors[0].connect(c.op("out1"))

    for i, o in enumerate([pa, pb, da, db]):
        o.nodeX, o.nodeY = 0, 300 - i * 130
    geo.nodeX, geo.nodeY = 250, 300
    mat.nodeX, mat.nodeY = 250, 150
    vert.nodeX, vert.nodeY = 250, -250
    pix.nodeX, pix.nodeY = 400, -250
    cam.nodeX, cam.nodeY = 500, 150
    target.nodeX, target.nodeY = 500, 300
    render.nodeX, render.nodeY = 800, 0
    return c.path
