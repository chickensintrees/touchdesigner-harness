# Builds a finish component: one COMP that any picture can pass through to pick up
# the texture of a period medium (35mm film, VHS tape, a CRT tube, a 1-bit screen).
# Run inside TouchDesigner:
#
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/sw_finish/build.py', encoding='utf-8').read(), g)
#     g['build']()                                   # /project1/sw_finish
#     g['build'](name='finish', parent='/project1/sc_x')   # a private copy inside another COMP
#
# Rebuilding destroys and recreates the COMP, so this file is the source of truth.
# The picture comes from the COMP's Input parameter (the path of any TOP) or, when
# that is blank, from whatever is wired into the COMP's input. /project1/sw_finish
# itself starts on the footage player (experiments/sw_footage) when that is built.
import json

import td

SLUG = "sw_finish"
DEFAULT_INPUT = "/project1/sw_footage/out1"

# name, label, default, slider max
SLIDERS = [
    ("Grain", "Film Grain", 0.0, 1.0),
    ("Bloom", "Bloom (glow around highlights)", 0.0, 1.0),
    ("Halation", "Halation (red halo, film)", 0.0, 1.0),
    ("Weave", "Gate Weave (frame wander)", 0.0, 1.0),
    ("Scanlines", "Scan Lines", 0.0, 1.0),
    ("Mask", "Phosphor Stripes", 0.0, 1.0),
    ("Curvature", "Tube Curvature", 0.0, 1.0),
    ("Corners", "Rounded Corners", 0.0, 1.0),
    ("Misregister", "Colour Misregistration", 0.0, 1.0),
    ("Bleed", "Tape Colour Bleed", 0.0, 1.0),
    ("Soften", "Softness (copy of a copy)", 0.0, 1.0),
    ("Tracking", "Tracking Error", 0.0, 1.0),
    ("Headswitch", "Head-Switch Noise (bottom edge)", 0.0, 1.0),
    ("Dither", "1-Bit Dither", 0.0, 1.0),
    ("Ditherpixel", "1-Bit Pixel Size", 3.0, 8.0),
    ("Letterbox", "Letterbox Shape (0 = none, 2.39 = scope)", 0.0, 2.6),
    ("Vignette", "Vignette", 0.0, 1.0),
    ("Blacktint", "Tint In The Blacks", 0.0, 0.3),
]

PRESET_EXEC = '''import json


def apply(comp, name):
    """Copy one preset from presets.json onto the Controls page."""
    path = comp.op('local/modules/paths').module.experiment('sw_finish', 'presets.json')
    with open(path, encoding='utf-8') as fh:
        presets = json.load(fh)
    preset = presets.get(name)
    if preset is None:
        return
    for key, value in preset.items():
        if key == 'label':
            continue
        if isinstance(value, list):
            for suffix, v in zip('rgb', value):
                getattr(comp.par, key + suffix).val = v
        elif hasattr(comp.par, key):
            getattr(comp.par, key).val = value


def onValueChange(par, prev):
    if par.name == 'Preset':
        apply(parent(), parent().par.Preset.eval())
    return
'''

DRIVER = '''def onFrameStart(frame):
    if parent().par.Preview.eval():
        op('out1').cook(force=True)
    return
'''


def _uniforms(glsl, rows):
    glsl.seq.vec.numBlocks = len(rows)
    for i, (name, exprs) in enumerate(rows):
        setattr(glsl.par, "vec%dname" % i, name)
        for axis, expr in zip("xyzw", exprs):
            getattr(glsl.par, "vec%dvalue%s" % (i, axis)).expr = str(expr)


def _shader(comp, name, rel, fmt="rgba16float"):
    dat = comp.create(td.textDAT, name + "_frag")
    dat.par.file.expr = "mod.paths.experiment('%s', 'shaders/%s')" % (SLUG, rel)
    dat.par.syncfile = True
    dat.par.loadonstartpulse.pulse()
    glsl = comp.create(td.glslTOP, name)
    for suffix in ("_pixel", "_compute"):
        docked = comp.op(name + suffix)
        if docked:
            docked.destroy()
    glsl.par.pixeldat = dat.name
    glsl.par.format = fmt
    return glsl


def build(name=SLUG, parent="/project1", preset="film35"):
    lib = {"op": op}  # noqa: F821
    repo = td.project.folder.replace(chr(92), "/")
    exec(open(repo + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), lib)
    root = op(parent)  # noqa: F821
    old = root.op(name)
    kept = {}
    if old:
        for key in ("Input", "Preview"):
            if hasattr(old.par, key):
                kept[key] = old.par[key].eval()
        old.destroy()
    if name == SLUG and not kept.get("Input") and op(DEFAULT_INPUT) is not None:  # noqa: F821
        kept["Input"] = DEFAULT_INPUT
    c = root.create(td.baseCOMP, name)
    c.nodeX, c.nodeY = 250, -1700
    lib["add_paths"](c)

    with open(repo + "/experiments/%s/presets.json" % SLUG, encoding="utf-8") as fh:
        presets = json.load(fh)

    page = c.appendCustomPage("Controls")
    page.appendStr("Input", label="Input (path of any TOP; blank = wired input)")[0].val = kept.get("Input", "")
    m = page.appendMenu("Preset", label="Preset (sets the sliders below)")[0]
    m.menuNames = list(presets)
    m.menuLabels = [presets[k]["label"] for k in presets]
    page.appendToggle("Bypass", label="Bypass (show the input untouched)")[0].val = False
    for pname, label, default, top in SLIDERS:
        p = page.appendFloat(pname, label=label)[0]
        p.normMin, p.normMax, p.min, p.clampMin = 0, top, 0, True
        p.default = default
        p.val = default
    page.appendToggle("Fourthree", label="4:3 Picture (crop the sides)")[0].val = False
    page.appendRGB("Blackcolor", label="Black Tint Colour")
    cast = page.appendRGB("Cast", label="Colour Cast")
    for p in cast:
        p.val = 1
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = kept.get("Preview", True)

    # ---- picture in ---------------------------------------------------------
    wired = c.create(td.inTOP, "in1")
    named = c.create(td.selectTOP, "named")
    named.par.top.expr = "parent().par.Input.eval() or ''"
    pick = c.create(td.switchTOP, "pick")
    wired.outputConnectors[0].connect(pick.inputConnectors[0])
    named.outputConnectors[0].connect(pick.inputConnectors[1])
    pick.par.index.expr = "1 if parent().par.Input.eval() else 0"
    fit = c.create(td.fitTOP, "fit")
    fit.par.outputresolution = "custom"
    fit.par.resolutionw, fit.par.resolutionh = 1280, 720
    fit.par.format = "rgba16float"
    pick.outputConnectors[0].connect(fit)

    clock = [
        "absTime.seconds % 3600",
        "absTime.frame % 4096",
        "parent().par.Weave",
        0,
    ]

    # ---- pass 1: the signal -------------------------------------------------
    signal = _shader(c, "signal", "signal.frag")
    fit.outputConnectors[0].connect(signal.inputConnectors[0])
    _uniforms(signal, [
        ("uTape", ["parent().par.Bleed", "parent().par.Tracking", "parent().par.Headswitch", "parent().par.Soften"]),
        ("uClock", clock),
    ])

    # ---- highlights, blurred twice -------------------------------------------
    bright = _shader(c, "bright", "bright.frag")
    bright.par.outputresolution = "quarter"
    signal.outputConnectors[0].connect(bright.inputConnectors[0])
    _uniforms(bright, [("uKnee", [0.7, 0, 0, 0])])
    bloom = c.create(td.blurTOP, "bloom")
    bloom.par.size = 6
    bright.outputConnectors[0].connect(bloom)
    hal = c.create(td.blurTOP, "halation")
    hal.par.size = 22
    bloom.outputConnectors[0].connect(hal)

    # ---- pass 2: the display -------------------------------------------------
    display = _shader(c, "display", "display.frag", fmt="rgba8fixed")
    signal.outputConnectors[0].connect(display.inputConnectors[0])
    bloom.outputConnectors[0].connect(display.inputConnectors[1])
    hal.outputConnectors[0].connect(display.inputConnectors[2])
    pp = "parent().par."
    _uniforms(display, [
        ("uTube", [pp + "Curvature", pp + "Scanlines", pp + "Mask", pp + "Corners"]),
        ("uGlow", [pp + "Bloom", pp + "Halation", pp + "Misregister", pp + "Grain"]),
        ("uFrame", [pp + "Letterbox", pp + "Fourthree", pp + "Dither", pp + "Ditherpixel"]),
        ("uTint", [pp + "Blackcolorr", pp + "Blackcolorg", pp + "Blackcolorb", pp + "Blacktint"]),
        ("uCast", [pp + "Castr", pp + "Castg", pp + "Castb", pp + "Vignette"]),
        ("uClock", clock),
    ])

    bypass = c.create(td.switchTOP, "bypass")
    display.outputConnectors[0].connect(bypass.inputConnectors[0])
    fit.outputConnectors[0].connect(bypass.inputConnectors[1])
    bypass.par.index.expr = "1 if parent().par.Bypass else 0"
    out1 = c.create(td.outTOP, "out1")
    bypass.outputConnectors[0].connect(out1)

    pe = c.create(td.parameterexecuteDAT, "preset_exec")
    pe.text = PRESET_EXEC
    pe.par.op = ".."
    pe.par.pars = "Preset"
    pe.par.valuechange = True
    pe.par.custom = True
    pe.par.builtin = False
    pe.par.active = True

    drv = c.create(td.executeDAT, "cook_driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True

    for i, o in enumerate([wired, named, pick, fit, signal, bright, bloom, hal, display, bypass, out1]):
        o.nodeX, o.nodeY = i * 170, 0
    pe.nodeX, pe.nodeY = 0, -200
    drv.nodeX, drv.nodeY = 200, -200

    c.par.Preset = preset
    pe.module.apply(c, preset)
    return c.path


def apply(path, preset):
    """Switch a built finish to a named preset from presets.json."""
    c = op(path)  # noqa: F821
    c.par.Preset = preset
    c.op("preset_exec").module.apply(c, preset)
    return preset
