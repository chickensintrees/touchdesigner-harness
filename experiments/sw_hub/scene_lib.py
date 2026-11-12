# Shared scaffolding for scene networks that read the audio hub.
# Use from a scene's build.py (which runs inside TouchDesigner):
#
#     LIB = {'op': op}
#     exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
#     scene = LIB['new_scene']('sc_example')
#
# Everything here is a starting point; a scene may build whatever it likes inside its COMP.
import td

# ---- where things are -------------------------------------------------------
# See paths_module.py. The same file is installed in every scene as the module
# DAT local/modules/paths, so parameters can use it in expressions.
_REPO = td.project.folder.replace(chr(92), "/")
_PATHS_FILE_EXPR = "project.folder.replace(chr(92), '/') + '/experiments/sw_hub/paths_module.py'"
_paths = {"project": td.project, "app": td.app, "me": None}
exec(open(_REPO + "/experiments/sw_hub/paths_module.py", encoding="utf-8").read(), _paths)
repo, assets, asset, have = _paths["repo"], _paths["assets"], _paths["asset"], _paths["have"]
font, samples, experiment = _paths["font"], _paths["samples"], _paths["experiment"]
model_file, model_texture = _paths["model_file"], _paths["model_texture"]


def add_paths(comp):
    """Install the paths module in a component: <comp>/local/modules/paths.

    Afterwards any parameter inside it can be an expression such as
    mod.paths.here('shaders/a.frag'), mod.paths.font('chicago') or
    mod.paths.model_file('phone'). Set every parameter that names a file this
    way (par.file.expr = "..."), never as a constant: a constant puts this
    machine's folder into the saved .tox and the snapshot.
    """
    local = comp.op("local") or comp.create(td.baseCOMP, "local")
    modules = local.op("modules") or local.create(td.baseCOMP, "modules")
    dat = modules.op("paths") or modules.create(td.textDAT, "paths")
    dat.par.file.expr = _PATHS_FILE_EXPR
    dat.par.syncfile = True
    dat.par.loadonstartpulse.pulse()
    local.nodeX, local.nodeY = -400, 460
    return dat


def scene_paths(scene):
    """The paths module as installed in this scene, so lookups honour its Assets parameter."""
    return scene.op("local/modules/paths").module


def scene_words(scene, defaults):
    """The scene's words: `defaults`, with names replaced by the pack's
    scenes/<slug>/words.json when it has one. Read once, when the scene is built."""
    return scene_paths(scene).words(defaults)


HUB_FEED = "/project1/sw_hub/feed"
HUB_SPECTRUM = "/project1/sw_hub/spectex"

# A scene cooks only while it is on screen (the hub's Active Scene), while its own
# Preview toggle is on, or while the hub's Cook All Scenes toggle is on.
DRIVER = '''def onFrameStart(frame):
    hub = op('/project1/sw_hub')
    me_on = parent().par.Preview.eval()
    if hub is not None:
        me_on = me_on or hub.par.Solo.eval() or hub.par.Scene.eval() == parent().name
    if me_on:
        op('hub').cook(force=True)
        op('out1').cook(force=True)
    return
'''


def new_scene(slug, x=0, y=0):
    """Create (or recreate) /project1/<slug> with out1, a hub feed and a cook driver."""
    root = op("/project1")
    old = root.op(slug)
    kept_assets = ""
    if old:
        if hasattr(old.par, "Assets"):
            kept_assets = old.par.Assets.eval()  # so a no-assets trial survives the rebuild that tests it
        old.destroy()
    scene = root.create(td.baseCOMP, slug)
    scene.nodeX, scene.nodeY = x, y
    page = scene.appendCustomPage("Scene")
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = True
    # The cutter sets these before each shot, so a scene never has to look the same twice.
    page.appendInt("Take", label="Take (which variation)")[0].val = 0
    page.appendFloat("Seed", label="Shot Seed (0-1)")[0].val = 0
    page.appendFloat("Shotstart", label="Shot Start (absTime s)")[0].val = 0
    # Describe: the words on screen say what the technique is (for the gallery and the website).
    page.appendToggle("Describe", label="Describe (words explain the technique)")[0].val = False
    # Input: path of another scene's output TOP to use as this scene's source picture. Blank = its own.
    page.appendStr("Input", label="Input TOP (another scene's out1)")[0].val = ""
    # Assets: blank means the normal assets folder. Point it at an empty folder to see
    # the scene with no assets at all (teapot, default font, stand-in pictures).
    page.appendFolder("Assets", label="Assets Folder (blank = default)")[0].val = kept_assets

    add_paths(scene)

    hub = scene.create(td.selectCHOP, "hub")
    hub.par.chop = HUB_FEED
    shot = scene.create(td.constantCHOP, "shot")
    shot.par.name0, shot.par.name1, shot.par.name2 = "take", "seed", "age"
    shot.par.value0.expr = "parent().par.Take"
    shot.par.value1.expr = "parent().par.Seed"
    shot.par.value2.expr = "max(0, absTime.seconds - parent().par.Shotstart)"
    shot.nodeX, shot.nodeY = -400, 330
    spectrum = scene.create(td.selectTOP, "spectrum")
    spectrum.par.top = HUB_SPECTRUM
    out1 = scene.create(td.outTOP, "out1")
    driver = scene.create(td.executeDAT, "cook_driver")
    driver.text = DRIVER
    driver.par.framestart = True
    driver.par.active = True
    hub.nodeX, hub.nodeY = -400, 200
    spectrum.nodeX, spectrum.nodeY = -400, 60
    driver.nodeX, driver.nodeY = -400, -80
    out1.nodeX, out1.nodeY = 1200, 0
    return scene




def import_model(scene, name, slug):
    """Add library model <slug> to the scene as a Geometry COMP named <name>.

    Inside it: 'mesh' (File In POP reading model.obj: one joined mesh, centred on
    the origin, longest side 1 unit, Y up, with normals and UVs), 'tex' (the base
    colour image) and 'mat' (a PBR MAT using it). Returns the Geometry COMP.
    TouchDesigner's FBX COMP does not read .glb, which is why the library holds
    converted copies (tools/models/convert_models.py). With no library in the assets
    folder the mesh is TouchDesigner's bundled teapot and the material is plain.
    """
    old = scene.op(name)
    if old:
        old.destroy()
    geo = scene.create(td.geometryCOMP, name)
    for child in geo.children:
        child.destroy()
    mesh = geo.create(td.fileinPOP, "mesh")
    mesh.par.file.expr = "mod.paths.model_file(%r)" % slug
    mesh.render = True
    mesh.display = True
    tex = geo.create(td.moviefileinTOP, "tex")
    texture = scene_paths(scene).model_texture(slug)  # the scene's own pack, which its Assets parameter may name
    tex.par.file.expr = "mod.paths.model_texture(%r)" % slug
    mat = geo.create(td.pbrMAT, "mat")
    if texture:
        mat.par.basecolormap = tex.path  # with no library the fallback teapot is plain
    mat.par.metallic, mat.par.roughness = 0, 0.6  # the defaults (1, 1) render near black
    geo.par.material = mat.path  # absolute: a relative path silently falls back to grey
    return geo
