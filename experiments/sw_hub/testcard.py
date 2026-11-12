# Builds /project1/sw_testcard: an always-cooking moving picture that scene builders
# use as a stand-in "another scene" when testing a scene's Input parameter.
# Run inside TouchDesigner:  exec(open(<this file>).read()); build()
import td

DRIVER = '''def onFrameStart(frame):
    op('out1').cook(force=True)
    return
'''


def build():
    root = op("/project1")
    old = root.op("sw_testcard")
    if old:
        old.destroy()
    c = root.create(td.baseCOMP, "sw_testcard")
    c.nodeX, c.nodeY = -350, -1100

    ramp = c.create(td.rampTOP, "ramp")
    ramp.par.outputresolution = "custom"
    ramp.par.resolutionw, ramp.par.resolutionh = 1280, 720
    ramp.par.type = "circular"
    ramp.par.phase.expr = "absTime.seconds * 0.15"

    bars = c.create(td.noiseTOP, "bars")
    bars.par.outputresolution = "custom"
    bars.par.resolutionw, bars.par.resolutionh = 1280, 720
    bars.par.mono = False
    bars.par.period = 2.5
    bars.par.tz.expr = "absTime.seconds * 0.4"

    mix = c.create(td.compositeTOP, "mix")
    mix.par.operand = "multiply"
    ramp.outputConnectors[0].connect(mix.inputConnectors[0])
    bars.outputConnectors[0].connect(mix)

    text = c.create(td.textTOP, "text")
    text.par.outputresolution = "custom"
    text.par.resolutionw, text.par.resolutionh = 1280, 720
    text.par.text = "TEST\nINPUT"
    text.par.fontsizex = 190
    text.par.bgalpha = 0

    spin = c.create(td.transformTOP, "spin")
    spin.par.rotate.expr = "math.sin(absTime.seconds * 0.8) * 12"
    spin.par.tx.expr = "math.sin(absTime.seconds * 0.5) * 0.12"
    text.outputConnectors[0].connect(spin)

    over = c.create(td.overTOP, "over")
    spin.outputConnectors[0].connect(over.inputConnectors[0])
    mix.outputConnectors[0].connect(over.inputConnectors[1])

    out1 = c.create(td.outTOP, "out1")
    over.outputConnectors[0].connect(out1)

    drv = c.create(td.executeDAT, "cook_driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True
    for i, o in enumerate(c.children):
        o.nodeX, o.nodeY = (i % 5) * 160, -(i // 5) * 130
    return c.path
