# Builder for /project1/sc_light_gobo ("Fluorescent fog and shadow type").
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md):
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/sc_light_gobo/build.py', encoding='utf-8').read(), g)
#     path = g['build']()
# Idempotent: destroys and rebuilds the whole scene.
import td

SLUG = "sc_light_gobo"
# Files are found through the scaffold's module DAT (local/modules/paths): every file parameter below is an
# expression, so nothing here names a folder. Fonts and models come from <assets>/ and are optional.
# With a font missing the Text TOP's own default face is used (set bold, since a stencil wants a heavy face).
# Do not name a system face as the fallback: a face the machine lacks is a warning on every Text TOP
# ("Arial Black" is not in this build's Font menu even on Windows).
ARCHIVO = "mod.paths.font('archivo')"     # <assets>/fonts/ArchivoBlack-Regular.ttf
BARLOW = "mod.paths.font('barlow')"       # <assets>/fonts/BarlowCondensed-Bold.ttf

# The scene's own content (2026-11-11). A pack may replace any of these five names with its
# scenes/sc_light_gobo/words.json; build() reads them once through LIB['scene_words'].
#   PHRASES: the text atlas, eight two-line phrases (2 columns x 4 rows of 512x256 cells, read by
#            beam.frag's textCell()). The count is fixed.
#   CELL:    how many of a cell's 512 pixels the widest line of a phrase may fill. Under 512 leaves a gap
#            between neighbours where the phrases are tiled (takes 4 and 8).
#   MODELS:  which library model stands where in which take, one row each:
#            [take, model, x, z, yaw degrees, scale, spin, y of its base]. A model once per take at most.
#   SIZES:   bounding box [x, y, z] of each of those models, from <assets>/models/<slug>/info.json
#            ("size_units"; the meshes are centred on the origin, longest side 1). Kept here so that a model can
#            be stood on the floor without reading the library, and so that the stand-in teapot can be fitted
#            to the same box.
#   NOUNS:   what the Describe captions call the things in the takes ({name} in CAPTIONS, CAPTIONS_IN and
#            DESCRIBE below), so the captions stay true whichever models a pack puts there.
DEFAULTS = {
    "PHRASES": [
        "REAL\nTIME.", "DO NOT\nTOUCH",
        "EVERY FRAME\nIS MADE NOW.", "NOTHING IS\nPRERENDERED.",
        "LISTEN WITH\nYOUR EYES.", "PLATE\n07",
        "FOUND,\nNOT MADE.", "SOUND IN.\nPICTURE OUT.",
    ],
    "CELL": 432,
    "MODELS": [
        # 0 WORDS IN AIR: one figure standing in the beam, cut out of every copy of the phrase
        [0, "amphora", -0.8, -0.7, 200, 1.5, 0.3, 0],
        # 1 BLINDS: one backlit thing among the shafts
        [1, "gramophone", 1.2, 2.2, 160, 1.4, 0.1, 0],
        # 2 RED PLANES: a skyline of five
        [2, "broken_column", 0.5, 0, 0, 1.5, 0, 0],
        [2, "lander", -1.6, 1.3, 40, 1.2, 0.4, 0],
        [2, "skeleton_key", 2.7, -1.2, -15, 1.7, 0, 0],
        [2, "traffic_cone", 1.1, 1.6, 150, 0.8, 0, 0],
        [2, "amphora", -0.6, -0.9, 0, 1.3, 0, 0],
        # 3 LAMP CONE: two things under the cone
        [3, "astrolabe", 0.32, -0.05, -20, 1.25, 0, 0],
        [3, "balanced_solids", -0.12, 0.3, 30, 1.3, 0, 0],
        # 4 FLOOR TYPE: two long shadows seen from above
        [4, "pierced_stone", 1.2, -0.3, 0, 2.0, 0.5, 0],
        [4, "traffic_cone", -1.0, 1.0, 140, 1.0, 0, 0],
        # 5 GRID WINDOW: three small things on a big floor, the first under the warm lamp
        [5, "lander", 0.5, 0.5, 0, 1.2, 0, 0],
        [5, "rubber_duck", 1.4, 1.5, 160, 0.9, 0, 0],
        [5, "hourglass", -2.2, -1.0, 20, 1.5, 0, 0],
        # 6 LEANING TUBES: a silhouette in front of the tubes
        [6, "crystal_cluster", 1.3, 0.8, 0, 1.4, 0.2, 0],
        # 7 ONE BIT: the silhouette in front of the wheel
        [7, "marble_bust", -0.4, 1.5, 180, 1.35, 1.0, 0],
        # 8 SHADOW PLAY: the thing that turns in the beam
        [8, "wire_cage", 0.6, 1.0, 0, 1.5, 1.2, 0],
        # 9 CORRIDOR: one near the wall, one far down
        [9, "balanced_solids", 1.9, -1.0, -90, 1.5, 0, 0],
        [9, "traffic_cone", -0.6, -6.5, 30, 1.0, 0, 0],
        # 10 FLOOR TUBE: the shadow caster and a small thing beside the tube
        [10, "ribbon_loop", 0.2, -0.9, 200, 1.1, 0.15, 0],
        [10, "hourglass", -0.3, 0.9, 40, 0.4, 0, 0],
    ],
    "SIZES": {
        "marble_bust": [0.5578, 1.0, 0.5336], "gramophone": [0.7399, 1.0, 0.7372],
        "broken_column": [0.7451, 1.0, 0.7748], "lander": [0.8823, 1.0, 0.883],
        "skeleton_key": [0.1223, 1.0, 0.4343], "traffic_cone": [0.6053, 1.0, 0.6052],
        "balanced_solids": [0.2997, 1.0, 0.2996], "astrolabe": [0.6383, 1.0, 0.6387],
        "hourglass": [0.5482, 1.0, 0.5481], "pierced_stone": [0.7907, 1.0, 0.3366],
        "amphora": [0.5717, 1.0, 0.5719], "crystal_cluster": [1.0, 0.6487, 0.8586],
        "rubber_duck": [1.0, 0.7802, 0.8354], "wire_cage": [0.9973, 0.97, 1.0],
        "ribbon_loop": [0.7078, 1.0, 0.5891],
    },
    "NOUNS": {
        "words": "amphora", "blinds": "gramophone",
        "things_are": "objects are", "things_own": "objects'",
        "lamp_a": "an astrolabe", "lamp_b": "a stack of solids",
        "floor_a": "pierced stone", "floor_b": "cone",
        "grid": "printed grid", "onebit": "bust", "wall": "cage", "tube": "looped ribbon",
    },
}
NPHRASES = 8
# TouchDesigner's bundled teapot (what mod.paths.model_file returns with no library): bounds measured
# 2026-11-11 in build 2025.33230, used only if the measurement at build time returns nothing.
TEAPOT_MIN, TEAPOT_MAX = (-0.9959, 0.0, -0.6105), (0.9681, 0.9158, 0.6105)
# 1 = stretch the teapot to the model's whole box; 0 = keep its proportions and fit it inside the box.
STANDIN_STRETCH = 1.0

# Describe mode (parent().par.Describe): the words explain the technique. Two kinds of words:
# DESCRIBE[take] = eight atlas cells for the takes whose gobo is text (0, 4, 8), built beside the phrase atlas
# so the toggle is only a Switch TOP; CAPTIONS[take] = a two-line caption along the bottom of every take.
# Mirrored in preset.json as "words". Every statement is true of beam.frag as built.
DESCRIBE = {
    0: ["LIGHT\nIN FOG", "A WORD IS\nA STENCIL", "RAY-MARCHED\nFOG", "LAYERS\nOF SMOKE",
        "36 FOG STEPS\nPER PIXEL", "SHADOW\nMAP", "BEAT MOVES\nTHE SMOKE", "SNARE =\nBRIGHTER"],
    4: ["TEXT AS\nA MASK", "PROJECTED\nON CARPET", "SEEN FROM\nABOVE", "RAKING\nLIGHT",
        "ROWS SLIDE\nON THE BEAT", "LONG\nSHADOWS", "64 FOG\nSTEPS", "SHADOW\nMAP"],
    8: ["INVERTED\nMASK", "WORDS ARE\nSHADOWS", "THE REST\nIS LIGHT", "ONE\nPROJECTOR",
        "{WALL} TURNS\nIN THE BEAM", "64 FOG\nSTEPS", "SNARE =\nBRIGHTER", "FOG AND\nSHADOW"],
}
CAP_W, CAP_H = 1216, 96      # caption strip size in pixels; it sits centred along the bottom
CAPTIONS = [
    "A projector shines through a stencil of these words into ray-marched fog.\n"
    "Thin layers of smoke catch the image and travel down the beam on the beat. A snare makes it brighter.",
    "Volumetric light: one shader steps 64 times through fog along each pixel's ray and asks if light reaches that point.\n"
    "Here the mask is a venetian blind. The slats open and close over two bars. A shadow map cuts out the {blinds}.",
    "No beam here: five thin planes of red light slice the fog, and each shows a cross-section of the drifting smoke.\n"
    "Kick and snare choose which planes flare. The {things_are} only a black skyline.",
    "One cone of warm light, ray-marched through fine smoke over {lamp_a} and {lamp_b}.\n"
    "The kick makes the smoke thicker. A shadow map cuts the {things_own} shadows out of the cone.",
    "Seen from straight above: a projector throws these tiled words across the carpet at a raking angle.\n"
    "Rows slide against each other on the beat. A shadow map gives the {floor_a} and the {floor_b} their long shadows.",
    "The projector's mask is a {grid}: its ruled lines and filled boxes become planes of blue light in the fog.\n"
    "Kick and snare strike the ceiling tubes. Each new section of the song fills different boxes.",
    "No projector: five bare fluorescent tubes are line lights in thin fog, each mirrored in the floor by one reflected ray.\n"
    "Kick and snare choose which tubes strike. They stutter like a ballast catching, then hold bright.",
    "The same fog and light, reduced to pure black and white dots by an ordered dither.\n"
    "A spoked wheel turns in front of the lamp on the beat. The {onebit}'s shadow is a solid shape in the fog.",
    "The mask is inverted: the projector lights the whole room and these words are its shadows.\n"
    "The {wall} turns in the beam and a shadow map throws its shadow on the wall. A snare makes the lamp brighter.",
    "No projector: eight ceiling tubes light the fog as line lights, sampled 12 times along each pixel's ray.\n"
    "A pulse of light runs down the row toward the camera every two beats. Kick and snare strike single tubes.",
    "One fluorescent tube lies on the carpet. A hidden lamp beside it throws the {tube}'s shadow up the wall.\n"
    "Kick and snare strike the tube, and the tube and its light flicker together.",
]

# The caption for the takes that use an Input picture, while one is on (the words above would be untrue then).
CAPTIONS_IN = {
    0: "A projector throws the incoming picture into ray-marched fog.\n"
       "Thin layers of smoke each catch the whole picture and travel down the beam on the beat. A shadow map cuts out the {words}.",
    1: "The incoming picture is the light behind a venetian blind: its colours ride the shafts through ray-marched fog.\n"
       "The slats open and close over two bars. A shadow map cuts out the {blinds}.",
    3: "The incoming picture is the lamp's light: one cone, ray-marched through fine smoke, landing on {lamp_a} and {lamp_b}.\n"
       "The kick makes the smoke thicker. A shadow map cuts the {things_own} shadows out of the cone.",
    4: "Seen from straight above: a projector throws the incoming picture across the carpet at a raking angle.\n"
       "Its beam streaks the ray-marched fog. A shadow map gives the {floor_a} and the {floor_b} their long shadows.",
    5: "A projector high on the left throws the incoming picture across a big dark floor, through ray-marched fog.\n"
       "Kick and snare strike the ceiling tubes. A shadow map cuts the {things_own} shadows out of the picture.",
    8: "The projector lights the room with the negative of the incoming picture.\n"
       "The {wall} turns in the beam and a shadow map throws its shadow on the wall. A snare makes the lamp brighter.",
    10: "A hidden projector beside the floor tube throws the incoming picture, and the {tube}'s shadow, up the wall.\n"
        "Kick and snare strike the tube, and the tube and the picture flicker together.",
}

GREEN = (0.62, 1.0, 0.5)
BLUE = (0.2, 0.46, 1.0)
WARM = (1.0, 0.5, 0.15)
WHITE = (0.9, 0.95, 1.0)
PAPER = (0.86, 0.9, 0.7)
RED = (1.0, 0.07, 0.04)

# Every number a take can change. A take overrides what it needs. (What stands in a take: DEFAULTS['MODELS'].)
DEF = dict(
    cam=(0, 1.3, 6.5), tgt=(0, 1.2, 0), ctan=0.55, cdrift=0.15,
    lp=(-2.5, 1.6, 6), lt=(1, 1.5, -4), ltan=0.33, lcol=BLUE, lint=6.0, lfall=0.012,
    gobo=1, grot=0.0, ginv=0, gscale=1.0, sweep=(0, 0, 0), sheets=0.0, sheetsp=1.3,
    ntube=0, tlay=0, tint=1.0, tidle=0.25, tz0=3.5, tsp=3.2,
    lamp=(0, 0, 0), lampi=0.0,
    fog=0.10, fnoise=0.9, fscale=1.0, amb=0.004, exp=1.0, onebit=0,
    room=(7, 3.2, -5, 9),
    # Input picture (parent().par.Input) as the projector's slide: inp 1 = this take uses it, ing = gain,
    # inw = how far the lamp moves toward white so the picture keeps its colours.
    inp=1, ing=1.0, inw=0.7,
)

TAKES = [
    # 0 WORDS IN AIR: looking down a projector beam; the phrase hangs on layers of smoke, one figure cuts it.
    dict(cam=(2.5, 1.2, 8.5), tgt=(0.8, 1.85, 0), lp=(-5.5, 2.3, 4), lt=(3, 0.9, -4.5), ltan=0.42,
         lcol=BLUE, gobo=1, ing=1.25, sheets=1.0, sheetsp=3.1, sweep=(0.6, 0.1, 0), fog=0.11,
         ntube=4, tlay=1, tz0=-1.0, tsp=5.0, tidle=0.05, tint=0.6),
    # 1 BLINDS: into the light. Venetian blind shafts fan out of the back wall past one backlit thing.
    dict(cam=(0.8, 1.0, 7.0), tgt=(0.2, 1.25, 0), lp=(-5.5, 3.1, 0), lt=(2.0, 0, 0), ltan=0.42,
         lcol=GREEN, lint=5.0, gobo=2, sweep=(0.7, 0, 0), fog=0.07),
    # 2 RED PLANES: no beam at all, a comb of thin red light planes. Each shows a cross-section of the smoke
    # and draws a contour line round every solid thing it meets. Many subjects, seen from above.
    dict(cam=(2.2, 2.2, 7.0), tgt=(0.3, 0.8, 0), ctan=0.55, grot=0.35, lp=(-6.5, 1.5, 0.6), lt=(2, 1.1, -0.4), ltan=0.5,
         lcol=RED, lint=14.0, gobo=6, inp=0, fog=0.09, fnoise=1.5, fscale=3.2, amb=0.002, sweep=(0.3, 0, 0.3)),
    # 3 LAMP CONE: macro. One tungsten cone over two things casting shadows up into the smoke.
    dict(cam=(1.0, 1.25, 1.5), tgt=(-0.15, 1.15, 0), ctan=0.5, cdrift=0.05,
         lp=(-0.25, 1.8, -0.05), lt=(0.15, 0.87, 0.15), ltan=0.5, lcol=WARM, lint=30.0, lfall=6.0, gobo=0, fog=0.3, fscale=5.0, fnoise=1.2, amb=0.006),
    # 4 FLOOR TYPE: straight down. Tiled phrases thrown across the carpet, two long shadows.
    dict(cam=(0.5, 8.2, 0.8), tgt=(0.5, 0, 0.3), ctan=0.5, cdrift=0.1,
         lp=(-4.5, 3.5, 2.5), lt=(1.5, 0, -0.5), ltan=0.5, lcol=GREEN, lint=9.0, gobo=4, fog=0.07,
         room=(8, 9, -7, 7)),
    # 5 GRID WINDOW: wide. A ruled sheet's lines and boxes as a lattice of light across a big dark floor, tiny things on it.
    dict(cam=(4.5, 2.7, 9.0), tgt=(0.0, 0.7, -1), ctan=0.7, lp=(-7.5, 5.0, 0.5), lt=(1.5, 0, -1), ltan=0.5,
         lcol=BLUE, lint=6.0, gobo=3, sweep=(0.5, 0, 0.5), fog=0.05, room=(9, 5.5, -9, 11),
         ntube=8, tlay=1, tz0=4.0, tsp=4.0, tidle=0.0, tint=0.5,
         lamp=(0.2, 1.45, 0.5), lampi=0.5),
    # 6 LEANING TUBES: bare tubes of three colours propped on a wall, mirrored in the floor, a silhouette in front.
    dict(cam=(-1.5, 1.0, 5.0), tgt=(0.3, 1.1, -2.5), lint=0.0, gobo=0, inp=0, ntube=5, tlay=2, tz0=-2.2, tsp=0.9,
         tidle=0.22, tint=0.6, fog=0.03, room=(6, 3.4, -2.5, 9)),
    # 7 ONE BIT: the whole machine dithered to black and white; a spoked wheel turning behind a silhouette.
    dict(cam=(-0.25, 0.9, 6.0), tgt=(0.5, 1.2, -3), cdrift=0.05, lp=(-0.4, 1.0, -4.5), lt=(0.1, 0.95, 6), ltan=0.6,
         lcol=WHITE, lint=1.0, gobo=5, onebit=1, inp=0, fog=0.06),
    # 8 SHADOW PLAY: negative. A bright wall printed with dark phrases; a giant shadow turns on it.
    dict(cam=(-2.5, 1.3, 7.5), tgt=(0, 1.6, -5), ctan=0.55, lp=(1.5, 1.0, 7), lt=(-0.5, 1.9, -5), ltan=0.5,
         lcol=PAPER, lint=4.0, gobo=4, ginv=1, gscale=0.8, sweep=(0.4, 0.1, 0), fog=0.04),
    # 9 CORRIDOR: no projector. A row of ceiling tubes down a long corridor; light races toward the camera.
    dict(cam=(0.5, 1.2, 6.5), tgt=(-0.2, 1.7, -8), ctan=0.6, lint=0.0, gobo=0, inp=0,
         ntube=8, tlay=0, tz0=3.0, tsp=3.4, tidle=0.03, tint=1.6, fog=0.04, room=(2.4, 2.7, -40, 8)),
    # 10 FLOOR TUBE: macro at carpet level. One tube lying on the floor throws a giant shadow up the wall.
    dict(cam=(1.9, 0.28, 2.6), tgt=(0.1, 0.55, -0.4), ctan=0.5, cdrift=0.05,
         lp=(-0.5, 0.1, 0.5), lt=(0.3, 0.55, -1.0), ltan=0.95, lcol=GREEN, lint=3.5, lfall=0.6, gobo=0,
         ntube=1, tlay=3, tz0=0.2, tidle=0.6, tint=0.25, fog=0.05, fscale=2.5, room=(4, 3.2, -2.2, 6)),
]

H = "op('hub')"
K = "op('tk')"
S = "op('shot')"


def described(nouns):
    """DESCRIBE, CAPTIONS and CAPTIONS_IN with the {names} filled in from NOUNS (capitals in the atlas cells)."""
    caps = {k.upper(): v.upper() for k, v in nouns.items()}
    return ({k: [c.format(**caps) for c in cells] for k, cells in DESCRIBE.items()},
            [c.format(**nouns) for c in CAPTIONS],
            {k: c.format(**nouns) for k, c in CAPTIONS_IN.items()})


def _flat(take):
    """One take as {channel: number}."""
    d = dict(DEF)
    d.update(take)
    out = {}
    for k, v in d.items():
        if isinstance(v, tuple):
            for i, x in enumerate(v):
                out["%s%d" % (k, i)] = float(x)
        else:
            out[k] = float(v)
    return out


def _by_take(values):
    """An expression that picks values[take]."""
    return "(%s)[int(parent().par.Take)%%%d]" % (",".join("%g" % v for v in values), len(TAKES))


def _text_cell(scene, i, txt, prefix="t", x=-1000, w=512):
    t = scene.create(td.textTOP, "%s%d" % (prefix, i))
    t.par.text = txt
    t.par.fontfile.expr = ARCHIVO
    t.par.bold.expr = "not %s" % ARCHIVO
    t.par.fontsizexunit = "pixels"
    t.par.fontsizex = 104
    t.par.fontautosize = "fitiffat"
    t.par.wordwrap = False
    t.par.alignx = "center"
    t.par.aligny = "center"
    t.par.linespacing = -14
    t.par.outputresolution = "custom"
    t.par.resolutionw, t.par.resolutionh = w, 256
    t.par.bgalpha = 1
    t.nodeX, t.nodeY = x, 900 - 120 * i
    return t


def _atlas(scene, name, pattern, x, fit="fill"):
    atlas = scene.create(td.layoutTOP, name)
    atlas.par.tops = pattern
    atlas.par.align = "gridrows"
    atlas.par.numcols = 2
    atlas.par.fit = fit
    atlas.par.outputresolution = "custom"
    atlas.par.resolutionw, atlas.par.resolutionh = 1024, 1024
    atlas.par.bgcolorr, atlas.par.bgcolorg, atlas.par.bgcolorb, atlas.par.bgcolora = 0, 0, 0, 1
    atlas.nodeX, atlas.nodeY = x, 500
    return atlas


def _file_dat(scene, name, fname, x, y):
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here('shaders/%s')" % fname
    d.par.syncfile = True
    d.par.loadonstartpulse.pulse()
    d.nodeX, d.nodeY = x, y
    return d


def _uniforms(o, uniforms):
    o.seq.vec.numBlocks = len(uniforms)
    for i, (name, exprs) in enumerate(uniforms):
        getattr(o.par, "vec%dname" % i).val = name
        for axis, e in zip("xyzw", exprs):
            getattr(o.par, "vec%dvalue%s" % (i, axis)).expr = e


def _drop_docked(scene, name):
    for suffix in ("_pixel", "_compute", "_vertex"):
        d = scene.op(name + suffix)
        if d:
            d.destroy()


def _teapot_bounds(scene, paths):
    """Bounds of TouchDesigner's bundled teapot, the stand-in for every model when there is no library."""
    probe = scene.create(td.fileinPOP, "teapot_probe")
    probe.par.file.expr = "mod.paths.samples() + '/Geo/UtahTeapot.obj'"
    probe.cook(force=True)
    b = probe.bounds()
    lo, hi = tuple(float(v) for v in b.min), tuple(float(v) for v in b.max)
    probe.destroy()
    if min(h - l for l, h in zip(lo, hi)) < 1e-4:        # not loaded yet, or a different sample: use the record
        return TEAPOT_MIN, TEAPOT_MAX
    return lo, hi


def _fit_standin(geo, slug, size, tmin, tmax):
    """A Transform POP after the mesh. With the library model it does nothing (scale 1); with no library the
    mesh is the teapot, and this fits it into the box the real model would fill, so it stands where the take
    put the model, at about the size the take was composed for. An expression, so a saved .tox works either way."""
    have = "mod.paths.have('models/%s/model.obj')" % slug
    mesh = geo.op("mesh")
    fit = geo.create(td.transformPOP, "fit")
    fit.inputConnectors[0].connect(mesh)
    for axis, s, lo, hi in zip("xyz", size, tmin, tmax):
        k = STANDIN_STRETCH * s / (hi - lo) + (1 - STANDIN_STRETCH) * min(a / (h - l) for a, l, h in zip(size, tmin, tmax))
        centre = 0.5 * (lo + hi)
        # y: stand the stand-in on the bottom of the box whatever its height
        t = (-0.5 * s - lo * k) if axis == "y" else -centre * k
        getattr(fit.par, "s" + axis).expr = "1 if %s else %.5g" % (have, k)
        getattr(fit.par, "t" + axis).expr = "0 if %s else %.5g" % (have, t)
    mesh.render = mesh.display = False
    fit.render = fit.display = True
    fit.nodeX, fit.nodeY = mesh.nodeX + 160, mesh.nodeY
    return fit


def build():
    LIB = {"op": op}
    exec(open(td.project.folder + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), LIB)
    scene = LIB["new_scene"](SLUG, 2250, -1100)
    paths = scene.op("local/modules/paths").module      # the installed module: it sees the Assets parameter
    nt = len(TAKES)
    W = LIB["scene_words"](scene, DEFAULTS)
    assert len(W["PHRASES"]) == NPHRASES, "the atlas has 8 cells"
    describe, captions, captions_in = described(W["NOUNS"])
    # placed[take] = {model: (x, z, yaw, scale, spin, y of its base)}
    placed = [{} for _ in TAKES]
    for row in W["MODELS"]:
        assert row[1] not in placed[int(row[0])], "a model stands once in a take: %r" % (row,)
        placed[int(row[0])][row[1]] = tuple(row[2:8])

    # --- per-take numbers: one channel each, picked by shot.take ---
    flats = [_flat(t) for t in TAKES]
    names = list(flats[0].keys())
    tk = scene.create(td.constantCHOP, "tk")
    tk.seq.const.numBlocks = len(names)
    for i, nme in enumerate(names):
        getattr(tk.par, "const%dname" % i).val = nme
        getattr(tk.par, "const%dvalue" % i).expr = _by_take([f[nme] for f in flats])
    tk.nodeX, tk.nodeY = -400, 500

    # --- the rig: camera and projector after drift, sweep and seed ---
    ph = "(%s['seed']*6.283)" % S
    ev = "%s['evolve']" % H
    dolly = "(0.84+0.32*%s['seed'])" % S                 # each shot stands a little nearer or further
    rig_ch = [
        ("cpx", "%s['tgt0'] + (%s['cam0']-%s['tgt0'])*%s + %s['cdrift']*math.sin(%s*0.6+%s)" % (K, K, K, dolly, K, ev, ph)),
        ("cpy", "%s['cam1'] + %s['cdrift']*0.35*math.sin(%s*0.43+%s*2)" % (K, K, ev, ph)),
        ("cpz", "%s['tgt2'] + (%s['cam2']-%s['tgt2'])*%s + %s['cdrift']*math.cos(%s*0.5+%s)" % (K, K, K, dolly, K, ev, ph)),
        ("ctx", "%s['tgt0']" % K), ("cty", "%s['tgt1']" % K), ("ctz", "%s['tgt2']" % K),
        ("lpx", "%s['lp0']" % K), ("lpy", "%s['lp1']" % K), ("lpz", "%s['lp2']" % K),
        ("ltx", "%s['lt0'] + %s['sweep0']*math.sin(%s['bar_pos']*math.pi/2+%s)" % (K, K, H, ph)),
        ("lty", "%s['lt1'] + %s['sweep1']*math.sin(%s['bar_pos']*math.pi+%s)" % (K, K, H, ph)),
        ("ltz", "%s['lt2'] + %s['sweep2']*math.cos(%s['bar_pos']*math.pi/2+%s)" % (K, K, H, ph)),
    ]
    rig = scene.create(td.constantCHOP, "rig")
    rig.seq.const.numBlocks = len(rig_ch)
    for i, (nme, e) in enumerate(rig_ch):
        getattr(rig.par, "const%dname" % i).val = nme
        getattr(rig.par, "const%dvalue" % i).expr = e
    rig.nodeX, rig.nodeY = -200, 500

    # --- slow tails of the kick and snare: how long a struck tube stays bright ---
    selh = scene.create(td.selectCHOP, "sel_hits")
    selh.par.chop = "hub"
    selh.par.channames = "hit_low hit_mid"
    slow = scene.create(td.lagCHOP, "slow")
    slow.par.lag1, slow.par.lag2 = 0, 0.8
    slow.inputConnectors[0].connect(selh)
    selh.nodeX, selh.nodeY = -400, -220
    slow.nodeX, slow.nodeY = -240, -220

    # --- text atlas ---
    for i, txt in enumerate(W["PHRASES"]):
        _text_cell(scene, i, txt, w=int(W["CELL"]))
    atlas = _atlas(scene, "atlas", "t[0-7]", -800, "fill" if int(W["CELL"]) == 512 else "fitbest")

    # --- Describe atlases (one per text take) and the Input picture, all behind one Switch TOP ---
    # slide = what the projector shines through: 0 the phrase atlas, 1.. the Describe atlases, last = the Input TOP.
    dtakes = sorted(describe)
    for j, k in enumerate(dtakes):
        for i, txt in enumerate(describe[k]):
            # tiled takes: a narrower cell centred in its tile, so neighbouring phrases do not run together
            _text_cell(scene, i, txt, "d%d_" % k, -1500 - 160 * j, 512 if TAKES[k].get("gobo", 1) == 1 else 432)
        _atlas(scene, "atlas_d%d" % k, "d%d_[0-7]" % k, -1500 - 160 * j, "fitbest").cook(force=True)
    # 'inp': is Input a TOP we may read (not our own output), and does this take use it
    P = "parent().par.Input.eval()"
    ok = "(1 if (%s and op(%s) is not None and op(%s).isTOP and op(%s).path != op('out1').path) else 0)" % (P, P, P, P)
    inp = scene.create(td.constantCHOP, "inp")
    inp.par.name0, inp.par.name1 = "valid", "on"
    inp.par.value0.expr = ok
    inp.par.value1.expr = "%s * %s['inp']" % (ok, K)
    inp.nodeX, inp.nodeY = -1200, 330
    insel = scene.create(td.selectTOP, "in_pic")
    insel.par.top.expr = "%s if op('inp')['valid'] else 'atlas'" % P
    insel.nodeX, insel.nodeY = -1200, 200
    slide = scene.create(td.switchTOP, "slide")
    for src in [atlas] + [scene.op("atlas_d%d" % k) for k in dtakes] + [insel]:
        src.outputConnectors[0].connect(slide)
    dsel = [0] * nt
    for j, k in enumerate(dtakes):
        dsel[k] = j + 1
    slide.par.index.expr = "%d if op('inp')['on'] else (%s if parent().par.Describe else 0)" % (len(dtakes) + 1, _by_take(dsel))
    slide.nodeX, slide.nodeY = -1000, 330

    # --- Describe caption: one strip along the bottom, drawn by grade.frag only while Describe is on ---
    cap = scene.create(td.textTOP, "caption")
    cap_in = tuple(captions_in.get(i, captions[i]) for i in range(nt))
    cap.par.text.expr = "((%r) if op('inp')['on'] else (%r))[int(parent().par.Take)%%%d] if parent().par.Describe else ''" % (
        cap_in, tuple(captions), nt)
    cap.par.fontfile.expr = BARLOW
    cap.par.fontsizexunit = "pixels"
    cap.par.fontsizex = 27
    cap.par.fontautosize = "fitiffat"
    cap.par.wordwrap = False
    cap.par.alignx = "left"
    cap.par.aligny = "center"
    cap.par.outputresolution = "custom"
    cap.par.resolutionw, cap.par.resolutionh = CAP_W, CAP_H
    cap.par.bgalpha = 1
    cap.nodeX, cap.nodeY = 740, -180

    # --- library models, placed per take ---
    used = []
    for models in placed:
        for m in models:
            if m not in used:
                used.append(m)
    tmin, tmax = _teapot_bounds(scene, paths)
    for j, m in enumerate(used):
        size = W["SIZES"][m]
        size_y = size[1]
        geo = LIB["import_model"](scene, m, m)
        _fit_standin(geo, m, size, tmin, tmax)
        geo.par.material = ""                           # both renders use the G-buffer override material:
        for unused in ("tex", "mat"):                    # the model's own texture and PBR MAT would only cost a load
            geo.op(unused).destroy()
        pl = [models.get(m) for models in placed]
        on = [1 if p else 0 for p in pl]
        pl = [p or (0, 0, 0, 1, 0, 0) for p in pl]
        geo.par.render.expr = _by_take(on)
        geo.par.tx.expr = _by_take([p[0] for p in pl])
        geo.par.ty.expr = _by_take([p[5] + p[3] * size_y * 0.5 for p in pl])
        geo.par.tz.expr = _by_take([p[1] for p in pl])
        geo.par.ry.expr = "%s + %s*%s*40 + %s['seed']*%s*360" % (
            _by_take([p[2] for p in pl]), _by_take([p[4] for p in pl]), ev, S, _by_take([p[4] for p in pl]))
        geo.par.scale.expr = _by_take([p[3] for p in pl])
        geo.op("mesh").cook(force=True)              # a hidden model would otherwise load on its first take: a hitch
        geo.op("fit").cook(force=True)
        geo.nodeX, geo.nodeY = -800 + 160 * (j % 4), 200 - 140 * (j // 4)

    # --- two G-buffers with our own projection: from the camera, and from the projector (the shadow map) ---
    vert = _file_dat(scene, "gbuf_vert", "gbuf_vert.glsl", 0, 420)
    pix = _file_dat(scene, "gbuf_frag", "gbuf_frag.glsl", 0, 320)
    cam = scene.create(td.cameraCOMP, "cam")
    cam.nodeX, cam.nodeY = -160, 200
    views = [
        ("cam", ["cpx", "cpy", "cpz"], "%s['ctan']" % K, ["ctx", "cty", "ctz"], "1280.0/720.0", 1280, 720),
        ("lgt", ["lpx", "lpy", "lpz"], "%s['ltan']" % K, ["ltx", "lty", "ltz"], "1", 1024, 1024),
    ]
    for j, (nme, ro, tan, ta, aspect, w, h) in enumerate(views):
        mat = scene.create(td.glslMAT, "m_" + nme)
        mat.par.vdat = vert.name
        mat.par.pdat = pix.name
        _drop_docked(scene, "m_" + nme)
        _uniforms(mat, [
            ("uRo", ["op('rig')['%s']" % c for c in ro] + [tan]),
            ("uTa", ["op('rig')['%s']" % c for c in ta] + [aspect]),
        ])
        mat.nodeX, mat.nodeY = 0, 200 - 140 * j
        r = scene.create(td.renderTOP, "gb_" + nme)
        r.par.camera = cam.name
        r.par.geometry = " ".join(used)
        r.par.lights = ""
        r.par.overridemat = mat.name
        r.par.antialias = r.par.antialias.menuNames[0]
        r.par.cullface = "neither" if "neither" in r.par.cullface.menuNames else r.par.cullface.menuNames[0]
        r.par.outputresolution = "custom"
        r.par.resolutionw, r.par.resolutionh = w, h
        r.par.format = "rgba32float"
        r.nodeX, r.nodeY = 180, 200 - 140 * j

    # --- the beam shader ---
    frag = _file_dat(scene, "beam_frag", "beam.frag", 380, 380)
    beam = scene.create(td.glslTOP, "beam")
    beam.par.pixeldat = frag.name
    _drop_docked(scene, "beam")
    beam.par.outputresolution = "custom"
    beam.par.resolutionw, beam.par.resolutionh = 1280, 720
    beam.par.format = "rgba16float"
    beam.par.inputfiltertype = "linear"
    scene.op("gb_cam").outputConnectors[0].connect(beam.inputConnectors[0])
    scene.op("gb_lgt").outputConnectors[0].connect(beam.inputConnectors[1])
    slide.outputConnectors[0].connect(beam.inputConnectors[2])
    tm = "absTime.seconds%1000"
    _uniforms(beam, [
        ("uCamP", ["op('rig')['cpx']", "op('rig')['cpy']", "op('rig')['cpz']", "%s['ctan']" % K]),
        ("uCamT", ["op('rig')['ctx']", "op('rig')['cty']", "op('rig')['ctz']", "1280.0/720.0"]),
        ("uLgtP", ["op('rig')['lpx']", "op('rig')['lpy']", "op('rig')['lpz']", "%s['ltan']" % K]),
        ("uLgtT", ["op('rig')['ltx']", "op('rig')['lty']", "op('rig')['ltz']", "%s['gobo']" % K]),
        ("uLgtC", ["%s['lcol%d']*%s['lint']*(0.8+0.3*min(%s['pulse'],1)+0.6*min(%s['hit_mid'],1.2))" % (K, i, K, H, H) for i in range(3)]
         + ["%s['sheets']" % K]),
        ("uGobo", ["%s['section'] + int(%s['seed']*8)" % (H, S),
                   "%s['grot'] + (%s['seed']-0.5)*0.25" % (K, S),
                   "%s['beat_pos']" % H,
                   "0.36 + 0.2*math.sin(%s['bar_pos']*math.pi)" % H]),
        ("uGobo2", ["%s['ginv']" % K, "%s['sheetsp']" % K, "%s['gscale']" % K, "%s['section']" % H]),
        ("uTube", ["%s['ntube']" % K, "%s['tlay']" % K,
                   "%s['tint']*(0.7+0.6*min(max((%s['energy']-0.33)/0.32,0),1))" % (K, H), tm]),
        ("uTube2", ["%s['tidle']" % K, "%s['tz0']" % K, "%s['tsp']" % K, "%s['lfall']" % K]),
        ("uTubeHit", ["%s['hits_low']" % H, "%s['hits_mid']" % H, "op('slow')['hit_low']", "op('slow')['hit_mid']"]),
        ("uHit", ["min(%s['hit_low'],1.5)" % H, "min(%s['hit_mid'],1.5)" % H, "min(%s['hit_high'],1.5)" % H,
                  "%s['pulse']" % H]),
        ("uLamp", ["%s['lamp0']" % K, "%s['lamp1']" % K, "%s['lamp2']" % K,
                   "%s['lampi']*(0.7+0.6*min(%s['vocals'],1.5))" % (K, H)]),
        ("uFog", ["%s['fog']*(0.6+0.35*min(%s['bass'],2)+0.45*min(op('slow')['hit_low'],1.2))" % (K, H), ev, "%s['fnoise']" % K, "%s['amb']" % K]),
        ("uMisc", ["%s['seed']" % S, "%s['age']" % S, "%s['exp']" % K, "%s['fscale']" % K]),
        ("uRoom", ["%s['room%d']" % (K, i) for i in range(4)]),
        ("uIn", ["op('inp')['on']", "%s['ing']" % K, "%s['inw']" % K, "0"]),
    ])
    beam.nodeX, beam.nodeY = 560, 100

    # --- glow and grade ---
    glow = scene.create(td.blurTOP, "glow")
    glow.par.outputresolution = "quarter"
    glow.par.size = 9
    glow.inputConnectors[0].connect(beam)
    glow.nodeX, glow.nodeY = 740, -40
    gfrag = _file_dat(scene, "grade_frag", "grade.frag", 740, 380)
    grade = scene.create(td.glslTOP, "grade")
    grade.par.pixeldat = gfrag.name
    _drop_docked(scene, "grade")
    grade.par.outputresolution = "custom"
    grade.par.resolutionw, grade.par.resolutionh = 1280, 720
    grade.par.format = "rgba8fixed"
    beam.outputConnectors[0].connect(grade.inputConnectors[0])
    glow.outputConnectors[0].connect(grade.inputConnectors[1])
    cap.outputConnectors[0].connect(grade.inputConnectors[2])
    _uniforms(grade, [
        ("uDesc", ["1 if parent().par.Describe else 0", "%g" % (CAP_H / 720.0), "%g" % ((1280 - CAP_W) / 2560.0), "%g" % (CAP_W / 1280.0)]),
        ("uMisc", ["%s['seed']" % S, "%s['age']" % S, "%s['exp']" % K, "%s['onebit']" % K]),
        ("uTime", [tm, "0", "0", "0"]),
    ])
    grade.nodeX, grade.nodeY = 920, 60
    grade.outputConnectors[0].connect(scene.op("out1").inputConnectors[0])
    return scene.path
