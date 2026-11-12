# sc_droste_crt: the monitor that shows itself (real feedback recursion on a CRT's glass).
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md). Idempotent.
# see: experiments/sc_droste_crt/NOTES.md (2026-11-10)
import math
import td

SLUG = 'sc_droste_crt'
# Files are found through the scaffold's paths module (mod.paths, experiments/sw_hub/paths_module.py):
# every parameter that names a file is an expression, and the assets folder may be empty.
CHICAGO = "mod.paths.font('chicago')"      # '' with no assets: the Text TOPs then use FALLBACK_FONT
FALLBACK_FONT = 'Arial'             # drawn bold; narrower than Chicago, so every line that fits in Chicago fits
H = "op('hub')"
TK = "op('tk')"
SH = "op('shot')"

# ---- world layout (1 unit is about half a metre; floor at y = 0) -------------------
DESK_S = 3.0
DESK_TOP = 0.242 * DESK_S * 2            # 1.45
# The CRT is stretched in x so the recess in its bezel is exactly 16:9: the glass can
# then show the whole frame, and a camera on the glass's axis sees a pure scaled copy.
CRT_SY, CRT_SZ = 1.5, 1.2
REC_X0, REC_X1, REC_Y0, REC_Y1 = -0.245, 0.235, -0.065, 0.285    # recess in model space (measured)
CRT_SX = CRT_SY * ((REC_Y1 - REC_Y0) * 16.0 / 9.0) / (REC_X1 - REC_X0)
CRT_T = (-0.35, DESK_TOP + 0.372 * CRT_SY, -0.12)
# glass surface fitted to the mesh (model space): z = Z0 + ZB*(y-YC) + ZC*(y-YC)^2 + ZD*(x-XC)^2
XC, YC = 0.5 * (REC_X0 + REC_X1), 0.5 * (REC_Y0 + REC_Y1)
Z0, ZB, ZC, ZD = 0.432, -0.108, -0.27, -0.25   # the mesh's own bulge is twice this; flatter keeps the copy near-exact
SCR_W = (REC_X1 - REC_X0) * CRT_SX       # world width of the picture
SCR_C = (CRT_T[0] + XC * CRT_SX, CRT_T[1] + YC * CRT_SY, CRT_T[2] + (Z0 - 0.008) * CRT_SZ)
TAU = math.atan2(-ZB / CRT_SY, 1.0 / CRT_SZ)     # the glass leans back by this much
FOV = 40.0
D1 = (SCR_W / 2) / math.tan(math.radians(FOV / 2))   # camera distance at which the glass fills the frame

# ---- content a pack may replace (see NOTES.md, "Words and models") ---------------------------
# Read in build() through LIB['scene_words']: a pack's scenes/sc_droste_crt/words.json replaces any
# of these names. Everything the scene says, and every model it stands on the desk, is here.
#   TERMS    screens typed on the glass in take 5, | = new line (46 px: keep lines under 32 characters)
#   PHRASES  one per beat in take 8, | = new line (150 px: keep lines under 11 characters)
#   MONITOR, DESK  model '' = the one built of boxes below; colour = its flat colour
#   PROPS    the five things on the desk. role is what the music does to it (fixed in build()):
#            kick hops on kicks, glow lights up on kicks and sways, rattle shakes on hi-hats,
#            snare jumps and tips on snares, hat hops on hi-hats and swings with the beat.
#            at = (x, height of its centre above the desk top, z); every library model is centred
#            with its longest side 1, so that height is half its height times scale.
#            standin = (half height of the model, longest side of the teapot that replaces it
#            with no model library), colour = that teapot's flat colour.
DEFAULTS = {
    'TERMS': [
        'PROGRAM STARTED...|REAL TIME PICTURE TERMINAL 01|SIGNAL .......... IN|PICTURE ......... OUT|FEEDBACK ........ OPEN',
        'THIS SCREEN: NOTHING STORED.|A PICTURE IS FORMING.|IT IS MADE NOW.|SOUND IN. PICTURE OUT.',
        'THE TABLE HOLDS FIVE OBJECTS.|  1  FOUND|  2  NOT MADE|OBJECTS OF UNKNOWN USE.',
        'NOTHING HERE IS PRERENDERED.|PLEASE WATCH.|EVERY FRAME IS MADE NOW.|THE KICK MOVES THE CAMERA.',
        'THE LOOP IS RUNNING|SIXTY FRAMES|A SECOND. LISTEN|WITH YOUR EYES.',
        'PLATE 07|OBJECT OF UNKNOWN USE|HANDLE WITH BOTH HANDS|PAST. PRESENT. LATER.',
    ],
    'PHRASES': ['REAL|TIME', 'HERE.', 'NOW.', 'DO NOT|TOUCH', 'PLATE|07', 'NO|PLAYBACK', 'SOUND IN|PICTURE|OUT',
                'EXHIBIT|12-B', 'LOUD IS|BRIGHT', 'LOOP.|LOOP.', 'FEEDBACK|OPEN', 'FOUND,|NOT MADE', 'SIGNAL|IN.',
                'FRAME|0047', 'OUT OF|NOISE', 'MADE OF|LIGHT'],
    'MONITOR': {'model': '', 'colour': [0.78, 0.75, 0.65]},
    'DESK': {'model': '', 'colour': [0.62, 0.44, 0.24]},
    'PROPS': [
        {'role': 'kick', 'model': 'rubber_duck', 'scale': 0.34, 'at': [-0.38, 0.39 * 0.34, 0.585], 'ry': 25,
         'standin': [0.39, 1.0], 'colour': [0.93, 0.76, 0.20]},
        {'role': 'glow', 'model': 'astrolabe', 'scale': 1.0, 'at': [1.12, 0.5 * 1.0, -0.30], 'ry': -35,
         'standin': [0.5, 0.80], 'colour': [0.72, 0.56, 0.24]},
        {'role': 'rattle', 'model': 'gramophone', 'scale': 0.55, 'at': [0.80, 0.5 * 0.55, 0.44], 'ry': -22,
         'standin': [0.5, 0.80], 'colour': [0.50, 0.22, 0.16]},
        {'role': 'snare', 'model': 'amphora', 'scale': 0.48, 'at': [-1.12, 0.5 * 0.48, 0.36], 'ry': 40,
         'standin': [0.5, 0.70], 'colour': [0.72, 0.36, 0.22]},
        {'role': 'hat', 'model': 'lander', 'scale': 0.36, 'at': [0.26, 0.5 * 0.36, 0.60], 'ry': 62,
         'standin': [0.5, 0.90], 'colour': [0.80, 0.66, 0.22]},
    ],
}
# The monitor and the desk are never teapots: the loop needs a screen in a bezel, so they are boxes.
# boxes in the library model's own space: (x0, x1, y0, y1, z0, z1)
CRT_BOXES = [
    (-0.326, 0.326, -0.12, 0.372, -0.30, 0.39),     # case, its front face just behind the glass
    (-0.23, 0.23, -0.06, 0.31, -0.50, -0.30),       # tube housing at the back
    (-0.30, 0.30, -0.372, -0.135, -0.40, 0.52),     # base unit, a step proud of the bezel
    (-0.326, 0.326, 0.285, 0.372, 0.39, 0.47),      # bezel: top, bottom, left, right of the recess
    (-0.326, 0.326, -0.12, -0.065, 0.39, 0.47),
    (-0.326, -0.245, -0.065, 0.285, 0.39, 0.47),
    (0.235, 0.326, -0.065, 0.285, 0.39, 0.47),
    (0.03, 0.22, -0.262, -0.238, 0.52, 0.532),      # drive slot
]
DESK_BOXES = [
    (-0.5, 0.5, 0.212, 0.242, -0.252, 0.252),       # top
    (-0.48, -0.20, -0.242, 0.212, -0.235, 0.235),   # pedestals
    (0.20, 0.48, -0.242, 0.212, -0.235, 0.235),
    (-0.20, 0.20, -0.10, 0.212, -0.235, -0.215),    # modesty panel
]

# ---- takes: genuinely different pictures from the same machine ------------------------
DEFAULT = dict(
    az=24, el=7, dist=4.3, tgx=0.55, tgy=-0.22, orb=4, seedaz=14,     # master camera, about the glass
    view=0,            # 0 master, 1 second camera (dolly or free), 2 Escher twist of the master
    omode=0, oaz=0, oel=0, odist=1, otgx=0, otgy=0, bars=2,
    delay=3,           # extra frames of age per level (0 = one frame per level)
    hue=38, gain=1.05, rot=0, zoom=1, inv=0, mono=0, flip=0, scan=0.45, text=0, lsat=1.15,
    tr=0.55, tg=1.0, tb=0.65,                    # phosphor tint
    room=1, wall=0,                              # desk set / wall of monitors
    lamp=6.0, lr=1.0, lg=0.72, lb=0.40,          # desk lamp
    fluor=3.4, fr=0.90, fg=0.95, fb=0.80,       # overhead tube
    glow=2.5, rimd=1.6, rr=0.35, rg=0.55, rb=0.9,
    bit=0, psat=1.08, pcon=1.12, vign=1.0, grain=0.035, bloom=0.5,
    sr=0.02, sg=0.05, sb=0.09,                   # shadow tint
    twist=1, edge=1, tscale=1,
    wr=0.27, wg=0.34, wb=0.30,                   # back wall colour
    kick=0.20,         # light added to the glass on each kick (walks down the levels)
    hk=0,              # degrees of extra hue step while a kick is sounding
    punch=0.03,        # master camera pushes in by this fraction on a kick (must be 0 for the on-axis maths of takes 1, 2)
    secflip=1,         # 1: the hue step changes sign with the section's parity
    mz=1.1,          # macro view: zoom into the glass
    # Input (the COMP's Input parameter names a TOP): where the given picture enters this take.
    # 1 = backdrop: it replaces the back wall behind the set, so the camera films it and the loop nests it.
    # 2 = on the glass: drawn on the outermost screen where the text is drawn, so it echoes down the levels.
    # 3 = both.
    inp=1, inmix=0.55, inscale=1.0, ingain=1.35,
    inkey=0,           # on the glass: 0 = flat mix, 1 = the picture's dark parts let the tunnel through
    inlit=0,           # on the glass: 1 = lighten (the brighter of picture and tunnel wins) instead of a mix
)
# Describe mode (the COMP's Describe toggle): each take's `describe` is what it shows instead of the scene's own text.
#   takes with no text of their own: [title, line, line] drawn as a caption strip under the picture;
#   'terminal': screens typed on the glass (| = new line); 'words out': one entry per beat, in order.
# Every statement is about this scene as built: keep them true when a number above changes.
TAKES = [
    dict(name='desk at night', dist=3.9, fluor=1.5, fr=0.6, fg=0.75, fb=1.0, glow=4,
         describe=['VIDEO FEEDBACK ON A 3D MONITOR',
                   "The monitor's screen shows the previous frame of this same camera.",
                   'Each copy inside is 4 frames older and its colours are turned a step.']),
    dict(name='droste dolly', az=0, el=0, dist=D1 / 0.46, tgx=0, tgy=0, orb=0, seedaz=0, view=1,
         bars=2, delay=0, hue=58, gain=1.0, scan=0.10, edge=0, fluor=4.4, fr=1.0, fg=0.93, fb=0.78, lamp=6.5,
         wr=0.60, wg=0.09, wb=0.06, punch=0, secflip=0, kick=0.10, psat=1.2,
         describe=['DROSTE ZOOM FROM REAL FEEDBACK',
                   'The screen shows the last frame of a wide camera facing it.',
                   'A second camera flies into it every 2 bars and comes out where it began.']),
    dict(name='escher spiral', az=0, el=0, dist=D1 / 0.5, tgx=0, tgy=0, orb=0, seedaz=0, view=2,
         bars=4, delay=1, hue=44, gain=1.0, scan=0.15, edge=0, twist=2, fluor=2.6, fr=1.0, fg=0.42, fb=0.25,
         lamp=7, glow=4, rimd=3, rr=0.2, rg=0.5, rb=1.0, punch=0, secflip=0, kick=0.12,
         describe=['ESCHER SPIRAL OF A FEEDBACK TUNNEL',
                   'A shader bends the monitor-in-monitor picture round its centre,',
                   'so the nested screens join into one spiral. It zooms in a level every 4 bars.']),
    dict(name='one-bit negative', az=-20, el=4, dist=2.7, tgx=-0.2, tgy=-0.05, inv=1, hue=0, gain=1.0,
         lsat=0, bit=1, delay=5, fluor=3.0, lamp=7.0, lr=1, lg=1, lb=1, scan=0.0, bloom=0.0, grain=0, vign=0.3,
         wr=0.05, wg=0.05, wb=0.05, punch=0.06, kick=0.3, inp=2, inmix=0.6,
         describe=['ONE-BIT FEEDBACK, NEGATIVE AT EVERY LEVEL',
                   "The screen shows this camera's previous frame as a negative,",
                   'so each copy inverts the one outside it. Every kick drum swaps black and white.']),
    dict(name='wall of monitors', room=0, wall=1, az=27, el=-5, dist=6.2, tgx=0.5, tgy=0.0, orb=5,
         delay=4, hue=24, lamp=0, fluor=3.0, inp=3, inmix=0.5, fr=1.0, fg=0.28, fb=0.2, glow=5, rimd=4, rr=0.2, rg=0.4, rb=1.0,
         hk=45, punch=0.07, kick=0.35,
         describe=['ONE FEEDBACK LOOP ON 15 SCREENS',
                   'Every monitor shows the previous frame of this same camera,',
                   'so the wall is filled with pictures of itself. Kick drums shift the colours.']),
    dict(name='terminal', az=-17, el=3, dist=2.25, tgx=-0.18, tgy=-0.05, orb=2, seedaz=8, mono=1, text=1,
         hue=0, gain=0.86, delay=7, scan=0.75, lamp=0.5, fluor=0.5, glow=5, rimd=0.5, inp=2, inmix=0.75, inlit=1,
         sr=0.0, sg=0.08, sb=0.03,
         describe=["THIS SCREEN SHOWS ITSELF.|THE CAMERA'S LAST FRAME|IS THE PICTURE ON THE GLASS.|EACH COPY INSIDE IS|8 FRAMES OLDER.",
                   'THE TUNNEL IS NOT DRAWN.|IT IS ONE 3D RENDER,|FED BACK TO ITS OWN SCREEN|ONCE EVERY FRAME.',
                   'THIS TEXT IS TYPED ON|THE OUTER SCREEN ONLY.|THE COPIES INSIDE ARE|ITS ECHOES, 8 FRAMES APART.',
                   'ONE SHADER STEP PER COPY:|GREEN TINT, SCANLINES,|A LITTLE LESS LIGHT.|EACH COPY GETS IT AGAIN.',
                   'KICK DRUMS LIGHT THE GLASS.|THE CAMERA SEES THE FLASH.|ONE STEP LATER THE NEXT|COPY SHOWS IT, AND SO ON.',
                   'BUILT IN TOUCHDESIGNER:|RENDER TOP, FEEDBACK TOP,|CACHE TOP, ONE GLSL SHADER,|A MATERIAL ON THE GLASS.']),
    dict(name='spiral tunnel', az=0, el=0, dist=D1 / 0.72, tgx=0, tgy=0, orb=1.5, seedaz=4, rot=17, zoom=1.03,
         delay=2, hue=31, gain=1.02, scan=0.2, edge=0.5, lamp=5, lr=1.0, lg=0.35, lb=0.6, fluor=2.2,
         fr=0.5, fg=0.6, fb=1.0, inp=2, inmix=0.8, inlit=1,
         describe=['FEEDBACK WITH A TURN',
                   "The screen shows this camera's previous frame, turned up to 17 degrees,",
                   'so the nested monitors wind into a tunnel. Bass notes add more turn.']),
    # lens against the glass: the view is the screen texture itself, broken into RGB phosphor slots
    dict(name='phosphor macro', view=3, az=20, el=6, dist=3.3, tgx=0.35, tgy=-0.15, scan=0.0, edge=0, delay=2,
         hue=47, lamp=9, glow=5, fluor=3.0, fr=0.6, fg=0.75, fb=1.0, bloom=0.7, gain=1.12, psat=1.3, pcon=1.05, vign=0.8,
         grain=0.02, kick=0.25, inp=2, inmix=0.6,
         describe=['PHOSPHOR MACRO OF THE FEEDBACK SCREEN',
                   "No camera here: this is the picture on the monitor's glass, enlarged,",
                   'and a shader splits it into red, green and blue phosphor slots.']),
    # camera closer than the fill distance: every level is bigger than the last, so what is
    # drawn in the middle of the glass flies outward. No room, only the loop and the words.
    dict(name='words out', az=0, el=0, dist=D1 / 1.22, tgx=0, tgy=0, orb=0, seedaz=0, room=0, text=2,
         tscale=0.27, delay=3, hue=31, gain=0.96, rot=5, scan=0, edge=0, lsat=1.0, tr=0.95, tg=0.62, tb=0.10,
         lamp=0, fluor=0, glow=0, rimd=0, bloom=0.9, vign=0.6, kick=0.05, punch=0, inp=2, inmix=1.0, inscale=0.34,
         describe=['VIDEO|FEEDBACK', 'A SCREEN', 'SHOWING', 'ITS OWN|LAST|FRAME', 'CAMERA|TOO CLOSE', 'SO EACH|COPY IS',
                   'BIGGER', 'NOT|SMALLER', 'WORDS|FLY OUT', 'ONE WORD|PER BEAT', 'DRAWN|SMALL', 'IN THE|CENTRE',
                   'HUE TURNS|EACH STEP', 'OLDER IS|BIGGER', 'NO ROOM', 'ONLY|THE LOOP']),
]
NT = len(TAKES)
# What this scene does to a picture it is given through Input (mirrored into preset.json by sync_preset.py)
AS_PROCESSOR = ("Puts the picture inside a real video feedback loop on an old monitor: it becomes the backdrop "
                "behind the desk or the image on the monitor's screen, and the loop repeats it as smaller, older, "
                "colour-shifted copies nested inside each other (spiralled, turned, 1-bit, in green phosphor, or "
                "flying outward, depending on the take).")

def tkexpr(key):
    vals = [t.get(key, DEFAULT[key]) for t in TAKES]
    # reads the parameter, not the shot CHOP: that one carries `age` and would recook this every frame
    return '(%s)[int(parent().par.Take) %% %d]' % (','.join('%g' % v for v in vals) + ',', NT)


# One Execute DAT replaces the scaffold's cook driver: same gate, plus a pulse to the
# feedback when the scene has not been cooking (a cut to this scene), so stale frames
# from the last visit do not come down the tunnel.
DRIVER = '''_last = [0, -1]

def onFrameStart(frame):
    hub = op('/project1/sw_hub')
    me_on = parent().par.Preview.eval()
    if hub is not None:
        me_on = me_on or hub.par.Solo.eval() or hub.par.Scene.eval() == parent().name
    if me_on:
        take = int(parent().par.Take)
        # a cut to this scene, or a new take: the last picture must not come down the tunnel
        if absTime.frame - _last[0] > 30 or take != _last[1]:
            op('fb').par.resetpulse.pulse()
            if hasattr(op('cache').par, 'resetpulse'):
                op('cache').par.resetpulse.pulse()
        _last[0] = absTime.frame
        _last[1] = take
        op('hub').cook(force=True)
        op('out1').cook(force=True)
    return
'''

_pos = [0, 0]


def _place(o, col=None):
    if col is not None:
        _pos[0], _pos[1] = col, 0
    o.nodeX, o.nodeY = -200 + _pos[0] * 170, 300 - _pos[1] * 120
    _pos[1] += 1
    return o


def _glsl(scene, name, frag, w, h, fmt, uniforms):
    dat = _place(scene.create(td.textDAT, name + '_frag'))
    dat.par.file.expr = "mod.paths.here('shaders/%s')" % frag
    dat.par.syncfile = True
    top = _place(scene.create(td.glslTOP, name))
    for docked in (name + '_pixel', name + '_compute'):
        if scene.op(docked):
            scene.op(docked).destroy()
    top.par.pixeldat = dat.name
    top.par.outputresolution = 'custom'
    top.par.resolutionw, top.par.resolutionh = w, h
    top.par.format = fmt
    top.seq.vec.numBlocks = len(uniforms)
    for i, (uname, exprs) in enumerate(uniforms):
        getattr(top.par, 'vec%dname' % i).val = uname
        for comp, e in zip('xyzw', exprs):
            getattr(top.par, 'vec%dvalue%s' % (i, comp)).expr = e
    return top


def _chop(scene, name, chans):
    c = _place(scene.create(td.constantCHOP, name))
    c.seq.const.numBlocks = len(chans)
    for i, (n, e) in enumerate(chans):
        getattr(c.par, 'const%dname' % i).val = n
        p = getattr(c.par, 'const%dvalue' % i)
        if isinstance(e, str):
            p.expr = e
        else:
            p.val = e
    return c


def _obj_bounds(path):
    """(min, max) of an OBJ file's vertices, read as text (the bundled teapot is 1660 points)."""
    lo, hi = [1e9] * 3, [-1e9] * 3
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('v '):
                for i, v in enumerate(line.split()[1:4]):
                    lo[i], hi[i] = min(lo[i], float(v)), max(hi[i], float(v))
    return lo, hi


def _boxes(geo, name, boxes):
    """A stand-in shape made of Box POPs merged into one POP called `name`."""
    merge = geo.create(td.mergePOP, name)
    for i, (x0, x1, y0, y1, z0, z1) in enumerate(boxes):
        b = geo.create(td.boxPOP, '%s_b%d' % (name, i))
        b.par.uniquepoints = True      # flat faces
        b.par.sizex, b.par.sizey, b.par.sizez = x1 - x0, y1 - y0, z1 - z0
        b.par.tx, b.par.ty, b.par.tz = 0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1)
        b.outputConnectors[0].connect(merge)
        b.render = b.display = False
    return merge


def _portable(geo, slug, standin, colour, teapot, boxes=None):
    """Make a scaffold model work with no library. Returns the POP to render (`shape`).

    With the library (and a model name): `shape` passes `mesh` through untouched and the material uses `tex`.
    Without: `mesh` is TouchDesigner's teapot (mod.paths.model_file), which `fit` scales and stands
    where the library model stood, or `boxes` take its place; the material uses the flat colour `plain`.
    All of it is decided by expressions, so one saved .tox works on a machine with or without assets.
    """
    have = "mod.paths.have('models/%s/model.obj')" % slug if slug else "False"    # '' = always the boxes
    half, size = standin
    mesh = geo.op('mesh')
    if boxes:
        alt = _boxes(geo, 'standin', boxes)
    else:
        (x0, y0, z0), (x1, y1, z1) = teapot
        k = size / max(x1 - x0, y1 - y0, z1 - z0)
        alt = geo.create(td.transformPOP, 'fit')
        alt.inputConnectors[0].connect(mesh)
        alt.par.scale = k
        alt.par.tx, alt.par.ty, alt.par.tz = -0.5 * (x0 + x1) * k, -half - y0 * k, -0.5 * (z0 + z1) * k
    shape = geo.create(td.switchPOP, 'shape')
    shape.inputConnectors[0].connect(mesh)
    shape.inputConnectors[1].connect(alt)
    shape.par.index.expr = "0 if %s else 1" % have
    for o in (mesh, alt):
        o.render = o.display = False
    shape.render = shape.display = True
    plain = geo.create(td.constantTOP, 'plain')
    plain.par.colorr, plain.par.colorg, plain.par.colorb = colour
    plain.par.outputresolution = 'custom'
    plain.par.resolutionw = plain.par.resolutionh = 16
    geo.op('mat').par.basecolormap.expr = (
        "op('tex') if mod.paths.model_texture(%r) else op('plain')" % slug if slug else "op('plain')")
    return shape


def build():
    LIB = {'op': op}
    exec(open(td.project.folder.replace(chr(92), '/') + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    teapot = _obj_bounds(LIB['samples']() + '/Geo/UtahTeapot.obj')
    scene = LIB['new_scene'](SLUG, x=1500, y=-1100)
    W = LIB['scene_words'](scene, DEFAULTS)
    MON, DESK = W['MONITOR'], W['DESK']
    out1 = scene.op('out1')
    scene.op('cook_driver').text = DRIVER

    # ---- per-take values and derived controls --------------------------------------
    _place(scene.op('shot'), 0)
    tk = _chop(scene, 'tk', [(k, tkexpr(k)) for k in DEFAULT])
    seed = "parent().par.Seed"
    # level transform, shared by the screen shader and by the compensation in post
    lv = _chop(scene, 'lv', [
        ('hue', "(%s['hue'] * (0.75 + 0.5 * %s) + %s['hk'] * min(1.2, %s['hit_low'])) * (1 - 2 * %s['secflip'] * (int(%s['section']) %% 2))"
                % (TK, seed, TK, H, TK, H)),
        ('gain', "%s['gain']" % TK),
        ('rot', "%s['rot'] * (0.6 + 0.4 * math.sin(%s['bar_pos'] * math.pi)) + 5 * %s['rot'] / 14 * min(1.5, %s['bass'])" % (TK, H, TK, H)),
        ('zoom', "%s['zoom']" % TK),
        ('p', "(%s['bar_pos'] / %s['bars']) %% 1" % (H, TK)),
    ])
    cam_a = _chop(scene, 'cam_a', [
        ('az', "math.radians(%s['az'] + %s['orb'] * math.sin(%s['evolve'] * 0.9 + %s * 6.283) + (%s - 0.5) * %s['seedaz'])" % (TK, TK, H, seed, seed, TK)),
        ('el', "math.radians(%s['el'] + 0.4 * %s['orb'] * math.sin(%s['evolve'] * 0.63 + 1.7)) + %r" % (TK, TK, H, TAU)),
        ('dist', "%s['dist'] * (1 - %s['punch'] * min(1.2, %s['hit_low']))" % (TK, TK, H)),
        ('oaz', "math.radians(%s['oaz'] + 3 * math.sin(%s['evolve'] * 0.8) + (%s - 0.5) * 10)" % (TK, H, seed)),
        ('oel', "math.radians(%s['oel']) + %r" % (TK, TAU)),
        # dolly: exponential in distance, so the apparent zoom rate is constant and the wrap is seamless
        ('e', "(%s['dist'] * (%r / %s['dist']) ** op('lv')['p'] - %s['dist']) / (%r - %s['dist'] - 1e-6)" % (TK, D1, TK, TK, D1, TK)),
    ])
    A = "op('cam_a')"
    cx, cy, cz = SCR_C
    mpos = ["%r + %s['dist'] * math.sin(%s['az']) * math.cos(%s['el'])" % (cx, A, A, A),
            "%r + %s['dist'] * math.sin(%s['el'])" % (cy, A, A),
            "%r + %s['dist'] * math.cos(%s['az']) * math.cos(%s['el'])" % (cz, A, A, A)]
    mlook = ["%r + %s['tgx']" % (cx, TK), "%r + %s['tgy']" % (cy, TK), "%r" % cz]
    fpos = [cx, cy + D1 * math.sin(TAU), cz + D1 * math.cos(TAU)]
    free = ["%r + %s['odist'] * math.sin(%s['oaz']) * math.cos(%s['oel'])" % (cx, TK, A, A),
            "%r + %s['odist'] * math.sin(%s['oel'])" % (cy, TK, A),
            "%r + %s['odist'] * math.cos(%s['oaz']) * math.cos(%s['oel'])" % (cz, TK, A, A)]
    flook = ["%r + %s['otgx']" % (cx, TK), "%r + %s['otgy']" % (cy, TK), "%r" % cz]
    camm = _chop(scene, 'camm', [(n, e) for n, e in zip(('px', 'py', 'pz', 'lx', 'ly', 'lz'), mpos + mlook)])
    M = "op('camm')"
    ochans = []
    for i, n in enumerate(('px', 'py', 'pz')):
        ochans.append((n, "(%s) if %s['omode'] > 0.5 else %s['%s'] + (%r - %s['%s']) * %s['e']" % (free[i], TK, M, n, fpos[i], M, n, A)))
    for i, n in enumerate(('lx', 'ly', 'lz')):
        ochans.append((n, "(%s) if %s['omode'] > 0.5 else %s['%s'] + (%r - %s['%s']) * %s['e']" % (flook[i], TK, M, n, SCR_C[i], M, n, A)))
    camo = _chop(scene, 'camo', ochans)

    # ---- Input: another scene's picture as this scene's raw material (blank = none) -------
    # `on` is 1 only for a TOP that exists and is not inside this scene (reading our own out1 is a cook loop).
    src = "parent().par.Input.eval().strip()"
    _chop(scene, 'inon', [
        ('on', "1 if (%s and op(%s) is not None and op(%s).isTOP and not op(%s).path.startswith(parent().path + '/')) else 0" % (src, src, src, src)),
    ])
    inc = _chop(scene, 'inc', [
        ('bg', "1 if op('inon')['on'] > 0.5 and int(%s['inp']) in (1, 3) else 0" % TK),
        ('gl', "1 if op('inon')['on'] > 0.5 and int(%s['inp']) in (2, 3) else 0" % TK),
    ])
    IN = "op('inc')"

    cams = {}
    for nm, ch in (('m', 'camm'), ('o', 'camo')):
        tgt = _place(scene.create(td.nullCOMP, 'tgt_' + nm), 1 if nm == 'm' else None)
        for a, c in zip('xyz', ('lx', 'ly', 'lz')):
            getattr(tgt.par, 't' + a).expr = "op('%s')['%s']" % (ch, c)
        cam = _place(scene.create(td.cameraCOMP, 'cam_' + nm))
        for a, c in zip('xyz', ('px', 'py', 'pz')):
            getattr(cam.par, 't' + a).expr = "op('%s')['%s']" % (ch, c)
        cam.par.lookat = tgt.path
        cam.par.fov = FOV
        cam.par.near, cam.par.far = 0.05, 80
        cams[nm] = cam

    # ---- the room ----------------------------------------------------------------------
    def plane(name, size, t, r, col, rough):
        g = _place(scene.create(td.geometryCOMP, name))
        for c in g.children:
            c.destroy()
        gr = g.create(td.gridSOP, 'grid')
        gr.par.sizex, gr.par.sizey = size
        gr.par.rows = gr.par.cols = 2
        gr.render = gr.display = True
        m = g.create(td.pbrMAT, 'mat')
        m.par.basecolorr, m.par.basecolorg, m.par.basecolorb = col
        m.par.metallic, m.par.roughness = 0, rough
        g.par.material = m.path
        g.par.tx, g.par.ty, g.par.tz = t
        g.par.rx, g.par.ry, g.par.rz = r
        g.par.render.expr = "%s['room'] > 0.5" % TK
        return g
    _pos[0], _pos[1] = 2, 0
    floor = plane('r_floor', (24, 24), (0, 0, 2), (-90, 0, 0), (0.20, 0.21, 0.19), 0.85)
    wall = plane('r_wall', (24, 9), (0, 4.5, -1.75), (0, 0, 0), (0.27, 0.34, 0.30), 0.8)
    for g in (wall, floor):   # a given picture stands in for the wall and the floor: the desk hangs in front of it
        g.par.render.expr = "%s['room'] > 0.5 and %s['bg'] < 0.5" % (TK, IN)
    for a, k in zip('rgb', ('wr', 'wg', 'wb')):
        getattr(wall.op('mat').par, 'basecolor' + a).expr = "parent(2).op('tk')['%s']" % k

    desk = _place(LIB['import_model'](scene, 'm_desk', DESK['model']))
    desk.par.scale = DESK_S
    desk.par.ty = DESK_TOP / 2
    desk.par.render.expr = "%s['room'] > 0.5" % TK
    _portable(desk, DESK['model'], (0, 1), DESK['colour'], teapot, DESK_BOXES)
    crt = _place(LIB['import_model'](scene, 'm_crt', MON['model']))
    _portable(crt, MON['model'], (0, 1), MON['colour'], teapot, CRT_BOXES)
    crt.par.sx, crt.par.sy, crt.par.sz = CRT_SX, CRT_SY, CRT_SZ
    crt.par.tx, crt.par.ty, crt.par.tz = CRT_T
    crt.op('mat').par.roughness = 0.5

    # the glass: a grid fitted to the tube's bulge, inside the CRT so it shares its transform
    scrgeo = crt.create(td.geometryCOMP, 'scrn')
    for c in scrgeo.children:
        c.destroy()
    gr = scrgeo.create(td.gridSOP, 'grid')
    gr.par.sizex, gr.par.sizey = REC_X1 - REC_X0, REC_Y1 - REC_Y0
    gr.par.tx, gr.par.ty = XC, YC
    gr.par.rows, gr.par.cols = 9, 13
    pt = scrgeo.create(td.pointSOP, 'bulge')
    pt.inputConnectors[0].connect(gr)
    pt.par.tz.expr = "%r + %r * (me.inputPoint.y - %r) + %r * (me.inputPoint.y - %r) ** 2 + %r * (me.inputPoint.x - %r) ** 2" % (
        Z0 + 0.004, ZB, YC, ZC, YC, ZD, XC)
    pt.render = pt.display = True
    gr.render = gr.display = False
    smat = scrgeo.create(td.constantMAT, 'mat')
    smat.par.colormap = scene.path + '/scr'
    scrgeo.par.material = smat.path

    props = {}
    for row in W['PROPS']:
        slug, (tx, dy, tz), ry = row['model'], row['at'], row['ry']
        g = _place(LIB['import_model'](scene, 'm_' + row['role'], slug))
        g.par.scale = row['scale']
        g.par.tx, g.par.ty, g.par.tz = tx, DESK_TOP + dy, tz
        g.par.ry = ry
        g.par.render.expr = "%s['room'] > 0.5" % TK
        _portable(g, slug, row['standin'], row['colour'], teapot)
        props[row['role']] = (g, DESK_TOP + dy, ry, slug)
    # what the music does to each role
    g, y, ry, slug = props['snare']
    g.par.ty.expr = "%r + 0.22 * min(1.2, %s['hit_mid'])" % (y, H)
    g.par.rz.expr = "14 * %s['hit_mid']" % H
    g, y, ry, slug = props['hat']
    g.par.ty.expr = "%r + 0.10 * min(1.2, %s['hit_high'])" % (y, H)
    g.par.ry.expr = "%r + 25 * math.sin(%s['beat_pos'] * math.pi * 0.5)" % (ry, H)
    g, y, ry, slug = props['rattle']
    g.par.rz.expr = "5 * %s['hit_high'] * math.sin(absTime.seconds * 70)" % H
    g, y, ry, slug = props['kick']
    g.par.ty.expr = "%r + 0.05 * min(1.2, %s['hit_low'])" % (y, H)
    g, y, ry, slug = props['glow']
    g.par.rz.expr = "3 * math.sin(%s['beat_pos'] * math.pi)" % H
    lm = g.op('mat')
    for a in 'rgb':
        getattr(lm.par, 'emit' + a).expr = "0.25 + 0.9 * min(1.3, parent(2).op('hub')['hit_low'])"
    lm.par.emitmap.expr = "op('tex') if mod.paths.model_texture(%r) else op('plain')" % slug
    P = scene.op('local/modules/paths').module      # the installed module: it sees the Assets parameter
    for g, slug in [(v[0], v[3]) for v in props.values()] + [(desk, DESK['model']), (crt, MON['model'])]:
        for n in ('mesh', 'shape', 'mat') + (('tex',) if slug and P.model_texture(slug) else ()):
            g.op(n).cook(force=True)

    # ---- take "wall of monitors": 14 more CRTs stacked around the hero, all showing the same feed ----
    inst = _place(scene.create(td.tableDAT, 'winst'))
    inst.clear()
    inst.appendRow(['tx', 'ty', 'tz'])
    px, py = 0.652 * CRT_SX * 1.015, 0.744 * CRT_SY * 1.01
    for j in (-1, 0, 1):
        for i in (-2, -1, 0, 1, 2):
            if (i, j) != (0, 0):
                inst.appendRow([CRT_T[0] + i * px, CRT_T[1] + j * py, CRT_T[2] - 0.12 * abs(i)])
    wc = _place(scene.create(td.geometryCOMP, 'w_crt'))
    for c in wc.children:
        c.destroy()
    wm = wc.create(td.fileinPOP, 'mesh')
    wm.par.file.expr = "mod.paths.model_file(%r)" % MON['model']
    wsh = wc.create(td.switchPOP, 'shape')     # the same choice as m_crt/shape: the model, or the box monitor
    wsh.inputConnectors[0].connect(wm)
    wsh.inputConnectors[1].connect(_boxes(wc, 'standin', CRT_BOXES))
    wsh.par.index.expr = crt.op('shape').par.index.expr
    wsh.render = wsh.display = False
    wx = wc.create(td.transformPOP, 'xf')
    wx.inputConnectors[0].connect(wsh)
    wx.par.sx, wx.par.sy, wx.par.sz = CRT_SX, CRT_SY, CRT_SZ
    wx.render = wx.display = True
    wm.render = wm.display = False
    wc.par.material = crt.op('mat').path
    ws = _place(scene.create(td.geometryCOMP, 'w_scrn'))
    for c in ws.children:
        c.destroy()
    g1 = ws.create(td.gridSOP, 'grid')
    g1.par.sizex, g1.par.sizey = REC_X1 - REC_X0, REC_Y1 - REC_Y0
    g1.par.tx, g1.par.ty = XC, YC
    g1.par.rows, g1.par.cols = 9, 13
    p1 = ws.create(td.pointSOP, 'bulge')
    p1.inputConnectors[0].connect(g1)
    p1.par.tz.expr = pt.par.tz.expr
    x1 = ws.create(td.transformSOP, 'xf')
    x1.inputConnectors[0].connect(p1)
    x1.par.sx, x1.par.sy, x1.par.sz = CRT_SX, CRT_SY, CRT_SZ
    x1.render = x1.display = True
    g1.render = g1.display = p1.render = p1.display = False
    ws.par.material = smat.path
    for g in (wc, ws):
        g.par.instancing = True
        g.par.instanceop = inst.path
        g.par.instancetx, g.par.instancety, g.par.instancetz = 'tx', 'ty', 'tz'
        g.par.render.expr = "%s['wall'] > 0.5" % TK

    # ---- lights --------------------------------------------------------------------------
    _pos[0], _pos[1] = 4, 0
    aim = _place(scene.create(td.nullCOMP, 'lamp_aim'))
    aim.par.tx, aim.par.ty, aim.par.tz = 0.1, DESK_TOP, 0.35

    def light(name, pos, cols, dim, kind='point'):
        l = _place(scene.create(td.lightCOMP, name))
        l.par.tx, l.par.ty, l.par.tz = pos
        for a, e in zip(('cr', 'cg', 'cb'), cols):
            getattr(l.par, a).expr = e
        l.par.dimmer.expr = dim
        l.par.lighttype = kind
        return l
    lamp = light('light_lamp', (0.85, DESK_TOP + 0.92, 0.0),
                 ["%s['lr']" % TK, "%s['lg']" % TK, "%s['lb']" % TK],
                 "%s['lamp'] * (0.6 + 1.4 * min(1.3, %s['hit_low']) + 0.25 * %s['pulse'])" % (TK, H, H), 'cone')
    lamp.par.lookat = aim.path
    lamp.par.coneangle, lamp.par.conedelta = 70, 40
    fluor = light('light_fluor', (-2.2, 5.0, 6.0),
                  ["%s['fr']" % TK, "%s['fg']" % TK, "%s['fb']" % TK],
                  "%s['fluor'] * (0.85 + 0.3 * %s['energy'] + 0.5 * %s['hit_mid'])" % (TK, H, H))
    glow = light('light_glow', (cx, cy + 0.1, cz + 0.9),
                 ['0.45', '0.62', '0.80'],
                 "%s['glow'] * (0.5 + 0.6 * %s['pulse'])" % (TK, H))
    glow.par.attenuated = True
    glow.par.attenuationstart, glow.par.attenuationend = 0.3, 3.5
    rim = light('light_rim', (-4.0, 3.2, -1.2),
                ["%s['rr']" % TK, "%s['rg']" % TK, "%s['rb']" % TK],
                "%s['rimd'] * (0.7 + 0.8 * %s['hit_mid'])" % (TK, H))

    # ---- the loop: master render -> feedback -> (delay) -> screen shader -> the glass ---------
    _pos[0], _pos[1] = 5, 0
    black = _place(scene.create(td.constantTOP, 'black'))
    black.par.colorr = black.par.colorg = black.par.colorb = 0
    black.par.outputresolution = 'custom'
    black.par.resolutionw, black.par.resolutionh = 1280, 720
    black.par.format = 'rgba16float'
    fb = _place(scene.create(td.feedbackTOP, 'fb'))
    fb.inputConnectors[0].connect(black)
    fb.par.top = 'mast'
    # per-level delay: 16 frames at 1280x720 is the same memory as the brief's 64 at 640x360
    cache = _place(scene.create(td.cacheTOP, 'cache'))
    cache.inputConnectors[0].connect(fb)
    cache.par.cachesize = 16
    csel = _place(scene.create(td.cacheselectTOP, 'csel'))
    csel.par.cachetop = 'cache'
    csel.par.index.expr = "-int(min(14, %s['delay']))" % TK
    feed = _place(scene.create(td.switchTOP, 'feed'))
    feed.inputConnectors[0].connect(fb)
    feed.inputConnectors[1].connect(csel)
    feed.par.index.expr = "1 if %s['delay'] > 0.5 else 0" % TK

    term = _place(scene.create(td.textTOP, 'term'))
    term.par.outputresolution = 'custom'
    term.par.resolutionw, term.par.resolutionh = 1280, 720
    term.par.fontfile.expr = CHICAGO
    term.par.font = FALLBACK_FONT
    term.par.bold.expr = "not %s" % CHICAGO
    term.par.bgalpha = 0
    terms = _place(scene.create(td.tableDAT, 'terms'))
    terms.clear()
    for t in W['TERMS']:
        terms.appendRow([t])
    phr = _place(scene.create(td.tableDAT, 'phr'))
    phr.clear()
    for t in W['PHRASES']:
        phr.appendRow([t])
    # Describe mode: the same two tables again, holding each take's `describe` words
    terms_d = _place(scene.create(td.tableDAT, 'terms_d'))
    terms_d.clear()
    for t in [t for t in TAKES if t.get('text', 0) == 1][0]['describe']:
        terms_d.appendRow([t])
    phr_d = _place(scene.create(td.tableDAT, 'phr_d'))
    phr_d.clear()
    for t in [t for t in TAKES if t.get('text', 0) == 2][0]['describe']:
        phr_d.appendRow([t])
    # text 1: a terminal screen typed out from the cut. text 2: one phrase per beat, centred
    # (in Describe mode the beats run through the list in order, with no seed offset: it reads as sentences).
    TT = "op('terms_d' if parent().par.Describe else 'terms')"
    PP = "op('phr_d' if parent().par.Describe else 'phr')"
    term.par.text.expr = ("'' if %s['text'] < 0.5 else ("
                          "(%s[int(parent().par.Seed * 997) %% %s.numRows, 0].val.replace('|', chr(10))[:int(%s['age'] * 26)]"
                          " + ('_' if int(absTime.seconds * 4) %% 2 else ' ')) if %s['text'] < 1.5 else "
                          "%s[(int(%s['beat_i']) + (0 if parent().par.Describe else int(parent().par.Seed * 997))) %% %s.numRows, 0].val.replace('|', chr(10)))"
                          % (TK, TT, TT, SH, TK, PP, H, PP))
    term.par.alignx.expr = "'center' if %s['text'] > 1.5 else 'left'" % TK
    term.par.aligny.expr = "'center' if %s['text'] > 1.5 else 'top'" % TK
    term.par.fontsizex.expr = "150 if %s['text'] > 1.5 else 46" % TK
    term.par.linespacing = 14
    term.par.borderspace1, term.par.borderspace2 = 90, 80

    scr = _glsl(scene, 'scr', 'screen.frag', 1280, 720, 'rgba16float', [
        ('uT', ["op('lv')['hue']", "op('lv')['gain']", "op('lv')['rot']", "op('lv')['zoom']"]),
        ('uM', ["%s['inv']" % TK, "%s['mono']" % TK, "%s['flip']" % TK, "%s['scan']" % TK]),
        # text amount; in 'words out' a given picture takes the words' place (unless Describe wants them)
        ('uS', ["%s['age']" % SH,
                "(1 if %s['text'] < 1.5 else float(%s['beat'] < 0.45) * (0 if (%s['gl'] > 0.5 and not parent().par.Describe) else 1)) * min(1, %s['text'])" % (TK, H, IN, TK),
                "%s['pulse']" % H, "%s['edge']" % TK]),
        ('uTint', ["%s['tr']" % TK, "%s['tg']" % TK, "%s['tb']" % TK, "%s['lsat']" % TK]),
        ('uX', ["%s['tscale']" % TK, "%s['kick'] * min(1.2, %s['hit_low'])" % (TK, H), "%s['inlit']" % TK, '0']),
        # Input drawn on the glass: on (in 'words out' only while the beat's stamp is down), mix, scale, key
        ('uI', ["%s['gl'] * (1 if %s['text'] < 1.5 else float(%s['beat'] < 0.45))" % (IN, TK, H),
                "%s['inmix']" % TK, "%s['inscale']" % TK, "%s['inkey']" % TK]),
    ])
    # the given picture: a Select TOP that only reads the named TOP (or `black` when Input is blank or unusable)
    insel = _place(scene.create(td.selectTOP, 'insel'))
    insel.par.top.expr = "%s if op('inon')['on'] > 0.5 else 'black'" % src
    insel.par.outputresolution = 'custom'
    insel.par.resolutionw, insel.par.resolutionh = 1280, 720
    inlev = _place(scene.create(td.levelTOP, 'inlev'))
    inlev.inputConnectors[0].connect(insel)
    inlev.par.brightness1.expr = "%s['ingain']" % TK
    scr.inputConnectors[0].connect(feed)
    scr.inputConnectors[1].connect(term)
    scr.inputConnectors[2].connect(inlev)
    scr.par.inputextenduv = 'zero'

    def render(name, cam):
        r = _place(scene.create(td.renderTOP, name))
        r.par.camera = cam.path
        r.par.geometry = 'm_* r_* w_* m_crt/scrn'
        r.par.lights = 'light_*'
        r.par.outputresolution = 'custom'
        r.par.resolutionw, r.par.resolutionh = 1280, 720
        r.par.antialias = 'aa4'
        r.par.format = 'rgba16float'
        r.par.bgcolorr, r.par.bgcolorg, r.par.bgcolorb, r.par.bgcolora = 0.004, 0.006, 0.01, 1
        # with a backdrop picture the empty background is transparent, so the picture shows behind the set
        r.par.bgcolora.expr = "0 if %s['bg'] > 0.5 else 1" % IN
        return r

    def backed(name, r):
        """`r` itself when Input is blank or not a backdrop here; otherwise `r` over the given picture."""
        ov = _place(scene.create(td.overTOP, name + '_ov'))
        ov.inputConnectors[0].connect(r)
        ov.inputConnectors[1].connect(inlev)
        ov.par.format = 'rgba16float'
        sw = _place(scene.create(td.switchTOP, name + '_in'))
        sw.inputConnectors[0].connect(r)
        sw.inputConnectors[1].connect(ov)
        sw.par.index.expr = "1 if %s['bg'] > 0.5 else 0" % IN
        return sw
    _pos[0], _pos[1] = 6, 0
    rm = render('render_m', cams['m'])
    mast = _place(scene.create(td.nullTOP, 'mast'))
    mast.inputConnectors[0].connect(backed('render_m', rm))
    ro = backed('render_o', render('render_o', cams['o']))
    esc = _glsl(scene, 'escher', 'escher.frag', 1280, 720, 'rgba16float', [
        ('uE', ["%r / %s['dist']" % (D1, TK), "op('lv')['p']", "op('lv')['hue']", "op('lv')['gain']"]),
        ('uE2', ["%s['twist']" % TK, '0', '0', "0"]),
    ])
    esc.inputConnectors[0].connect(mast)
    view = _place(scene.create(td.switchTOP, 'view'))
    view.inputConnectors[0].connect(mast)
    view.inputConnectors[1].connect(ro)
    view.inputConnectors[2].connect(esc)
    mac = _glsl(scene, 'macro', 'macro.frag', 1280, 720, 'rgba16float', [
        ('uP', ["0.36 + 0.10 * math.sin(%s['evolve'] * 0.7 + %s * 6.283)" % (H, seed),
                "0.60 + 0.06 * math.cos(%s['evolve'] * 0.5 + %s * 9.0)" % (H, seed),
                "%s['mz'] * (0.75 + 0.7 * %s) * (1 + 0.10 * min(1.2, %s['hit_low']))" % (TK, seed, H),
                "15 + 3 * int(%s * 2.99)" % seed]),
        ('uQ', ["%s['hit_low']" % H, "min(1.0, %s['hit_high'])" % H, "%s['pulse']" % H, "%s['age']" % SH]),
    ])
    mac.inputConnectors[0].connect(scr)
    view.inputConnectors[3].connect(mac)
    view.par.index.expr = "int(%s['view'])" % TK

    # ---- post (outside the loop) ----------------------------------------------------------
    _pos[0], _pos[1] = 7, 0
    lo = _place(scene.create(td.resolutionTOP, 'glow_lo'))
    lo.inputConnectors[0].connect(view)
    lo.par.outputresolution = 'custom'
    lo.par.resolutionw, lo.par.resolutionh = 320, 180
    blur = _place(scene.create(td.blurTOP, 'glow_blur'))
    blur.inputConnectors[0].connect(lo)
    blur.par.size = 10
    dolly = "(%s['view'] == 1 and %s['omode'] < 0.5)" % (TK, TK)
    post = _glsl(scene, 'post', 'post.frag', 1280, 720, 'rgba8fixed', [
        ('uComp', ["-op('lv')['hue'] * op('lv')['p'] if %s else 0" % dolly,
                   "op('lv')['gain'] ** -op('lv')['p'] if %s else 1" % dolly,
                   "tdu.clamp((op('lv')['p'] - 0.955) / 0.045, 0, 1) if %s else 0" % dolly,
                   "%s['bit']" % TK]),
        ('uA', ["%s['age']" % SH, "%s['pulse']" % H, "min(1.0, %s['hit_high'])" % H, "%s['evolve']" % H]),
        ('uG', ["%s['psat']" % TK, "%s['pcon']" % TK, "%s['vign']" % TK, "%s['grain']" % TK]),
        ('uTintP', ["%s['sr']" % TK, "%s['sg']" % TK, "%s['sb']" % TK, "%s['bloom']" % TK]),
        ('uB', ["min(1.2, %s['hit_low'])" % H, "int(%s['hits_low']) %% 2" % H, '0', '0']),
    ])
    post.inputConnectors[0].connect(view)
    post.inputConnectors[1].connect(blur)
    post.inputConnectors[2].connect(scr)
    # ---- Describe caption for the takes that have no text of their own (after post, never fed back) ----
    caps = _place(scene.create(td.tableDAT, 'caps'))
    caps.clear()
    for t in TAKES:
        d = t.get('describe', [])
        caps.appendRow(d[:3] if t.get('text', 0) == 0 and len(d) == 3 else ['', '', ''])
    row = "int(parent().par.Take) %% %d" % NT

    def captext(name, size, bottom, expr):
        c = _place(scene.create(td.textTOP, name))
        c.par.outputresolution = 'custom'
        c.par.resolutionw, c.par.resolutionh = 1280, 720
        c.par.fontfile.expr = CHICAGO
        c.par.font = FALLBACK_FONT
        c.par.bold.expr = "not %s" % CHICAGO
        c.par.bgalpha = 0
        c.par.fontsizex = size
        c.par.alignx, c.par.aligny = 'left', 'bottom'
        c.par.borderspace1, c.par.borderspace2 = 34, bottom
        c.par.text.expr = expr
        return c
    cap_t = captext('cap_title', 26, 96, "op('caps')[%s, 0].val" % row)
    cap_b = captext('cap_body', 20, 22, "op('caps')[%s, 1].val + chr(10) + op('caps')[%s, 2].val" % (row, row))
    cap_b.par.linespacing = 6
    capfx = _glsl(scene, 'capfx', 'caption.frag', 1280, 720, 'rgba8fixed', [
        ('uC', ['142.0 / 720.0', "%s['bit']" % TK, '0', '0']),
    ])
    capfx.inputConnectors[0].connect(post)
    capfx.inputConnectors[1].connect(cap_b)
    capfx.inputConnectors[2].connect(cap_t)
    final = _place(scene.create(td.switchTOP, 'final'))
    final.inputConnectors[0].connect(post)
    final.inputConnectors[1].connect(capfx)
    final.par.index.expr = "1 if (parent().par.Describe and op('caps')[%s, 0].val) else 0" % row
    out1.inputConnectors[0].connect(final)
    _place(out1)
    # A wider face than the one the captions were written in (a monospace one, say) gets a smaller size:
    # the widest body line, measured with the real font, must fit the frame.
    widest = max([cap_b.evalTextSize(caps[r, c].val)[0] for r in range(caps.numRows) for c in (1, 2)] + [1])
    if widest > 1280 - 2 * 34:
        cap_b.par.fontsizex = 20 * (1280 - 2 * 34) / widest * 0.995
    # widths the Describe words must fit, measured with the real fonts: an empty list means they all fit
    over = []
    for r in range(caps.numRows):
        if caps[r, 0].val:
            for c, top in ((0, cap_t), (1, cap_b), (2, cap_b)):
                if top.evalTextSize(caps[r, c].val)[0] > 1280 - 2 * 34:
                    over.append('caption %d.%d' % (r, c))
    scene.store('describe_overflow', over)
    fb.par.resetpulse.pulse()
    return scene.path
