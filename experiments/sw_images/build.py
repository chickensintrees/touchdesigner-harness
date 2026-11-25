# Builds /project1/sw_images: plays the pictures of a prepared image set in colour
# order. Its out1 is an ordinary 1280x720 picture, so it can be the Input of any
# scene ("/project1/sw_images/out1"): the scene then applies its technique to a
# folder of photographs.
#
# Prepare a set first, outside TouchDesigner:
#     python tools/imageprep/prepare.py <folder of pictures>
# then run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/sw_images/build.py', encoding='utf-8').read(), g)
#     g['build'](folder='image_sets/<name>')
import td

SLUG = "sw_images"
DEFAULT_SET = "assets/image_sets/generated_depth"


def build(folder=""):
    LIB = {"op": op}  # noqa: F821
    exec(open(td.project.folder.replace(chr(92), "/") + "/experiments/sw_images/image_lib.py", encoding="utf-8").read(), LIB)
    c, page = LIB["new_comp"](SLUG, folder, x=450, y=-1700, default=DEFAULT_SET)
    LIB["clock"](c, page, hold=4.0, travel=0.25)
    m = page.appendMenu("Change", label="Change Between Pictures")[0]
    m.menuNames = ["dissolve", "cut", "static"]
    m.menuLabels = ["Dissolve", "Hard Cut", "Cut Through Static"]
    m.val = "static"
    LIB["slider"](page, "Push", "Slow Push In", 0.06, 0.3)
    LIB["slider"](page, "Colour", "Colour Treatment Per Picture (0 = as photographed)", 1.0, 1.0)
    page.appendToggle("Fill", label="Fill The Frame (crop) / Show Whole Picture")[0].val = True
    g = page.appendRGB("Ground", label="Colour Behind A Whole Picture")
    for p, v in zip(g, (0.008, 0.086, 0.078)):
        p.val = v

    a, b = LIB["pair"](c, "file")
    play = LIB["glsl_top"](c, "player", SLUG, "shaders/player.frag", fmt="rgba8fixed")
    a.outputConnectors[0].connect(play.inputConnectors[0])
    b.outputConnectors[0].connect(play.inputConnectors[1])
    S = "op('state')"
    LIB["uniforms"](play, [
        ("uMix", [S + "['mix']", "parent().par.Change.menuIndex", "parent().par.Push", S + "['phase']"]),
        ("uShape", ["mod.imset.number(%s['i0'], 'aspect')" % S, "mod.imset.number(%s['i1'], 'aspect')" % S,
                    "1 if parent().par.Fill else 0", "absTime.seconds % 600"]),
        ("uGround", ["parent().par.Groundr", "parent().par.Groundg", "parent().par.Groundb", 1]),
        ("uColour", [S + "['i0'] % max(1, mod.imset.count())", S + "['i1'] % max(1, mod.imset.count())", "parent().par.Colour", 0]),
    ])
    play.outputConnectors[0].connect(c.op("out1"))
    a.nodeX, a.nodeY = 0, 100
    b.nodeX, b.nodeY = 0, -100
    play.nodeX, play.nodeY = 400, 0
    return c.path
