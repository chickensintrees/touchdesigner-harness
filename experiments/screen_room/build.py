# Builds /project1/screen_room: a photographed room with a television in it, and
# any other picture playing on that television. The rooms are pictures in
# assets/rooms (generated, with the four corners of each screen and a mask of
# its glass: see tools/assets/file_generated.py). Give it the path of a TOP (the
# footage player, another scene's out1, a camera) and it pins that picture to the
# glass, keeps the room's reflections on it, lets the screen light the bezel, and
# re-photographs the whole thing through the finish. Each take is another room.
#
# Run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/screen_room/build.py', encoding='utf-8').read(), g)
#     g['build']()                                        # shows /project1/sw_footage/out1
#     g['build'](source='/project1/sc_rutt_etra/out1')
import td

SLUG = "screen_room"
DEFAULT_FOLDER = "assets/rooms"  # read against the repository unless it is a full path
DEFAULT_SOURCE = "/project1/sw_footage/out1"

DRIVER = '''def onFrameStart(frame):
    if parent().par.Preview.eval():
        op('out1').cook(force=True)
    return
'''

FOLDER = (
    "(lambda f: f if (f.startswith('/') or f[1:2] == ':') else project.folder.replace(chr(92), '/') + '/' + f)"
    "(str(parent().par.Folder.eval()).replace(chr(92), '/').rstrip('/'))"
)
ROW = "(1 + int(parent().par.Take) % max(1, op('rooms').numRows - 1))"


def _cell(col, number=True):
    get = "op('rooms')[%s, '%s']" % (ROW, col)
    if number:
        return "float(%s.val) if op('rooms').numRows > 1 else %s" % (get, "1" if col in ("m0", "m4", "m8", "aspect") else "0.5" if col in ("cx", "cy") else "0")
    return "(%s + '/' + %s.val) if op('rooms').numRows > 1 else ''" % (FOLDER, get)


def build(source="", folder=""):
    repo = td.project.folder.replace(chr(92), "/")
    LIB = {"op": op}  # noqa: F821
    exec(open(repo + "/experiments/sw_images/image_lib.py", encoding="utf-8").read(), LIB)
    SCENE = {"op": op}  # noqa: F821
    exec(open(repo + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), SCENE)
    root = op("/project1")  # noqa: F821
    old = root.op(SLUG)
    if old:
        if not source and hasattr(old.par, "Input"):
            source = old.par.Input.eval()
        if not folder and hasattr(old.par, "Folder"):
            folder = old.par.Folder.eval()
        old.destroy()
    c = root.create(td.baseCOMP, SLUG)
    c.nodeX, c.nodeY = 1250, -1700
    SCENE["add_paths"](c)

    page = c.appendCustomPage("Controls")
    page.appendStr("Input", label="Input (path of the TOP to show; blank = no signal)")[0].val = source or DEFAULT_SOURCE
    page.appendStr("Folder", label="Folder Of Rooms")[0].val = folder or DEFAULT_FOLDER
    page.appendInt("Take", label="Take (which room)")[0].val = 0
    page.appendFloat("Shotstart", label="Shot Start (absTime s; the push in begins here)")[0].val = 0
    LIB["slider"](page, "Push", "Push In (how far the camera closes on the screen)", 0.3, 0.8)
    LIB["slider"](page, "Pushtime", "Seconds The Push Takes", 9.0, 30.0, 1.0)
    LIB["slider"](page, "Glow", "Screen Glow Into The Room", 1.0, 2.5)
    LIB["slider"](page, "Roomlight", "Room Light", 0.8, 1.2, 0.1)
    LIB["slider"](page, "Reflect", "Room Reflected In The Glass", 0.7, 2.0)
    LIB["slider"](page, "Bright", "Screen Brightness", 0.95, 2.0, 0.2)
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = True

    rooms = c.create(td.tableDAT, "rooms")
    rooms.par.file.expr = FOLDER + " + '/rooms.tsv'"
    rooms.par.syncfile = True
    rooms.par.loadonstartpulse.pulse()

    picture = LIB["movie"](c, "room_picture", _cell("file", number=False))
    mask = LIB["movie"](c, "glass_mask", _cell("mask", number=False))

    named = c.create(td.selectTOP, "named")
    named.par.top.expr = "parent().par.Input.eval() or ''"

    g = {"op": op, "td": td, "__name__": "build"}  # noqa: F821
    exec(open(repo + "/experiments/sw_finish/build.py", encoding="utf-8").read(), g)
    tube = op(g["build"](name="tube", parent=c.path, preset="crt"))  # noqa: F821
    named.outputConnectors[0].connect(tube.inputConnectors[0])
    tube.par.Preview.expr = "parent().par.Preview"
    # the photographed glass already has the tube's shape, its corners and its surround
    for name in ("Curvature", "Corners", "Fourthree", "Vignette"):
        tube.par[name] = 0
    tube.par.Bloom = 0.2

    spill = c.create(td.blurTOP, "spill")
    spill.par.outputresolution = "eighth"
    spill.par.size = 30
    tube.outputConnectors[0].connect(spill)

    frag = LIB["shader_dat"](c, "room_frag", SLUG, "shaders/room.frag")
    room = c.create(td.glslmultiTOP, "room")
    for d in list(room.docked):
        d.destroy()
    room.par.pixeldat = frag.name
    room.par.format = "rgba16float"
    room.par.outputresolution = "custom"
    room.par.resolutionw, room.par.resolutionh = 1280, 720
    for i, src in enumerate((picture, mask, tube, spill)):
        src.outputConnectors[0].connect(room.inputConnectors[i])
    pp = "parent().par."
    LIB["uniforms"](room, [
        ("uRow0", [_cell("m0"), _cell("m1"), _cell("m2"), 0]),
        ("uRow1", [_cell("m3"), _cell("m4"), _cell("m5"), 0]),
        ("uRow2", [_cell("m6"), _cell("m7"), _cell("m8"), _cell("glass")]),
        ("uScreen", [_cell("cx"), _cell("cy"), _cell("aspect"), "0 if parent().par.Input.eval() else 1"]),
        ("uShot", [pp + "Push", "max(0, absTime.seconds - parent().par.Shotstart)", pp + "Pushtime", "absTime.seconds % 3600"]),
        ("uLight", [pp + "Glow", pp + "Roomlight", pp + "Reflect", pp + "Bright"]),
    ])

    fin = LIB["finish"](c, page, room, preset="film35")
    out1 = c.create(td.outTOP, "out1")
    fin.outputConnectors[0].connect(out1)

    drv = c.create(td.executeDAT, "cook_driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True
    rooms.nodeX, rooms.nodeY = -250, 300
    picture.nodeX, picture.nodeY = 0, 300
    mask.nodeX, mask.nodeY = 0, 170
    frag.nodeX, frag.nodeY = 600, -250
    drv.nodeX, drv.nodeY = -250, -160
    for i, o in enumerate([named, tube, spill, room, fin, out1]):
        o.nodeX, o.nodeY = i * 200, 0
    return c.path
