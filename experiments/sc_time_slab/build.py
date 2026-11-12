# sc_time_slab: slit-scan / time displacement of the pack's models.
# Run inside TouchDesigner (see experiments/sw_hub/SCENE_BRIEF.md). Idempotent.
# see: experiments/sc_time_slab/NOTES.md (2026-11-10)
import td

# No folder is named here: files are found through the paths module the scaffold installs
# (mod.paths in parameter expressions). see: experiments/sw_hub/SCENE_BRIEF.md, "Portability"
FONT = "mod.paths.font('archivo')"      # expressions for Text TOP fontfile parameters;
CHICAGO = "mod.paths.font('chicago')"   # '' (TouchDesigner's default face) when the font is absent
BARLOW = "mod.paths.font('barlow')"
SLUG = 'sc_time_slab'

# Everything a pack may replace: the scene reads these through scene_words() in build(), and a
# pack that holds scenes/sc_time_slab/words.json replaces any of them by name.
DEFAULTS = {
    # One row per model: [pack model, uniform scale, base tilt rx, stand-in colour, stand-in metallic].
    # The last two are used only when the pack has no models: every model is then TouchDesigner's
    # teapot, and the colour is what tells them apart. Metallic over 0.9 also makes the textured
    # model real metal.
    "MODELS": [
        ["gramophone", 2.0, 14, [0.84, 0.80, 0.68], 0.35],
        ["space_helmet", 1.9, 10, [0.30, 0.52, 0.66], 0.35],
        ["hourglass", 1.9, 16, [0.80, 0.18, 0.13], 0.35],
        ["ribbon_loop", 2.1, 6, [0.86, 0.62, 0.22], 0.95],
        ["lander", 1.9, 8, [0.50, 0.60, 0.30], 0.35],
    ],
    # Which rows of MODELS a take may show (the seed picks one); a take not named here may show any.
    "TAKE_MODELS": {
        "twist": [0, 4, 2, 1],
        "rings": [3, 4, 2, 0],
        "triptych": [0, 3, 2, 4],
        "blades_macro": [3, 2, 0],
    },
    # big words for the WORD TEAR map; the shot's seed picks one
    "PHRASES": ["SIGNAL\nNOISE", "DO NOT\nTOUCH", "THEN.\nNOW.", "PLATE\n07", "THE\nLOOP",
                "NOT\nYET", "SOON.\nLATE.", "NO\nSIGNAL", "NOW"],
    # small lines for the PHRASE CRAWL map (text as texture, never one centred word)
    "WALL": ["OBJECT 12-B: USE UNKNOWN.", "EVERY FRAME IS MADE NOW. NONE IS KEPT.",
             "NOTHING HERE IS PRERENDERED.", "LISTEN WITH YOUR EYES.", "HANDLE WITH BOTH HANDS.",
             "FOUND, NOT MADE.", "PLATE 07 OF 64", "SEE THE LAST SECOND BEFORE THIS ONE.",
             "THE HOURGLASS IS RUNNING OUT OF SAND", "SOUND IN. PICTURE OUT. NOW.",
             "EVERYTHING IS LATE", "OBJECT THAT WAS HERE", "CATALOGUE OF UNKNOWN USES",
             "PAST. PRESENT. LATER. IN ORDER.", "LOOP. LOOP. LOOPLOOP.", "SIXTY FRAMES A SECOND",
             "SIGNAL ........ FOUND", "DO NOT TOUCH"],
}
# ---- Describe mode (the COMP's Describe toggle): every word explains the technique ----
# see: experiments/sc_time_slab/NOTES.md, "Fourth pass (Describe and Input, 2026-11-11)"
# Same count as PHRASES: the same seed number picks from either list.
D_PHRASES = ['SLIT\nSCAN', 'TIME\nSLAB', 'THE\nPAST', 'OLDER\nHERE', '64\nFRAMES',
             'TIME\nTEAR', 'NOT\nNOW', 'TIME\nMAP', 'LATE']
# Same count as WALL. Nothing here names the prop: with an Input the prop is not in the picture.
D_WALL = ['EVERY LETTER IS A WINDOW INTO THE PAST.', 'INSIDE A LETTER THE PICTURE IS OLDER.',
          'THE LAST 64 FRAMES ARE KEPT IN A STACK.', 'EACH PIXEL PICKS ITS OWN MOMENT.',
          'THIS TEXT IS THE MAP THAT PICKS IT.', 'NO TEXT IS DRAWN. ONLY TIME IS MOVED.',
          'EACH LINE LOOKS BACK A DIFFERENT AMOUNT.', 'THE CRAWL IS LOCKED TO THE TEMPO.',
          'BASS AND LOUDNESS DEEPEN THE LETTERS.', 'KICK DRUMS DROP STRIPS INTO THE PAST.',
          'RED, GREEN AND BLUE READ DIFFERENT MOMENTS.', 'A TEXTURE 3D TOP HOLDS THE LAST SECOND.',
          'ONE GLSL PASS REBUILDS EVERY FRAME.', 'WHAT STANDS STILL LOOKS NORMAL.',
          'WHAT MOVES IS TORN ALONG THE LETTERS.', 'SLIT-SCAN, WITH WORDS FOR THE SLIT.',
          'HISTORY 640 X 360. OUTPUT 1280 X 720.', 'TIME DISPLACEMENT.']
SLAB = 64          # frames of history (brief cap)
LOOKBACK = 1.0     # seconds of past that a white map pixel reaches
SW, SH = 640, 360  # history resolution (brief cap)
H = "op('hub')"

# One row per take. The cutter counts a scene's visits in its Take parameter; the
# row used is Take % len(TAKES). A tuple means "the shot's seed picks one of these".
#   map    time map in dispmap.frag: 0 words+sweep, 1 ramp (twist), 2 rings, 3 blades,
#          4 none, 5 phrase crawl
#   samp   how the picture is made: 0 slab read by the map, 1 strip photograph (its own
#          scrolling canvas, strip.frag), 2 slab as panels, 3 slab as a contact-sheet grid
#   rooms  bg.frag room: 0 green-black, 1 beige wall, 2 red-black, 3 CRT blue,
#          4 daylight cyclorama, 5 empty black
#   grade  grade.frag: 0 dark studio, 1 daylight, 2 one-bit dither
#   dist, fov, elev, aimy  camera: distance, horizontal field of view, degrees above
#          the horizon, height it looks at
#   px, ps, spin  prop: sideways offset, scale multiplier, spin multiplier
#   bspin  extra spin locked to the tempo, degrees per beat
#   split  how far apart in time R, G and B read (1 = the original fringes)
#   n      panels, or grid columns and rows
#   flip, tumble  1: allowed (the seed decides): letters are "now"; ramp runs sideways
#   inmove  with an Input only: how far the given picture sways sideways with the beat, as a
#          fraction of its width (the prop spins; a picture has to move some other way to be torn)
#   describe  (title, sentence): the caption laid along the bottom in Describe mode. {n} is this
#          shot's panel or column count, {nn} its square, {slices} the twist's slice count.
#          Takes 0 and 7 also swap their map text for D_PHRASES and D_WALL.
# Which models a take may show is not here: it differs between packs (DEFAULTS, TAKE_MODELS).
DEFAULT = dict(map=0, samp=0, rooms=(0,), grade=0, bloom=1, dist=3.4, fov=60, elev=0, aimy=0,
               px=0.5, ps=1.0, spin=1.0, bspin=0, split=1.0, n=(3,), flip=0, tumble=0,
               describe=('', ''), inmove=0.015)
TAKES = [
    dict(name='word_tear', rooms=(0, 2, 3),   # flip=1 was tried: the words stop reading (r15, g_take_0_s37)
         describe=('TIME DISPLACEMENT', 'The letters are not drawn. Inside them the picture is up to a second '
                   'older, so whatever moves tears.')),
    # tumble=1 was tried: it shows the models' dark undersides (d_take_1_s31)
    dict(name='twist', map=1, rooms=(5,), dist=4.3, elev=-6, px=0, ps=1.3, bspin=150, split=0.5, inmove=0.10,
         describe=('SLIT-SCAN IN {slices} SLICES', 'Each slice shows a different moment of the last second, '
                   'so anything that moves is cut into steps.')),
    dict(name='strip_photo', map=4, samp=1, rooms=(3, 2, 0), px=0, ps=1.15, bspin=90, split=0, inmove=0.30,
         describe=('STRIP PHOTOGRAPH', 'One thin slit of the picture is recorded each frame and laid beside '
                   'the last, so across is time.')),
    dict(name='rings', map=2, rooms=(2, 3, 0), dist=5.6, elev=58, px=0, ps=1.8, spin=2.5,
         describe=('RINGS OF THE PAST', 'Each ring is an older moment. A new one leaves the centre on every '
                   'beat. Kick drums push rings back.')),
    dict(name='triptych', map=4, samp=2, rooms=(5,), px=0, ps=0.5, spin=1.5, split=0.4, n=(3, 4, 5),
         describe=('{n} MOMENTS', 'The same view at {n} moments of the last second. Each kick drum '
                   'moves the present one panel along.')),
    dict(name='contact_sheet', map=4, samp=3, rooms=(5, 4), grade=2, bloom=0, px=0, ps=1.25, spin=1.3,
         split=0, n=(4, 6, 8),
         describe=('CONTACT SHEET OF ONE SECOND', '{nn} frames from the last second in reading order, '
                   'newest at top left, drawn in black and white dots.')),
    dict(name='blades_macro', map=3, rooms=(0, 3, 2), fov=17, px=0, split=2.4,
         describe=('BLADES OF TIME', 'Each slanted blade shows one of four moments of the last second. '
                   'Kick drums reshuffle them.')),
    dict(name='phrase_crawl', map=5, rooms=(1,), grade=1, bloom=0, dist=2.9, elev=16, px=0.75, ps=1.25,
         split=0.6,
         describe=('TEXT AS A TIME MAP', 'No text is drawn. Each letter is a window: inside it the picture is '
                   'up to a second older.')),
]
NT = len(TAKES)
TK = "int(op('shot')['take']) %% %d" % NT


def _take(field):
    """Expression: this take's value of a plain field."""
    return "%r[%s]" % (tuple(dict(DEFAULT, **t)[field] for t in TAKES), TK)


def _pick(field, seed_chan, shift=''):
    """Expression: the seed's choice among this take's options for a tuple field."""
    return _pick_from([dict(DEFAULT, **t)[field] for t in TAKES], seed_chan, shift)


def _pick_from(options, seed_chan, shift=''):
    """Expression: the seed's choice among this take's options (one row of options per take).

    shift: an expression added to the choice (the take number, so that two takes
    given similar seeds still start on different models).
    """
    return "(lambda o: o[(int(op('sd')['%s'] * len(o))%s) %% len(o)])(%r[%s])" % (
        seed_chan, shift and ' + ' + shift, tuple(tuple(o) for o in options), TK)


# Advances the slab's write index once per frame, only while the scene is cooking,
# and measures the real frame rate so the shader can look back in seconds, not frames.
# It also accumulates drum hits into `acc` from the feed's counters, ignoring the
# backwards step when the track loops, so the prop never whips back at the loop.
# And it counts the frames stored since this shot's take and seed were set (or since
# the scene last stopped cooking): the shader never reads further back than that, so
# a cut cannot show plates from an earlier take. Counted in cooks, not seconds: under
# load the shared instance drops frames and age x fps overshoots (arr_take_1.png).
# "Stopped cooking" means a gap of over 30 frames: with 3, dropped frames under load reset
# the count all the time and the time map went flat (f_take_1.png).
HEAD_DRIVER = '''import time
_last = [0.0]
_prev = [None, None]
_shot = [None, 0]
_ran = [0]

def onFrameStart(frame):
    # "on" = out1 was cooked this frame or last, whoever asked: the scene's own
    # cook_driver, or the cutter warming it up or using it as a layer (the cutter
    # cooks out1 directly, without Preview and without making it the hub's scene)
    # "last" means the last frame this ran, not absTime.frame - 1: under load TouchDesigner
    # skips frame numbers (7 at a time at 8 fps, 2026-11-11), and "<= 1" then never held,
    # so the slab stood still (i2_sheet.png).
    ran, _ran[0] = _ran[0], absTime.frame
    if op('out1').cookAbsFrame >= min(ran, absTime.frame - 1):
        h = op('head')
        h.par.value0 = (int(h.par.value0.eval()) + 1) %% %d
        key = (int(parent().par.Take.eval()), round(parent().par.Seed.eval(), 5), parent().par.Input.eval())
        if key != _shot[0]:
            op('strip_fb').par.resetpulse.pulse()   # a new shot starts a new strip
        if key != _shot[0] or absTime.frame - _shot[1] > 30:
            h.par.value2 = 0
        else:
            h.par.value2 = h.par.value2.eval() + 1
        _shot[0], _shot[1] = key, absTime.frame
        now = time.perf_counter()
        dt = now - _last[0]
        _last[0] = now
        if 0.004 < dt < 0.3:
            h.par.value1 = h.par.value1.eval() * 0.92 + (1.0 / dt) * 0.08
        hb = op('hub')
        a = op('acc')
        for i, nm in enumerate(('hits_low', 'hits_mid')):
            v = float(hb[nm])
            if _prev[i] is not None and 0 < v - _prev[i] < 4:
                p = getattr(a.par, 'value' + str(i))
                p.val = p.eval() + (v - _prev[i])
            _prev[i] = v
    return
''' % SLAB


def _glsl(scene, name, frag, w, h, fmt, uniforms):
    dat = scene.create(td.textDAT, name + '_frag')
    dat.par.file.expr = "mod.paths.here('shaders/%s')" % frag
    dat.par.syncfile = True
    top = scene.create(td.glslTOP, name)
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


def _const(scene, name, chans, x, y):
    c = scene.create(td.constantCHOP, name)
    c.seq.const.numBlocks = len(chans)
    for i, (cname, e) in enumerate(chans):
        getattr(c.par, 'const%dname' % i).val = cname
        getattr(c.par, 'const%dvalue' % i).expr = e
    c.nodeX, c.nodeY = x, y
    return c


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, x=250, y=-700)
    out1 = scene.op('out1')
    # the installed module, not LIB's copy: only it sees the COMP's Assets parameter
    paths = LIB['scene_paths'](scene)
    W = LIB['scene_words'](scene, DEFAULTS)
    models = W['MODELS']
    take_models = [W['TAKE_MODELS'].get(t['name'], range(len(models))) for t in TAKES]

    # ---- the shot: four unrelated numbers from the seed, then this take's settings ----
    S = "op('shot')['seed']"
    _const(scene, 'sd', [('s1', "(%s * 7.13) %% 1" % S), ('s2', "(%s * 13.71) %% 1" % S),
                         ('s3', "(%s * 29.37) %% 1" % S), ('s4', "(%s * 53.9) %% 1" % S)], -250, 330)
    chans = [(f, _take(f)) for f in ('map', 'samp', 'grade', 'bloom', 'dist', 'fov', 'elev', 'aimy',
                                     'px', 'ps', 'spin', 'bspin', 'split', 'inmove')]
    chans += [
        ('room', _pick('rooms', 's1')),
        ('model', _pick_from(take_models, 's2', "int(op('shot')['take'])")),
        ('n', _pick('n', 's3')),
        ('flip', "%s and op('sd')['s3'] > 0.75" % _take('flip')),
        ('tumble', "%s and op('sd')['s4'] > 0.5" % _take('tumble')),
        ('side', "1 if op('sd')['s4'] > 0.5 else -1"),
        # arrival: 1 at the cut, gone in about half a second
        ('arrive', "math.exp(-6 * op('shot')['age'])"),
    ]
    _const(scene, 'tk', chans, -100, 330)
    T = "op('tk')"

    # ---- motion: continuous spin from evolve, jolts from drum hit counters ----
    hits = scene.create(td.constantCHOP, 'acc')   # advanced by head_driver
    hits.par.name0, hits.par.name1 = 'hits_low', 'hits_mid'
    jolt = scene.create(td.lagCHOP, 'jolt')
    jolt.inputConnectors[0].connect(hits)
    jolt.par.lag1, jolt.par.lag2 = 0.07, 0.07
    jolt.par.overshoot1, jolt.par.overshoot2 = 0.05, 0.05
    hits.nodeX, hits.nodeY = -200, 200
    jolt.nodeX, jolt.nodeY = -50, 200

    geos = []
    for i, (slug, s, tilt, tint, metal) in enumerate(models):
        g = LIB['import_model'](scene, 'm_' + slug, slug)
        m = g.op('mat')
        if paths.model_texture(slug):
            m.par.basecolormap = g.op('tex').path   # import_model asks the default pack, not this scene's
        if not paths.have('models/%s/model.obj' % slug):
            # No library: the mesh is the teapot, of any size and position. A Transform POP
            # centres it and makes its longest side 1 unit, as the library's models are.
            fit = g.create(td.transformPOP, 'fit')
            fit.inputConnectors[0].connect(g.op('mesh'))
            fit.par.aligntx = fit.par.alignty = fit.par.aligntz = 'origin'
            fit.par.alignscale = 'unity'
            g.op('mesh').render = g.op('mesh').display = False
            fit.render = fit.display = True
        if not paths.model_texture(slug):
            # No picture to wrap it in: a plain colour, one per model
            g.op('tex').destroy()
            m.par.basecolormap = ''
            m.par.basecolorr, m.par.basecolorg, m.par.basecolorb = tint
        g.nodeX, g.nodeY = -400 + 160 * i, -300
        # every model stays loaded; the take and seed choose which one is drawn
        g.par.render.expr = "int(%s['model']) == %d" % (T, i)
        # arrives oversized and whipping round, settles in half a second
        g.par.scale.expr = "%g * %s['ps'] * (1 + 0.10 * %s['hit_low']) * (1 + 0.45 * %s['arrive'])" % (s, T, H, T)
        # Y spin: steady + 38 degrees per kick. X: the prop stays upright enough to be
        # recognised (slow swing), nods 30 degrees on each snare and springs back.
        # tumble: the same spin goes to X instead (for the sideways ramp).
        spin = ("(%s['evolve'] * 70 * %s['spin'] + op('jolt')['hits_low'] * 38 + 200 * %s['arrive']"
                " + %s['beat_pos'] * %s['bspin'])" % (H, T, T, H, T))
        g.par.ry.expr = "(1 - %s['tumble']) * %s" % (T, spin)
        g.par.rx.expr = "%g + 16 * math.sin(%s['bar_pos'] * math.pi) - 30 * %s['hit_mid'] + %s['tumble'] * %s" % (
            tilt, H, H, T, spin)
        g.par.rz.expr = "10 * math.sin(%s['beat_pos'] * math.pi * 0.5)" % H
        # sideways: off centre by the take's amount, on the seed's side
        g.par.tx.expr = "%s['side'] * %s['px']" % (T, T)
        g.par.ty.expr = "0.07 * math.sin(%s['beat_pos'] * math.pi)" % H   # one bounce per two beats
        m.par.metallic, m.par.roughness = 0.35, 0.26   # glossy: the tube environment shows in it
        if metal > 0.9:
            m.par.metallic, m.par.roughness = metal, 0.2   # real metal
        # load now: otherwise each model's first showing costs a 25 to 60 ms hitch mid-track
        for n in ('mesh', 'fit', 'tex', 'mat'):
            if g.op(n):
                g.op(n).cook(force=True)
        geos.append(g)

    # environment: black studio with tubes (env.frag), so gloss and metal have a room to reflect
    envmap = _glsl(scene, 'envmap', 'env.frag', 512, 256, 'rgba16float', [
        ('uA', ["%s['room']" % T, "%s['room'] == 4" % T, '0', '0']),
    ])
    envmap.nodeX, envmap.nodeY = -560, -620
    scene.op('envmap_frag').nodeX, scene.op('envmap_frag').nodeY = -700, -620
    env = scene.create(td.environmentlightCOMP, 'light_env')
    env.par.envlightmap = envmap.path
    env.par.dimmer = 0.85
    env.par.envlightmaprotatey.expr = "%s['evolve'] * 12" % H
    env.nodeX, env.nodeY = -400, -620

    # camera on a rig at the origin: the take sets distance, lens and height; the
    # macro take (narrow lens) also wanders off the prop's centre with the seed
    rig = scene.create(td.nullCOMP, 'cam_rig')
    rig.par.rx.expr = "-%s['elev']" % T
    rig.par.ry.expr = "14 * %s['arrive'] * %s['side']" % (T, T)
    rig.par.tx.expr = "(op('sd')['s1'] - 0.5) * 0.6 if %s['fov'] < 30 else 0" % T
    rig.par.ty.expr = "%s['aimy'] + ((op('sd')['s2'] - 0.5) * 0.7 if %s['fov'] < 30 else 0)" % (T, T)
    rig.nodeX, rig.nodeY = -560, -460
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.inputCOMPConnectors[0].connect(rig)
    cam.par.tz.expr = "%s['dist']" % T
    cam.par.fov.expr = "%s['fov']" % T   # horizontal: 60 at 3.4 shows 3.9 x 2.2 units at the origin
    cam.nodeX, cam.nodeY = -400, -460

    def light(name, pos, col, dim):
        l = scene.create(td.lightCOMP, name)
        l.par.tx, l.par.ty, l.par.tz = pos
        l.par.cr, l.par.cg, l.par.cb = col
        l.par.dimmer = dim
        l.par.lookat = geos[0].path
        return l
    key = light('light_key', (-2.6, 2.8, 3.0), (1.0, 0.93, 0.80), 2.0)
    rim = light('light_rim', (2.8, 1.2, -2.6), (0.72, 1.0, 0.58), 3.0)
    fill = light('light_fill', (1.5, -2.2, 2.2), (0.49, 0.61, 0.69), 0.5)
    rim.par.dimmer.expr = "2.4 + 3.0 * %s['hit_mid'] + 1.5 * %s['pulse']" % (H, H)
    for i, l in enumerate((key, rim, fill)):
        l.nodeX, l.nodeY = -240 + 160 * i, -460

    render = scene.create(td.renderTOP, 'render')
    render.par.camera = 'cam'
    render.par.geometry = 'm_*'
    render.par.lights = 'light_*'
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = SW, SH
    render.par.antialias = 'aa4'
    render.par.format = 'rgba8fixed'
    render.nodeX, render.nodeY = 0, -100

    bg = _glsl(scene, 'bg', 'bg.frag', SW, SH, 'rgba8fixed', [
        ('uA', ["%s['evolve']" % H, "%s['energy']" % H, "%s['pulse']" % H, "int(%s['section'])" % H]),
        ('uB', ["%s['bar_pos']" % H, "%s['hit_mid']" % H, "%s['room']" % T,
                "%s['side'] * min(1, %s['px'] * 2)" % (T, T)]),
    ])
    bg.nodeX, bg.nodeY = 0, 60
    scene.op('bg_frag').nodeX, scene.op('bg_frag').nodeY = -150, 60

    plate = scene.create(td.overTOP, 'plate')
    plate.inputConnectors[0].connect(render)
    plate.inputConnectors[1].connect(bg)
    plate.nodeX, plate.nodeY = 170, -40
    own_plate = plate

    # ---- Input: another scene's picture takes the plate's place and is time-sliced instead ----
    # `inp` says whether the COMP's Input names a usable TOP (not one of our own: a cook loop).
    # Blank or unusable: the Switch stays on our plate and the Select is never cooked.
    _const(scene, 'inp', [('on', "(lambda p: int(bool(p) and op(p) is not None and op(p).isTOP"
                                 " and not op(p).path.startswith(parent().path + '/')))"
                                 "(parent().par.Input.eval().strip())")], 20, 200)
    in_sel = scene.create(td.selectTOP, 'in_sel')
    in_sel.par.top.expr = "parent().par.Input.eval().strip() if op('inp')['on'] else 'strip_blank'"
    in_fit = scene.create(td.fitTOP, 'in_fit')
    in_fit.inputConnectors[0].connect(in_sel)
    in_fit.par.fit = 'fitoutside'
    in_fit.par.outputresolution = 'custom'
    in_fit.par.resolutionw, in_fit.par.resolutionh = SW, SH
    in_fit.par.format = 'rgba8fixed'
    # The technique shows only what moves, and the prop's spin, kick and arrival are gone with an
    # Input, so the given picture gets them back as a move of the whole frame: it sways sideways
    # with the beat (the take's `inmove`), swells on each kick, and arrives oversized like the prop.
    in_move = scene.create(td.transformTOP, 'in_move')
    in_move.inputConnectors[0].connect(in_fit)
    in_move.par.extend = 'mirror'
    in_move.par.tx.expr = "%s['inmove'] * math.sin(%s['beat_pos'] * math.pi)" % (T, H)
    for pn in ('sx', 'sy'):
        getattr(in_move.par, pn).expr = (
            "(1.03 + 0.07 * min(1, %s['hit_low'])) * (1 + 0.25 * %s['arrive'])" % (H, T))
    in_move.nodeX, in_move.nodeY = 320, 330
    plate = scene.create(td.switchTOP, 'plate_sw')
    plate.inputConnectors[0].connect(own_plate)
    plate.inputConnectors[1].connect(in_move)
    plate.par.index.expr = "op('inp')['on']"
    in_sel.nodeX, in_sel.nodeY = 20, 330
    in_fit.nodeX, in_fit.nodeY = 170, 330
    plate.nodeX, plate.nodeY = 260, 60

    # ---- the slab: 64 frames of history as a 2D texture array ----
    slab = scene.create(td.texture3dTOP, 'slab')
    slab.par.type = 'texture2darray'
    slab.par.cachesize = SLAB
    # Our own ring: write one known layer per frame, so the shader knows where "now" is.
    # (In the TOP's own rolling mode the newest layer's index is not exposed.)
    head = scene.create(td.constantCHOP, 'head')
    head.par.name0 = 'head'
    head.par.name1 = 'fps'
    head.par.value1 = 60
    head.par.name2 = 'since'
    head.nodeX, head.nodeY = 340, 100
    hd = scene.create(td.executeDAT, 'head_driver')
    hd.text = HEAD_DRIVER
    hd.par.framestart = True
    hd.par.active = True
    hd.nodeX, hd.nodeY = 340, 200
    slab.par.replacesingle = True
    slab.par.replaceindex.expr = "int(op('head')['head'])"
    slab.inputConnectors[0].connect(plate)
    slab.nodeX, slab.nodeY = 340, -40

    # ---- the time maps' text: one giant phrase, and a wall of small lines ----
    words = scene.create(td.textTOP, 'words')
    words.par.text.expr = "(lambda o: o[int(op('sd')['s3'] * len(o)) %% len(o)])(%r if parent().par.Describe else %r)" % (
        D_PHRASES, W['PHRASES'])
    words.par.fontfile.expr = FONT
    words.par.outputresolution = 'custom'
    words.par.resolutionw, words.par.resolutionh = 1280, 720
    words.par.fontsizex = 250
    words.par.fontautosize = 'fitiffat'   # a six-letter line can be wider than the frame at 250
    words.par.borderspace1, words.par.borderspace2 = 30, 20
    words.par.alignx, words.par.aligny = 'center', 'center'
    words.par.linespacing = -40
    words.par.fontcolorr = words.par.fontcolorg = words.par.fontcolorb = 1
    words.par.bgalpha = 1
    words.par.format = 'mono8fixed'
    words.nodeX, words.nodeY = 170, -260
    soft = scene.create(td.blurTOP, 'words_soft')
    soft.inputConnectors[0].connect(words)
    soft.par.size = 3
    soft.nodeX, soft.nodeY = 340, -260

    # twelve lines of Chicago, 60 px apart (dispmap.frag counts on twelve), each starting
    # part-way through a phrase so no line reads as a centred title. Static: cooks once.
    # Two sheets, the pack's lines and Describe, both made now; a Switch picks one, so the toggle costs nothing.
    walls = []
    for k, (suffix, lines) in enumerate((('', W['WALL']), ('_d', D_WALL))):
        spec = scene.create(td.tableDAT, 'wall_spec' + suffix)
        spec.clear()
        spec.appendRow(['x', 'y', 'text'])
        for i in range(12):
            line = '   '.join(lines[(i * 5 + j) % len(lines)] for j in range(3))
            spec.appendRow([-((i * 173) % 420), 60 * i + 14, line])
        spec.nodeX, spec.nodeY = 170, -520 - 130 * k
        w = scene.create(td.textTOP, 'wall' + suffix)
        w.par.specdat = spec.name
        w.par.fontfile.expr = CHICAGO
        w.par.outputresolution = 'custom'
        w.par.resolutionw, w.par.resolutionh = 1280, 720
        w.par.fontsizex = 44
        w.par.alignx, w.par.aligny = 'left', 'bottom'
        w.par.fontcolorr = w.par.fontcolorg = w.par.fontcolorb = 1
        w.par.bgalpha = 1
        w.par.format = 'mono8fixed'
        w.nodeX, w.nodeY = 340, -520 - 130 * k
        w.cook(force=True)
        walls.append(w)
    wall = scene.create(td.switchTOP, 'wall_sw')
    wall.inputConnectors[0].connect(walls[0])
    wall.inputConnectors[1].connect(walls[1])
    wall.par.index.expr = "int(parent().par.Describe)"
    wall.nodeX, wall.nodeY = 510, -520

    disp = _glsl(scene, 'dispmap', 'dispmap.frag', 1280, 720, 'mono16fixed', [
        ('uA', ["%s['bar']" % H, "%s['bass']" % H, "%s['energy']" % H, "%s['evolve']" % H]),
        ('uB', ["%s['pulse']" % H, "int(%s['section'])" % H, "%s['hit_low']" % H, "%s['beat']" % H]),
        ('uC', ["op('acc')['hits_low']", "%s['hit_mid']" % H, "%s['bar_pos'] %% 64" % H, "%s['beat_pos'] %% 64" % H]),
        ('uT', ["%s['map']" % T, "%s['flip']" % T, "op('sd')['s3']", "op('sd')['s4']"]),
    ])
    disp.inputConnectors[0].connect(soft)
    disp.inputConnectors[1].connect(wall)
    disp.par.inputextenduv = 'repeat'
    disp.nodeX, disp.nodeY = 510, -260
    scene.op('dispmap_frag').nodeX, scene.op('dispmap_frag').nodeY = 510, -380

    # ---- resample the slab per pixel in one pass ----
    depth = ["min(%d, %g * (1 - %g * %s['split']) * op('head')['fps'])" % (SLAB - 2, LOOKBACK, k, T)
             for k in (0, 0.045, 0.09)]
    samp = _glsl(scene, 'slabsample', 'slabsample.frag', 1280, 720, 'rgba16float', [
        ('uHead', ["op('head')['head']", str(SLAB), "op('head')['since']", "%s['samp']" % T]),
        ('uDepth', depth + ['0.012']),
        ('uS', ["%s['n']" % T, "%s['n']" % T, "int(parent().par.Describe)", '0']),
        ('uK', ["op('sd')['s4']", "op('sd')['s1']", "op('acc')['hits_low']", "%s['hit_low']" % H]),
    ])
    samp.inputConnectors[0].connect(slab)
    samp.inputConnectors[1].connect(disp)
    samp.nodeX, samp.nodeY = 700, -40
    scene.op('slabsample_frag').nodeX, scene.op('slabsample_frag').nodeY = 700, -180

    # ---- the strip photograph: a scrolling canvas fed from one slit of the plate ----
    # It cooks only while its take is selected (Switch TOPs cook one input). head_driver
    # clears it when a new shot starts; unexposed canvas is transparent and shows the live
    # plate, so every shot opens on the ordinary picture and the strip wipes across it.
    strip = _glsl(scene, 'strip', 'strip.frag', 1280, 720, 'rgba8fixed', [
        ('uP', ['6', "%s['side']" % T, "0.5 + (op('sd')['s2'] - 0.5) * 0.12", '0.004']),
    ])
    paper = scene.create(td.constantTOP, 'strip_blank')   # what the canvas holds before its first shot
    paper.par.colorr, paper.par.colorg, paper.par.colorb, paper.par.alpha = 0.0, 0.0, 0.0, 0.0
    paper.par.outputresolution = 'custom'
    paper.par.resolutionw, paper.par.resolutionh = 1280, 720
    fb = scene.create(td.feedbackTOP, 'strip_fb')
    fb.inputConnectors[0].connect(paper)
    fb.par.top = strip.name
    strip.inputConnectors[0].connect(plate)
    strip.inputConnectors[1].connect(fb)
    fb.par.resetpulse.pulse()
    strip.nodeX, strip.nodeY = 700, -420
    scene.op('strip_frag').nodeX, scene.op('strip_frag').nodeY = 700, -560
    fb.nodeX, fb.nodeY = 540, -500
    paper.nodeX, paper.nodeY = 400, -640
    pic = scene.create(td.switchTOP, 'pic')
    pic.inputConnectors[0].connect(samp)
    strip_over = scene.create(td.overTOP, 'strip_over')
    strip_over.inputConnectors[0].connect(strip)
    strip_over.inputConnectors[1].connect(plate)
    strip_over.par.size = 'input1'   # the default (input2) made it the plate's 640x360
    strip_over.nodeX, strip_over.nodeY = 800, -300
    pic.inputConnectors[1].connect(strip_over)
    pic.par.index.expr = "1 if int(%s['samp']) == 1 else 0" % T
    pic.nodeX, pic.nodeY = 800, -40

    bloom = scene.create(td.bloomTOP, 'bloom')
    bloom.inputConnectors[0].connect(pic)
    bloom.par.bloomintensity = 0.6   # the default (1.0) turned loud passages into haze
    bloom.par.bloomthreshold = 0.05  # measured: 0.3 adds nothing at all, 0.01 (default) adds 60% to the mean
    bloom.nodeX, bloom.nodeY = 900, 100
    # bright and one-bit takes skip the bloom (it only hazes them); a Switch cooks one input
    post = scene.create(td.switchTOP, 'post')
    post.inputConnectors[0].connect(pic)
    post.inputConnectors[1].connect(bloom)
    # an Input is another scene's finished picture, already graded and glowing: no second bloom (i1_sheet)
    post.par.index.expr = "int(%s['bloom'] and not op('inp')['on'])" % T
    post.nodeX, post.nodeY = 950, -40
    grade = _glsl(scene, 'grade', 'grade.frag', 1280, 720, 'rgba16float', [
        ('uA', ["%s['pulse']" % H, "%s['energy']" % H, "%s['hit_high']" % H, "%s['evolve']" % H]),
        ('uB', ["%s['grade']" % T, "op('sd')['s3']", "op('shot')['age']", '0']),
    ])
    grade.inputConnectors[0].connect(post)
    grade.nodeX, grade.nodeY = 1100, -40
    scene.op('grade_frag').nodeX, scene.op('grade_frag').nodeY = 1100, -180

    # ---- Describe mode: a caption along the bottom naming the take's technique ----
    # Title and sentence come from the take's `describe` row; they read the COMP's Take and Seed
    # directly (not the shot CHOP, which cooks every frame), so the text is drawn once per shot.
    # With Describe off the Switch passes the grade through and none of this cooks.
    pick = ("(lambda t, s3: (lambda n: %%r[t].format(n=n, nn=n * n, slices=10 + int(((s3 * 7) %%%% 1) * 18)))"
            "((lambda o: o[int(s3 * len(o)) %%%% len(o)])(%r[t])))"
            "(int(parent().par.Take) %%%% %d, (parent().par.Seed * 29.37) %%%% 1)" % (
                tuple(tuple(dict(DEFAULT, **t)['n']) for t in TAKES), NT))
    caps = []
    for k, (nm, font, size, hh) in enumerate((('cap_title', FONT, 25, 40), ('cap_body', BARLOW, 30, 44))):
        c = scene.create(td.textTOP, nm)
        c.par.text.expr = pick % (tuple(dict(DEFAULT, **t)['describe'][k] for t in TAKES),)
        c.par.fontfile.expr = font
        c.par.outputresolution = 'custom'
        c.par.resolutionw, c.par.resolutionh = 1280, hh
        c.par.fontsizex = size
        c.par.fontautosize = 'fitiffat'
        c.par.alignx, c.par.aligny = 'left', 'center'
        c.par.borderspace1, c.par.borderspace2 = 30, 0
        c.par.fontcolorr = c.par.fontcolorg = c.par.fontcolorb = 1
        c.par.bgalpha = 0
        c.nodeX, c.nodeY = 1100, -330 - 120 * k
        c.cook(force=True)
        caps.append(c)
    label = _glsl(scene, 'label', 'label.frag', 1280, 720, 'rgba16float', [
        ('uL', ["%s['grade']" % T, '0', '0', '0']),
    ])
    label.inputConnectors[0].connect(grade)
    label.inputConnectors[1].connect(caps[0])
    label.inputConnectors[2].connect(caps[1])
    label.nodeX, label.nodeY = 1250, -200
    scene.op('label_frag').nodeX, scene.op('label_frag').nodeY = 1250, -330
    desc = scene.create(td.switchTOP, 'desc_sw')
    desc.inputConnectors[0].connect(grade)
    desc.inputConnectors[1].connect(label)
    desc.par.index.expr = "int(parent().par.Describe)"
    desc.nodeX, desc.nodeY = 1250, -40
    out1.nodeX = 1400

    out1.inputConnectors[0].connect(desc)
    # compile the caption shader now (its file loads a frame late), not at the first Describe shot
    td.run("o = op('%s/label'); o and o.cook(force=True)" % scene.path, delayFrames=5)
    return scene.path
