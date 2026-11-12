# Builder for /project1/sc_exploded_view. Run inside TouchDesigner (see sw_hub/SCENE_BRIEF.md).
# Idempotent: destroys and rebuilds the whole scene.
# The takes (TAKES table), palettes and all per-frame decisions are in logic.py beside this file.
# see: experiments/sc_exploded_view/NOTES.md
import json

import td

# No folder is named here: the repository is where the open project file is saved, and every file
# parameter is an expression on mod.paths (experiments/sw_hub/paths_module.py). see: NOTES.md "Assets"
REPO = td.project.folder.replace(chr(92), '/')
SLUG = 'sc_exploded_view'
HERE = REPO + '/experiments/' + SLUG

# Everything the scene says and every model it draws. A pack may replace any of these names in its
# scenes/sc_exploded_view/words.json (experiments/sw_hub/paths_module.py, words()); build() reads
# them once and hands them to logic.py through the Text DAT 'words'. see: NOTES.md "Words and models"
DEFAULTS = {
    # name, size in units (x, y, z), triangles, drawing title, catalogue number, plain name (Describe).
    # The first row is the parts file below; the others are <assets>/models/<name>/model.obj.
    'MODELS': [
        ['parts', [0.8823, 1.0, 0.883], 29095, 'LANDER, FOUR LEG', 'CAT-0047', 'LANDER'],
        ['gramophone', [0.7399, 1.0, 0.7372], 29161, 'GRAMOPHONE, WIND-UP', 'CAT-0011', 'GRAMOPHONE'],
        ['space_helmet', [1.0, 0.9112, 0.9933], 29560, 'HELMET, PRESSURE', 'CAT-0019', 'SPACE HELMET'],
        ['skeleton_key', [0.1223, 1.0, 0.4343], 29544, 'KEY, SKELETON', 'CAT-0002', 'SKELETON KEY'],
        ['astrolabe', [0.6383, 1.0, 0.6387], 29403, 'SPHERE, ARMILLARY', 'CAT-0012', 'ASTROLABE'],
        ['hourglass', [0.5482, 1.0, 0.5481], 29577, 'HOURGLASS, THREE POST', 'CAT-0027', 'HOURGLASS'],
        ['ribbon_loop', [0.7078, 1.0, 0.5891], 29404, 'KNOT, BRONZE', 'CAT-0001', 'BRONZE KNOT'],
        ['balanced_solids', [0.2997, 1.0, 0.2996], 29390, 'SOLIDS, BALANCED', 'CAT-0031', 'BALANCED SOLIDS'],
        ['wire_cage', [0.9973, 0.97, 1.0], 28800, 'CAGE, GEODESIC', 'CAT-0040', 'WIRE CAGE'],
        ['amphora', [0.5717, 1.0, 0.5719], 29930, 'AMPHORA, TWO HANDLE', 'CAT-0008', 'AMPHORA'],
        ['marble_bust', [0.5578, 1.0, 0.5336], 28229, 'BUST, MARBLE', 'CAT-0016', 'MARBLE BUST'],
        ['broken_column', [0.7451, 1.0, 0.7748], 29853, 'COLUMN, BROKEN', 'CAT-0006', 'BROKEN COLUMN'],
        ['rubber_duck', [1.0, 0.7802, 0.8354], 29957, 'DUCK, RUBBER', 'CAT-0004', 'RUBBER DUCK'],
        ['crystal_cluster', [1.0, 0.6487, 0.8586], 29184, 'CRYSTALS, CLUSTER', 'CAT-0022', 'CRYSTAL CLUSTER'],
        ['traffic_cone', [0.6053, 1.0, 0.6052], 29872, 'CONE, TRAFFIC', 'CAT-0035', 'TRAFFIC CONE'],
        ['pierced_stone', [0.7907, 1.0, 0.3366], 28280, 'STONE, PIERCED', 'CAT-0009', 'PIERCED STONE'],
    ],
    # Which models each take may draw (a new song section picks the next one).
    'POOLS': {
        'take_three_view': ['space_helmet', 'gramophone', 'astrolabe', 'hourglass', 'ribbon_loop', 'wire_cage',
                            'amphora', 'rubber_duck'],
        'take_parts_sheet': ['gramophone', 'balanced_solids', 'ribbon_loop', 'traffic_cone', 'hourglass', 'marble_bust'],
        'take_section_sweep': ['space_helmet', 'rubber_duck', 'amphora', 'crystal_cluster', 'marble_bust'],
        'take_slab_strip': ['traffic_cone', 'space_helmet', 'marble_bust', 'amphora', 'broken_column', 'balanced_solids'],
        'take_contour_scan': ['marble_bust', 'space_helmet', 'amphora', 'ribbon_loop', 'broken_column', 'gramophone',
                              'pierced_stone', 'rubber_duck'],
        'take_rosette': ['skeleton_key', 'gramophone', 'rubber_duck', 'amphora', 'space_helmet', 'astrolabe'],
        'take_bill_of_materials': ['balanced_solids', 'hourglass', 'marble_bust', 'amphora', 'traffic_cone', 'astrolabe'],
    },
    # With an Input picture the takes that wrap it round the part use the models with broad faces.
    'INPUT_POOLS': {
        'take_contour_scan': ['space_helmet', 'amphora', 'marble_bust', 'rubber_duck', 'pierced_stone'],
        'take_section_sweep': ['space_helmet', 'rubber_duck', 'amphora', 'marble_bust'],
        'take_three_view': ['space_helmet', 'marble_bust', 'amphora', 'rubber_duck', 'gramophone'],
    },
    # Models that are thin double-walled shells, not solids: through a cut the camera sees the inner
    # skin, and the shader hatches it as the cut face (shaders/part_pixel.glsl). Only convex shapes.
    'CAP_INSIDE': ['rubber_duck', 'amphora', 'marble_bust', 'crystal_cluster', 'traffic_cone', 'balanced_solids',
                   'broken_column'],
    # The object that comes apart into separate shapes (takes 0, 2 and 7): a parts file made by
    # prep_parts.py, looked up with mod.paths.scene_file so a pack's own copy wins, and how each of
    # the three takes frames it and throws it about.
    'PARTS': {
        'name': 'parts', 'obj': 'meshes/parts.obj', 'info': 'meshes/parts.json',
        'iso': {'scale': 1.1, 'ox': -0.40, 'oy': -0.02, 'yaw': 0.62, 'yaw_sway': 0.22, 'pitch': 0.42,
                'pitch_sway': 0.08, 'chaos': 0.35, 'spread': 0.6, 'lift': 0.06, 'rowlift': 0.0,
                'dim': [0.4412, -0.5, 0.4415], 'mm': 300.0},
        'macro': {'scale': 1.9, 'pitch': 0.35, 'pitch_sway': 0.2, 'drift': [0.3, 0.2], 'chaos': 0.75, 'spread': 0.9,
                  'lift': 0.05, 'casesink': 0.22, 'camz': 1.7, 'fov': 70.0},
        'plan': {'pitch': 0.16, 'scale': 1.15, 'oy': 0.22, 'chaos': 0.45, 'spread': 0.8, 'lift': 0.05},
    },
    # Typed along the sheet while the parts land (takes 0 and 7), one per song section.
    'PHRASES': [
        'NOTHING HERE IS PRERENDERED.', 'EVERY FRAME IS MADE NOW.', 'SOUND IN. PICTURE OUT.',
        'OBJECT OF UNKNOWN USE. DO NOT TOUCH.', 'THE KICK MOVES THE PARTS.',
        'HANDLE WITH BOTH HANDS. THEN LISTEN.', 'THIS PLATE IS MADE OF SOUND.',
        'CATALOGUE NO. 0047: FOUND.', 'SIXTY FRAMES A SECOND, EVERY SECOND', 'HERE. NOW. HERE. NOW.',
        'LISTEN WITH YOUR EYES.', 'SIGNAL ....... FEEDBACK', 'FOUND, NOT MADE.',
    ],
    # The rubber stamp that lands on the snare.
    'STAMPS': ['DO NOT TOUCH', 'PLATE 07', 'LOOP', 'UNKNOWN USE', 'EXHIBIT 12', 'REAL TIME', 'FOUND OBJECT'],
    # Title block: the owner line and the sheet line (one %-field: the song section).
    'TITLE': {'org': 'CATALOGUE OF OBJECTS OF UNKNOWN USE', 'sheet': 'PLATE 07    SHEET %02d OF 43'},
    # Lettering of the three parts takes: the leader to the landing part, the counter and the heading.
    'PARTS_LABELS': {'leader': 'PART %02d  ', 'count': 'ONSET %05d', 'head': 'ELEVATION.  PLATE 12 / CAT-0047'},
    # What the three parts takes say in Describe mode (the other takes' Describe words are in logic.py).
    'PARTS_WORDS': {
        'take_iso_keys': {
            'typed': ['THE MODEL IS CUT INTO PARTS.', 'PARTS FLY OUT ON THE BAR LINE.',
                      'THE BAR SETS THE PARTS BACK IN.', 'A SHADER TRACES EVERY LINE HERE.'],
            'leader': 'PART %02d OF %d LANDING'},
        'take_macro_keys': {
            'lines': ['EXPLODED VIEW: %d PARTS, EACH A SEPARATE SHAPE.',
                      'A SHADER TRACES THE EDGES. THE BAR SETS THE PARTS BACK IN.']},
        'take_plan_typed': {
            'typed': ['PARTS SET BACK OVER TWO BARS.', 'EVERY PART IS ITS OWN SHAPE.', 'HI-HATS POP PARTS OUT OF PLACE.'],
            'head': 'FRONT VIEW.  %d PARTS SCATTER, THEN LAND FROM THE GROUND UP'},
    },
    # Drafting labels every pack is likely to keep. %-fields are live values.
    'LABELS': {
        'dwg': 'DWG ', 'rev': 'REV %03d', 'beat': 'BEAT %d',
        'views': ['FRONT ELEVATION', 'PLAN', 'SIDE ELEVATION'], 'iso': 'EXPLODED ISOMETRIC  %d SECTIONS',
        'deg': '%03d DEG', 'section': 'SECTION A-A', 'cut_at': 'CUT AT %05.1f MM   %s', 'cut_face': 'CUT FACE  %02d%%',
        'strip': '%s   %s   %d SECTIONS AT %.1f', 'bar': 'BAR %03d',
        'bass': 'BASS DEFLECTION, MM', 'list_row': '%s  %-22s QTY %02d', 'slab': 'S-%02d',
        'plane': 'PLANE %03d', 'planes': 'PLANES   %s', 'station': 'STATION %02d OF 12',
    },
}

SCRIPT_CB = '''# Script OP callbacks: all the work is in the 'logic' DAT (logic.py).
def onCook(scriptOp):
    op('logic').module.%s
    return
'''


def _logic():
    g = {'absTime': td.absTime, 'project': td.project}
    exec(open(HERE + '/logic.py', encoding='utf-8').read(), g)
    return g


def _file_dat(scene, name, fname, x, y):
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here('%s')" % fname
    d.par.syncfile = True
    d.text = open(HERE + '/' + fname, encoding='utf-8').read()
    d.nodeX, d.nodeY = x, y
    return d


def _script(scene, optype, name, call, x, y):
    o = scene.create(optype, name)
    for d in list(o.docked):
        d.destroy()
    cb = scene.create(td.textDAT, name + '_cb')
    cb.text = SCRIPT_CB % call
    cb.nodeX, cb.nodeY = x, y - 90
    o.par.callbacks = cb.path
    o.nodeX, o.nodeY = x, y
    return o


def _vecs(o, rows):
    """rows: [(name, (x, y, z, w))]; each component a number or an expression string."""
    o.seq.vec.numBlocks = len(rows)
    for i, (name, vals) in enumerate(rows):
        getattr(o.par, 'vec%dname' % i).val = name
        for c, v in zip('xyzw', vals):
            p = getattr(o.par, 'vec%dvalue%s' % (i, c))
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _arrays(o, rows):
    o.seq.array.numBlocks = len(rows)
    for i, (name, chop) in enumerate(rows):
        getattr(o.par, 'array%dname' % i).val = name
        getattr(o.par, 'array%dtype' % i).val = 'vec4'
        getattr(o.par, 'array%dchop' % i).val = chop


def C(name):
    return "op('ctl')['" + name + "']"


def _obj_box(path):
    """Bounds and triangle count of an OBJ file, read as text (a POP's computeBounds is not
    ready in the call that creates it)."""
    lo, hi, tris = [1e9] * 3, [-1e9] * 3, 0
    for line in open(path, encoding='utf-8', errors='replace'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            for i in range(3):
                x = float(p[1 + i])
                lo[i], hi[i] = min(lo[i], x), max(hi[i], x)
        elif p[0] == 'f':
            tris += len(p) - 3
    return lo, hi, tris


def build():
    LIB = {'op': op}
    exec(open(REPO + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 1000, -1100)
    # The installed module, not LIB: only it sees the scene's Assets parameter.
    pdat = scene.op('local/modules/paths')
    if 'def model_file' not in pdat.text:      # a Text DAT loads its file a frame after it is set
        pdat.text = open(REPO + '/experiments/sw_hub/paths_module.py', encoding='utf-8').read()
    paths = pdat.module
    W = LIB['scene_words'](scene, DEFAULTS)
    L = _logic()
    words = scene.create(td.textDAT, 'words')      # read by logic.py (setup); written here and nowhere else
    words.text = json.dumps(W, indent=1)
    words.nodeX, words.nodeY = -1000, 600
    H = "op('hub')"

    # ---------------- per-frame decisions (logic.py) ----------------
    _file_dat(scene, 'logic', 'logic.py', -800, 600)
    ctl = _script(scene, td.scriptCHOP, 'ctl', 'cook_ctl(scriptOp)', -600, 600)
    views = _script(scene, td.scriptCHOP, 'views', 'cook_views(scriptOp)', -400, 600)
    lines = _script(scene, td.scriptCHOP, 'lines', 'cook_lines(scriptOp)', -200, 600)
    sel = {}
    for i, (name, src, chans) in enumerate([('view_a', views, 'a*'), ('view_b', views, 'b*'),
                                             ('line_a', lines, 'x0 y0 x1 y1'), ('line_b', lines, 'k c w u')]):
        s = scene.create(td.selectCHOP, name)
        s.par.chop = src.path
        s.par.channames = chans
        s.nodeX, s.nodeY = -400 + i * 150, 420
        sel[name] = s

    # ---------------- Input: another scene's picture, or nothing ----------------
    # see: NOTES.md "Input". Blank, missing or our own TOPs select 'inblank', and 'pic' in ctl is 0.
    blank = scene.create(td.constantTOP, 'inblank')
    blank.par.colorr = blank.par.colorg = blank.par.colorb = blank.par.alpha = 0
    blank.par.outputresolution = 'custom'
    blank.par.resolutionw, blank.par.resolutionh = 16, 16
    blank.nodeX, blank.nodeY = -1000, 250
    insel = scene.create(td.selectTOP, 'insel')
    insel.par.top.expr = "op('logic').module.input_path(parent()) or 'inblank'"
    insel.nodeX, insel.nodeY = -850, 250

    # ---------------- the parts ----------------
    vert = _file_dat(scene, 'part_vertex', 'shaders/part_vertex.glsl', -800, 100)
    pix = _file_dat(scene, 'part_pixel', 'shaders/part_pixel.glsl', -800, 0)
    mat = scene.create(td.glslMAT, 'part_mat')
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = vert.path
    mat.par.pdat = pix.path
    mat.par.cullface = 'neither'
    _arrays(mat, [('uViewA', sel['view_a'].path), ('uViewB', sel['view_b'].path)])
    _vecs(mat, [
        ('uObj', (C('mode'), C('slabs'), C('axis'), C('nviews'))),
        ('uExt', (C('ext_lo'), C('ext_hi'), C('gap'), C('fan'))),
        ('uMisc', (H + "['evolve']", "min(1.0, float(" + H + "['hit_high']))", "op('shot')['seed']", H + "['beat_pos']")),
        ('uKeys', (C('chaos'), C('spread'), C('lift'), C('rowlift'))),
        ('uKeys2', (C('casesink'), 0, 0, 0)),
        ('uParts', (C('p_count'), C('p_ylo'), C('p_yspan'), 0)),
        ('uPartsUV', (C('p_sx'), C('p_s2'), C('p_plane'), 0)),
        ('uPicFit', (C('pic'), C('picw'), C('pich'), C('capin'))),
    ])
    mat.seq.sampler.numBlocks = 1
    mat.par.sampler0name = 'sPic'
    mat.par.sampler0top = insel.path
    mat.par.sampler0extendu = mat.par.sampler0extendv = 'hold'
    mat.par.sampler0filter = 'linear'
    mat.nodeX, mat.nodeY = -600, 50

    standins = []
    for i, m in enumerate(W['MODELS']):
        geo = scene.create(td.geometryCOMP, 'part%d' % i)
        for ch in geo.children:
            ch.destroy()
        mesh = geo.create(td.fileinPOP, 'mesh')
        mesh.render = True
        mesh.display = True
        if m[0] == W['PARTS']['name']:
            mesh.par.file.expr = "mod.paths.scene_file(%r)" % W['PARTS']['obj']
        else:
            mesh.par.file.expr = "mod.paths.model_file(%r)" % m[0]
            if not paths.have('models/%s/model.obj' % m[0]):
                # No model library: mod.paths gives TouchDesigner's teapot. The shaders and logic.py
                # expect a mesh centred on the origin with its longest side 1 unit, so fit it here
                # and tell logic.py its real size and triangle count (table 'model_info').
                lo, hi, tris = _obj_box(paths.model_file(m[0]))
                k = 1.0 / max(max(hi[a] - lo[a] for a in range(3)), 1e-6)
                fit = geo.create(td.transformPOP, 'fit')
                mesh.outputConnectors[0].connect(fit)
                fit.par.scale = k
                fit.par.tx, fit.par.ty, fit.par.tz = [-(lo[a] + hi[a]) / 2 * k for a in range(3)]
                mesh.render = mesh.display = False
                fit.render = fit.display = True
                fit.nodeX = 150
                standins.append([i] + [round((hi[a] - lo[a]) * k, 4) for a in range(3)] + [tris])
        geo.par.material = mat.path
        geo.par.instancing = True
        geo.par.instancecountmode = 'manual'
        geo.par.numinstances.expr = "int(" + C('ninst') + ")"
        geo.par.render.expr = "int(" + C('model') + ") == " + str(i)
        geo.nodeX, geo.nodeY = -400 + (i % 6) * 130, 150 - (i // 6) * 110
        geo.comment = m[0]
        mesh.cook(force=True)     # a hidden part must not load its mesh on the cut that first shows it

    # With the file an expression, the forced cook above is not enough: each mesh loaded again
    # (25 to 50 ms) on the cut that first showed its part. A second forced cook a moment after the
    # build stops that; four frames after was too soon. Measured 2026-11-11, NOTES.md log 20.
    td.run("[g.op('mesh').cook(force=True) for g in args[0].findChildren(name='part*', depth=1)]",
           scene, delayMilliSeconds=1500)

    info = scene.create(td.tableDAT, 'model_info')      # read by logic.py; rows only for stand-ins
    info.clear()
    info.appendRow(['index', 'sx', 'sy', 'sz', 'tris'])
    for row in standins:
        info.appendRow(row)
    info.nodeX, info.nodeY = -800, 480

    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.projection.expr = "'perspective' if " + C('persp') + " > 0.5 else 'ortho'"
    cam.par.orthowidth = 1280.0 / L['PPU']
    cam.par.tz.expr = C('camz')
    cam.par.fov.expr = C('fov')
    cam.par.near = 0.05
    cam.par.far = 40
    cam.nodeX, cam.nodeY = -600, -150

    render = scene.create(td.renderTOP, 'gbuffer')
    render.par.camera = cam.path
    render.par.geometry = 'part*'
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba32float'
    render.par.antialias = 'aa4'
    render.par.numcolorbufs = 3        # third: the Input picture as it sits on the parts
    render.par.bgcolorr = render.par.bgcolorg = render.par.bgcolorb = render.par.bgcolora = 0
    render.nodeX, render.nodeY = 0, 100
    data = scene.create(td.renderselectTOP, 'gdata')
    data.par.top = render.path
    data.par.colorbufindex = 1
    data.nodeX, data.nodeY = 0, -50
    gpic = scene.create(td.renderselectTOP, 'gpic')
    gpic.par.top = render.path
    gpic.par.colorbufindex = 2
    gpic.nodeX, gpic.nodeY = 150, -50

    # ---------------- lettering ----------------
    texts = []
    for i, (name, cls, font, size, colour) in enumerate([
            ('txt_s', 's', 'barlow', 17, (1, 1, 1)), ('txt_a', 'a', 'barlow', 17, (1, 0, 0)),
            ('txt_l', 'l', None, None, (1, 1, 1)), ('txt_x', 'x', None, None, (1, 0, 0))]):
        tab = _script(scene, td.scriptDAT, 'lab_' + cls, "cook_labels(scriptOp, '" + cls + "')", -400 + i * 170, -350)
        t = scene.create(td.textTOP, name)
        t.par.specdat = tab.path
        if font:
            t.par.fontfile.expr = "mod.paths.font('%s')" % font
            # TouchDesigner's default face is far wider than Barlow Condensed: set it smaller so the
            # title block and labels still fit their boxes when the font is not there
            t.par.fontsizex.expr = "%d if mod.paths.font('%s') else 13" % (size, font)
        else:
            t.par.fontfile.expr = "mod.paths.font(('chicago', 'archivo', 'barlow')[int(" + C('bigfont') + ")])"
            t.par.fontsizex.expr = C('big') if cls == 'l' else C('huge')
        t.par.fontsizexunit = 'pixels'
        t.par.fontautosize = 'nofit'
        t.par.alignx = 'left'
        t.par.aligny = 'bottom'
        t.par.outputresolution = 'custom'
        t.par.resolutionw, t.par.resolutionh = 1280, 720
        t.par.fontcolorr, t.par.fontcolorg, t.par.fontcolorb = colour
        t.par.bgalpha = 0
        t.nodeX, t.nodeY = -400 + i * 170, -560
        texts.append(t)
    letter = scene.create(td.compositeTOP, 'lettering')
    letter.par.operand = 'over'
    for t in texts:
        t.outputConnectors[0].connect(letter)
    letter.nodeX, letter.nodeY = 300, -560

    # ---------------- the drawing ----------------
    draw = scene.create(td.glslTOP, 'draw')
    for d in list(draw.docked):
        if d.name.endswith('_pixel') or d.name.endswith('_compute'):
            d.destroy()
    draw.par.pixeldat = _file_dat(scene, 'draw_frag', 'shaders/draw.frag', 300, -150).path
    draw.par.outputresolution = 'custom'
    draw.par.resolutionw, draw.par.resolutionh = 1280, 720
    draw.par.format = 'rgba8fixed'
    render.outputConnectors[0].connect(draw.inputConnectors[0])
    data.outputConnectors[0].connect(draw.inputConnectors[1])
    letter.outputConnectors[0].connect(draw.inputConnectors[2])
    draw.par.tops = gpic.path + ' ' + insel.path   # a GLSL TOP has three connectors; these are sTD2DInputs[3] and [4]
    _arrays(draw, [('uL0', sel['line_a'].path), ('uL1', sel['line_b'].path)])
    _vecs(draw, [
        ('uPaper', (C('paper_r'), C('paper_g'), C('paper_b'), C('paper_style'))),
        ('uInk', (C('ink_r'), C('ink_g'), C('ink_b'), C('ow'))),
        ('uAccent', (C('acc_r'), C('acc_g'), C('acc_b'), C('cw'))),
        ('uStyle', (C('hatch'), C('cutfill'), C('shade'), C('vig'))),
        ('uAudio', (H + "['pulse']", "min(1.0, float(" + H + "['hit_mid']))", "op('shot')['age']", H + "['evolve']")),
        ('uAudio2', ("min(1.0, float(" + H + "['hit_low']))", H + "['beat']", C('reveal'), C('dthr'))),
        ('uStyle2', (C('contours'), C('fill'), C('mode'), C('scan'))),
        ('uPic', (C('pic'), C('knock'), C('sheet'), 0)),
    ])
    draw.nodeX, draw.nodeY = 600, 0
    # halo for the dark sheets: a quarter-size blur added back (amount 0 on paper)
    small = scene.create(td.resolutionTOP, 'glow_small')
    small.par.outputresolution = 'custom'
    small.par.resolutionw, small.par.resolutionh = 320, 180
    draw.outputConnectors[0].connect(small)
    blur = scene.create(td.blurTOP, 'glow_blur')
    blur.par.size = 10
    small.outputConnectors[0].connect(blur)
    small.nodeX, small.nodeY = 780, -150
    blur.nodeX, blur.nodeY = 930, -150
    final = scene.create(td.glslTOP, 'final')
    for d in list(final.docked):
        if d.name.endswith('_pixel') or d.name.endswith('_compute'):
            d.destroy()
    final.par.pixeldat = _file_dat(scene, 'final_frag', 'shaders/final.frag', 930, -300).path
    final.par.outputresolution = 'custom'
    final.par.resolutionw, final.par.resolutionh = 1280, 720
    final.par.format = 'rgba8fixed'
    draw.outputConnectors[0].connect(final.inputConnectors[0])
    blur.outputConnectors[0].connect(final.inputConnectors[1])
    _vecs(final, [('uGlow', (C('glow'), H + "['pulse']", "min(1.0, float(" + H + "['hit_mid']))", 0))])
    final.nodeX, final.nodeY = 930, 0
    final.outputConnectors[0].connect(scene.op('out1'))
    # compile messages, for whoever debugs this next
    for name, target, x, y in (('part_info', mat, -600, -50), ('draw_info', draw, 600, -150)):
        old = scene.op(name)
        if old:
            old.destroy()
        info = scene.create(td.infoDAT, name)
        info.par.op = target.path
        info.nodeX, info.nodeY = x, y
    return scene.path
