# Builder for /project1/sc_rutt_etra. Run inside TouchDesigner:
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open(project.folder + '/experiments/sc_rutt_etra/build.py', encoding='utf-8').read(), g)
#   path = g['build']()
# Idempotent: destroys and rebuilds the whole scene.
import td

SLUG = 'sc_rutt_etra'
# Files are named only through the scene's paths module (local/modules/paths), as expressions.
# see: NOTES.md "Assets" (2026-11-11)

SEG = 384                      # segments along one scan line
MAXLINES = 300
# With no model library every slot is TouchDesigner's teapot: each slot stands it differently
# (degrees about x, degrees about z, lift in units) so the takes that differ by model still
# differ. Slot 2 is lifted because its first take frames the top of its model.
TEAPOT_POSE = [(0, 0, 0), (28, 0, 0), (18, 0, 0.27), (0, -32, 0), (62, 18, 0)]
LABEL_PX, LABEL_H, LABEL_Y = 24, 132, 8    # Describe caption: font px, strip height px, strip's lower edge px

# Everything a pack may replace: the phrases, their typeface, the five models, and how each
# model take frames its model. A pack's scenes/sc_rutt_etra/words.json replaces any of these names whole.
# see: NOTES.md "Words and models" (2026-11-11)
FRAMING_COLS = ('model', 'mscale', 'mty', 'mgain', 'yawr', 'mspin', 'mrock', 'szoom', 'sox', 'soy')
DEFAULTS = {
    'PHRASES': [
        'SOUND\nIN.\nPICTURE\nOUT.', 'NOTHING\nIS\nPRERENDERED.', 'THE KICK\nMOVES\nTHE LINE.',
        'DO NOT\nTOUCH', 'PLATE\n07', 'OBJECT\nNO. 0047', 'LISTEN\nWITH\nYOUR EYES.',
        'EVERY FRAME\nIS NEW', 'LOOP. LOOP.\nLOOPLOOP.', 'A SIGNAL IS\nARRIVING.',
        'ORIGIN\n.......\nUNKNOWN', 'PAST.\nPRESENT.\nLATER.', 'REAL\nTIME', 'SIXTY\nFRAMES',
    ],
    # 'chicago', 'archivo' or 'barlow' (the paths module's font names); '' with no assets is
    # TouchDesigner's default face
    'FONT': 'archivo',
    # slots m0..m4; a take names its slot in FRAMING
    'MODELS': ['amphora', 'gramophone', 'marble_bust', 'space_helmet', 'lander'],
    # take name -> columns of the takes table (FRAMING_COLS only) that fit the take to its model
    'FRAMING': {
        'portrait': dict(model=0, mscale=1.1, szoom=1.15),
        'colouriser': dict(model=2, mscale=1.5, mty=-0.25, mgain=2.3, yawr=70, mspin=0, mrock=32,
                           szoom=1.7, sox=0.06, soy=0.1),
        'negative': dict(model=1, mscale=1.2, szoom=1.1),
        'macro': dict(model=3, mscale=1.3, szoom=1.5),
        'wall': dict(model=4, mscale=1.1),
        'rings': dict(model=0, mscale=1.2),
    },
}

# Every take is one row of numbers for the same machine. Columns not given take DEFAULT.
DEFAULT = dict(
    wm=0.0, wt=0.0, wo=0.0,          # source mix: model, text, oscillators
    ww=0.0, wk=0.0,                  # spectrum waterfall weight; text in the key channel only
    model=0, mscale=1.0, mty=0.0, myaw=0.0, mspin=20.0, mgain=2.4, yawr=360.0, mrock=0.0,   # yawr: yaw range the seed picks from; mrock: rocking, degrees
    tzoom=1.0, tscroll=0.0, oscf=2.0, sblur=4.0,
    szoom=1.0, sox=0.0, soy=0.0,     # which part of the source the raster scans
    lines=100, width=1.6, vert=0,    # scan: 0 horizontal, 1 vertical, 2 disc of rings, 3 drum
    hspread=0.0, hoff=0.0, hamt=0.0, # chroma oscillator on the line counter (turns, offset, amount)
    dy=0.12, dz=0.3, spec=0.05, osc=0.0,
    bend=1.0, tear=1.0, brk=0.8,
    rx=0.0, ry=0.0, rz=0.0, sway=1.0, dist=2.1, camx=0.0, camy=0.0, rh=1.0,   # rh raster height
    cr=0.25, cg=1.0, cb=0.45, hr=0.9, hg=1.0, hb=0.8,   # phosphor, and its hot colour
    base=0.10, lumi=1.0, gain=2.6,
    fb=0.0, fbrot=0.0, fbrotj=0.0, fbzoom=1.0, fbhue=0.0, fbmirror=0, fbin=1.0,
    fbsym=0, fbcut=0.0,              # fbsym 1: rotation per pass is 360/n (n by seed); black-level cut per pass
    colz=0.0, pal=0, bands=5, key=0.0, neg=0.0,
    hidden=0, roll=0.0, flag=0.0, wall=1,
    interlace=1.0, bleed=2.5, snow=1.0, glow=0.9, expo=1.0,
    # with an Input picture: source zoom, gain, how far the beam takes the picture's colour, and
    # whether the picture scrolls sideways with the take's text scroll (the drum turns it)
    iz=1.0, igain=1.2, icol=0.0, iscroll=0.0,
)

TAKES = [
    # 0 wire portrait: the classic. A model as a green relief, three-quarter view.
    dict(name='portrait', wm=1, lines=110, dy=0.09, dz=0.34,
         rx=-26, ry=24, dist=2.2, camy=0.08, expo=1.3, icol=0.7, igain=0.8,
         words=[],
         label='RUTT-ETRA SCAN PROCESSOR\n'
               'A hidden picture of {src} is redrawn as {n} scan lines.\n'
               'The brighter the picture under a line, the higher it lifts.',
         label_in='RUTT-ETRA SCAN PROCESSOR\n'
                  'Another picture is redrawn as {n} scan lines, coloured by it.\n'
                  'The brighter the picture under a line, the higher it lifts.'),
    # 1 colouriser: dense lines face-on, almost a solid picture, luminance bands to hard colours.
    dict(name='colouriser', wm=1, lines=230, width=1.7,
         dy=0.05, dz=0.04, sway=0.2, dist=1.9, cr=1, cg=1, cb=1,
         hr=1, hg=1, hb=1, base=0.05, lumi=1.0, gain=2.6, colz=1, pal=0, roll=1, flag=0.6,
         glow=0.5, bend=1.5, tear=0.6,
         words=[],
         label='COLOURISER\n'
               '{n} scan lines seen face on. Brightness is cut into 5 bands,\n'
               'each given one flat colour. Bass bends the picture sideways.'),
    # 2 mandala: two dozen oscillator lines into the camera-at-monitor loop, n-fold by seed.
    dict(name='mandala', wo=1, wt=0.5, tzoom=0.8, lines=24, width=2.4, dy=0.3, dz=0.0, spec=0.25,
         dist=3.3, sway=0.3, cr=1.0, cg=0.25, cb=0.08, hr=0.1, hg=0.5, hb=1.0, base=0.25,
         fb=0.9, fbsym=1, fbzoom=1.2, fbhue=0.22, fbmirror=1, fbin=0.9, fbcut=0.03, glow=0.5,
         tear=0.4, icol=0.5, igain=1.0,
         words=['FEED\nBACK', 'OSCIL-\nLATORS', 'CAMERA\nAT ITS\nMONITOR', 'SINE\nWAVES'],
         label='VIDEO FEEDBACK\n'
               '{n} lines of sine waves and words, fed back like a camera aimed\n'
               'at its own monitor. Each pass turns them 1/{sym} of a circle.',
         label_in='PICTURE INTO FEEDBACK\n'
                  '{n} lines lifted by another picture, fed back like a camera\n'
                  'aimed at its own monitor. Each pass turns them 1/{sym} of a circle.'),
    # 3 text landscape: a phrase laid back, read as amber terrain.
    dict(name='landscape', wt=1, tzoom=1.15, tscroll=0.05, lines=90, width=1.8, dy=0.0, dz=0.11,
         sblur=3, rx=-32, ry=10, dist=1.45, camy=0.0, cr=1.0, cg=0.55, cb=0.1, hr=1.0, hg=0.9,
         hb=0.6, base=0.12, lumi=1.2, icol=0.45,
         words=['SCAN\nLINES', 'BRIGHT\nLIFTS\nTHE LINE', 'RUTT-\nETRA', 'TEXT AS\nTERRAIN',
                'KICK =\nTALLER', 'SNARE =\nTEAR', 'BASS =\nBEND', 'NOT\nPIXELS'],
         label='TEXT AS TERRAIN\n'
               '{n} scan lines cross {page} that is never shown.\n'
               'Bright parts push the lines up off it. Kicks push further.',
         label_in='PICTURE AS TERRAIN\n'
                  '{n} scan lines cross another picture that is never shown.\n'
                  'Bright parts push the lines up off it. Kicks push further.'),
    # 4 waterfall: no picture. Three seconds of live spectra as a hidden-line mountain range.
    dict(name='waterfall', ww=1.0, lines=72, width=2.0, dy=0.02, dz=0.15, sblur=2, hidden=1,
         rh=1.9, rx=-52, ry=0, sway=0.35, dist=1.5, camy=0.0, mspin=0, cr=0.8, cg=0.85, cb=1.0, hr=1, hg=1, hb=1,
         base=0.5, lumi=0.7, gain=2.4, bend=0.4, tear=0.5, glow=0.6, icol=0.6, igain=0.6,
         words=[],
         label='SPECTRUM WATERFALL\n'
               'Each of {n} lines is the sound spectrum a moment ago: newest\n'
               'in front, low notes in the middle. Near ridges hide far ones.',
         label_in='SPECTRUM OVER A PICTURE\n'
                  '{n} scan lines lifted by another picture, with the last two\n'
                  'seconds of sound spectrum added. Near lines hide far ones.'),
    # 5 negative: dark wires on a lit beige field, the phrase printed behind in flat red.
    dict(name='negative', wm=1, wk=1, tzoom=1.6, tscroll=0.12,
         lines=110, dy=0.14, dz=0.3, rx=-18, ry=-26, dist=1.9, camx=-0.3, cr=1, cg=1, cb=1, hr=1, hg=1,
         hb=1, base=0.32, neg=1, pal=3, key=1.0, glow=0.3, snow=0.6, tear=0.6, igain=0.6,
         words=['KEYER', 'NEGATIVE', 'BLACK\nWIRES', 'FLAT RED\nBEHIND', 'POLARITY\nREVERSED',
                'WORDS\nKEYED\nIN'],
         label='NEGATIVE AND KEYER\n'
               'Polarity reversed: {n} scan lines of {src}, dark on a\n'
               'lit field. A keyer prints these words flat in red behind.'),
    # 6 hidden-line macro: fat vertical lines, a black surface hides the ones behind. Red.
    dict(name='macro', wm=1, lines=46, width=3.4, vert=1, dy=0.0, dz=0.6,
         rx=-34, ry=32, dist=1.5, hidden=1, cr=1.0, cg=0.16, cb=0.1, hr=1.0, hg=0.8,
         hb=0.55, base=0.16, lumi=1.3, sblur=10, tear=0.5, igain=0.5,
         words=[],
         label='HIDDEN LINE, CLOSE UP\n'
               '{n} fat scan lines run top to bottom over {src}, very\n'
               'close. A black surface under the lines hides the ones behind.'),
    # 7 monitor wall: the signal on a bank of small tubes (4, 9 or 16 by seed), no two set up alike.
    dict(name='wall', wm=1, lines=44, width=3.8, dy=0.2, dz=0.3, rx=-22,
         ry=-18, dist=2.0, cr=0.2, cg=1.0, cb=0.5, base=0.25, gain=3.4, colz=0.75, pal=4, wall=3,
         flag=0.5, glow=0.7, expo=1.5, igain=0.7,
         words=[],
         label='MONITOR WALL\n'
               'One scan-line signal on {tiles} tubes, no two set up alike:\n'
               'colour, brightness, hold, mirror, zoom and polarity differ.'),
    # 8 rings: the raster re-patched to circles. Concentric rings scan the picture, each its own hue.
    dict(name='rings', wm=1, vert=2, lines=72, width=1.8, dy=0.0, dz=0.34,
         rx=-38, ry=14, dist=2.35, camy=0.2, hamt=1.0, hspread=0.8, hr=1, hg=1, hb=1, base=0.16, lumi=1.1,
         tear=0.6,
         words=[],
         label='RING SCAN\n'
               'The scan is re-patched from rows to {n} rings over {src}.\n'
               'Each ring has its own hue. Brightness lifts it towards you.'),
    # 9 drum: phrases wrapped round a see-through cylinder of rings, turning.
    dict(name='drum', wt=1, tzoom=0.5556, tscroll=0.25, vert=3, lines=130, width=1.7, dy=0.02,
         dz=0.09, sblur=2.5, hidden=1, rx=22, ry=0, rz=-8, dist=1.8, camx=0.13, camy=-0.05, cr=0.1, cg=0.8, cb=1.0, hr=1.0, hg=0.3, hb=0.7,
         base=0.14, lumi=1.3, tear=0.5, igain=1.0, iscroll=1.0, iz=0.5,   # iz 0.5: the picture goes twice round, so a whole one faces the camera
         words=['SCAN\nLINES', 'DRUM\nSCAN', 'RINGS\nNOT\nROWS', 'WORDS\nPUSH\nOUT', 'RUTT-\nETRA',
                'SNARE =\nTEAR', 'KICK =\nTALLER', 'WRAPPED\nROUND'],
         label='DRUM SCAN\n'
               '{n} rings stacked into a cylinder, {page} wrapped round.\n'
               'Bright parts push the rings out. A black drum hides the back.'),
]
NT = len(TAKES)
COLS = [k for k in DEFAULT]

H = "op('hub')"
S = "op('shot')"
K = "op('tk')"
C = "op('ctl')"
SEED = "float(op('shot')['seed'])"
EN = "min(max((float(op('hub')['energy']) - 0.33) / 0.32, 0.0), 1.0)"
_IP = "parent().par.Input.eval()"
INP = ("1 if (%s and op(%s) is not None and op(%s).isTOP and op(%s).path != op('out1').path) else 0"
       % (_IP, _IP, _IP, _IP))


def _vecs(o, items):
    """Fill a GLSL operator's Vectors sequence. Strings are expressions."""
    o.seq.vec.numBlocks = len(items)
    for i, (name, vals) in enumerate(items):
        o.par['vec%dname' % i] = name
        for comp, v in zip('xyzw', vals):
            p = o.par['vec%dvalue%s' % (i, comp)]
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _dat(scene, name, fname, x, y):
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here('shaders/%s')" % fname
    d.par.syncfile = True
    d.nodeX, d.nodeY = x, y
    return d


def _glsl_top(scene, name, fname, x, y, w=1280, h=720, fmt='rgba16float'):
    d = _dat(scene, name + '_px', fname, x, y - 130)
    g = scene.create(td.glslTOP, name)
    for extra in ('_pixel', '_compute'):
        e = scene.op(name + extra)
        if e:
            e.destroy()
    g.par.pixeldat = d.name
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    g.nodeX, g.nodeY = x, y
    return g


def _const(scene, name, chans, x, y):
    c = scene.create(td.constantCHOP, name)
    c.seq.const.numBlocks = len(chans)
    for i, (n, e) in enumerate(chans):
        c.par['const%dname' % i] = n
        if isinstance(e, str):
            c.par['const%dvalue' % i].expr = e
        else:
            c.par['const%dvalue' % i].val = e
    c.nodeX, c.nodeY = x, y
    return c


def k(col):
    return "float(%s['%s'])" % (K, col)


def c(ch):
    return "%s['%s']" % (C, ch)


def _fit_model(scene, geo, slug, pose):
    """Make a model slot safe with no model library. Everything is a live expression on the
    paths module, so the saved .tox behaves the same on a machine without assets.

    A library model is already centred with its longest side 1 unit and is drawn untouched
    ('pick' input 0). The stand-in (TouchDesigner's teapot) is neither: 'fit' centres it on its
    bounds (mod.fit reads them from the file), scales its longest side to 1 and turns it by this
    slot's pose ('pick' input 1). The texture reader gets a bundled grey image instead of an
    empty path (an empty path is a warning), and the material ignores it.
    """
    have = "mod.paths.have('models/%s/model.obj')" % slug
    path = "mod.paths.model_file(%r)" % slug
    mesh = geo.op('mesh')
    fit = geo.create(td.transformPOP, 'fit')
    fit.inputConnectors[0].connect(mesh)
    for i, axis in enumerate('xyz'):
        fit.par['p' + axis].expr = "mod.fit.center(%s, %d)" % (path, i)
        fit.par['t' + axis].expr = "%r - mod.fit.center(%s, %d)" % (float(pose[2]) if i == 1 else 0.0, path, i)
    fit.par.scale.expr = "mod.fit.scale(%s)" % path
    fit.par.rx, fit.par.rz = float(pose[0]), float(pose[1])
    pick = geo.create(td.switchPOP, 'pick')
    pick.inputConnectors[0].connect(mesh)
    pick.inputConnectors[1].connect(fit)
    pick.par.index.expr = "0 if %s else 1" % have
    mesh.render = False
    mesh.display = False
    pick.render = True
    pick.display = True
    geo.op('tex').par.file.expr = ("mod.paths.asset('models/%s/basecolor.png', mod.paths.samples() + '/Map/GreyWedge.tif')"
                                   % slug)
    geo.op('mat').par.basecolormap.expr = "'tex' if mod.paths.model_texture(%r) else ''" % slug


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 1250, -1100)
    # the scaffold's spectex is a near-empty ramp (TRAPS.md, sc_spectral_terrain): read the full one
    scene.op('spectrum').par.top = '/project1/sw_hub/specraw'
    fitmod = scene.op('local/modules').create(td.textDAT, 'fit')
    fitmod.par.file.expr = "mod.paths.here('fit_module.py')"
    fitmod.par.syncfile = True
    fitmod.par.loadonstartpulse.pulse()
    W = LIB['scene_words'](scene, DEFAULTS)
    PHRASES, MODELS = W['PHRASES'], W['MODELS']
    FONT = "mod.paths.font(%r)" % W['FONT']
    for name, cols in W['FRAMING'].items():
        extra = [col for col in cols if col not in FRAMING_COLS]
        if extra or name not in [t['name'] for t in TAKES]:
            raise ValueError('FRAMING %r: unknown take or column %r' % (name, extra))

    # ---- takes table and the current take's row as channels ----
    takes = scene.create(td.tableDAT, 'takes')
    takes.clear()
    takes.appendRow(['name'] + COLS)
    for t in TAKES:
        row = dict(DEFAULT)
        row.update(t)
        row.update(W['FRAMING'].get(t['name'], {}))
        takes.appendRow([row['name']] + [row[col] for col in COLS])
    takes.nodeX, takes.nodeY = -700, 330
    phr = scene.create(td.tableDAT, 'phrases')
    phr.clear()
    for p in PHRASES:
        phr.appendRow([p])
    phr.nodeX, phr.nodeY = -700, 200

    # Describe mode: each take's own words for the text tile (count, then the words), and its caption
    nw = max(len(t.get('words', [])) for t in TAKES)
    dw = scene.create(td.tableDAT, 'dwords')
    dw.clear()
    dl = scene.create(td.tableDAT, 'dlabel')
    dl.clear()
    for t in TAKES:
        w = list(t.get('words', []))
        dw.appendRow([len(w)] + w + [''] * (nw - len(w)))
        dl.appendRow([t.get('label', ''), t.get('label_in', t.get('label', ''))])   # caption; caption when Input is set
    dw.nodeX, dw.nodeY = -700, 70
    dl.nodeX, dl.nodeY = -700, -60

    row = "int(%s['take']) %% %d + 1" % (S, NT)
    tk = _const(scene, 'tk', [(col, "float(op('takes')[%s, '%s'])" % (row, col)) for col in COLS],
                -550, 330)

    seedf = lambda m: "((%s * %r) %% 1.0)" % (SEED, m)
    sgn = "(1.0 if %s > 0.5 else -1.0)" % seedf(5.3)
    chans = [
        ('lines', "min(%d, max(8, round(%s * (0.85 + 0.3 * %s))))" % (MAXLINES, k('lines'), seedf(3.7))),
        # the tube warms up over the first third of a second of every shot
        ('arr', "1.0 - math.exp(-min(float(%s['age']), 20.0) * 8.0)" % S),
        ('en', EN),
        ('dy', "%s * (0.65 + 0.5 * %s) * (1.0 + 0.8 * min(float(%s['hit_low']), 1.2))" % (k('dy'), EN, H)),
        ('dz', "%s * (0.65 + 0.5 * %s) * (1.0 + 0.8 * min(float(%s['hit_low']), 1.2))" % (k('dz'), EN, H)),
        ('bend', "%s * 0.03 * min(float(%s['bass']), 1.7)" % (k('bend'), H)),
        ('tear', "%s * min(float(%s['hit_mid']), 1.2)" % (k('tear'), H)),
        ('brk', "%s * min(float(%s['hit_high']) * 1.3, 1.0)" % (k('brk'), H)),
        ('flash', "0.7 * min(float(%s['hit_low']), 1.2) + 0.25 * float(%s['pulse'])" % (H, H)),
        ('rx', "%s + %s * 4.0 * math.sin(float(%s['evolve']) * 0.63)" % (k('rx'), k('sway'), H)),
        # the raster is re-patched to a new angle at every section change
        ('ry', "%s * %s + %s * ((%s - 0.5) * 14.0 + 13.0 * math.sin(float(%s['evolve']) * 0.9 + %s * 6.28)"
               " + ((int(%s['section']) * 0.381) %% 1.0 - 0.5) * 26.0)"
               % (k('ry'), sgn, k('sway'), seedf(9.1), H, SEED, H)),
        ('rz', "%s + %s * 2.0 * math.sin(float(%s['bar_pos']) * 1.5708)" % (k('rz'), k('sway'), H)),
        ('dist', "%s - 0.05 * min(float(%s['hit_low']), 1.2)" % (k('dist'), H)),
        ('camx', "%s * %s" % (k('camx'), sgn)),
        # each time round the takes table the model steps on by two, so a take meets a new subject
        ('model', "(int(%s) + 2 * (int(%s['take']) // %d)) %% %d" % (k('model'), S, NT, len(MODELS))),
        ('fbhue', "%s * (0.3 + 1.7 * %s)" % (k('fbhue'), seedf(8.3))),
        ('myaw', "%s + %s * float(%s['evolve']) + (%s - 0.5) * %s + %s * math.sin(float(%s['evolve']) * 0.8)"
                 % (k('myaw'), k('mspin'), H, SEED, k('yawr'), k('mrock'), H)),
        ('phrase', "(int(%s * %d) + int(%s['section'])) %% %d" % (SEED, len(PHRASES), H, len(PHRASES))),
        ('oscf', "%s * (0.7 + 0.6 * %s)" % (k('oscf'), seedf(2.3))),
        ('fbgain', "%s * (0.95 + 0.07 * %s) * min(float(%s['age']) * 4.0, 1.0)" % (k('fb'), EN, S)),
        ('fbrot', "math.radians((360.0 / (3 + int(%s * 5.99)) if %s > 0.5 else %s + (%s - 0.5) * %s)"
                  " + 1.5 * math.sin(float(%s['evolve']) * 0.9) + 2.0 * min(float(%s['bass']), 1.7))"
                  % (seedf(4.1), k('fbsym'), k('fbrot'), seedf(4.1), k('fbrotj'), H, H)),
        ('fbzoom', "%s + (0.03 * min(float(%s['hit_low']), 1.2) if %s > 0 else 0.0)" % (k('fbzoom'), H, k('fb'))),
        # vertical hold: slips on the bar line in takes that ask for it, and in every take the
        # picture rolls once through as a new section starts
        ('roll', "%s * 0.5 * float(%s['bar_pulse']) ** 2"
                 " + (1.0 - min(float(%s['section_pos']) / 0.035, 1.0)) ** 2" % (k('roll'), H, H)),
        ('flag', "%s * (0.25 + min(float(%s['bass']), 1.7))" % (k('flag'), H)),
        ('field', "absTime.frame % 4096"),
        ('wall', "(2 + int(%s * 2.99)) if %s > 1.5 else 1" % (seedf(7.9), k('wall'))),
        ('tsx', "%s * float(%s['evolve']) + %s" % (k('tscroll'), H, seedf(6.7))),
        # Input: 1 when the COMP's Input names a TOP that exists and is not this scene's own output
        ('inp', INP),
        # Describe: which of the take's words are on the text tile (steps with the section, like the phrases)
        ('dn', "max(1, int(op('dwords')[int(%s['take']) %% %d, 0]))" % (S, NT)),
        ('dph', "(int(%s * 97) + int(%s['section'])) %% max(1, int(op('dwords')[int(%s['take']) %% %d, 0]))" % (SEED, H, S, NT)),
        ('sym', "3 + int(%s * 5.99)" % seedf(4.1)),
    ]
    ctl = _const(scene, 'ctl', chans, -550, 200)

    # ---- source picture: model render + text + oscillators, 640x360 ----
    for i, slug in enumerate(MODELS):
        geo = LIB['import_model'](scene, 'm%d' % i, slug)
        geo.par.render.expr = "int(%s) == %d" % (c('model'), i)
        geo.par.scale.expr = k('mscale')
        geo.par.ty.expr = k('mty')
        geo.par.ry.expr = c('myaw')
        geo.par.rx.expr = "8.0 * math.sin(float(%s['evolve']) * 0.5)" % H
        geo.nodeX, geo.nodeY = -550 + 130 * i, -330
        _fit_model(scene, geo, slug, TEAPOT_POSE[i % len(TEAPOT_POSE)])
        # load now: a model hidden at build time would otherwise hitch on its first shot
        geo.op('mesh').cook(force=True)
        geo.op('pick').cook(force=True)
        geo.op('tex').cook(force=True)
    key = scene.create(td.lightCOMP, 'key')
    key.par.tx, key.par.ty, key.par.tz = 2.2, 2.4, 2.6
    key.par.dimmer = 2.2
    key.nodeX, key.nodeY = -550, -460
    fill = scene.create(td.lightCOMP, 'fill')
    fill.par.tx, fill.par.ty, fill.par.tz = -3.0, -0.4, 1.2
    fill.par.dimmer = 0.45
    fill.nodeX, fill.nodeY = -420, -460
    scam = scene.create(td.cameraCOMP, 'scam')
    scam.par.fov = 30
    scam.par.tz = 3.3
    scam.nodeX, scam.nodeY = -290, -460
    srender = scene.create(td.renderTOP, 'srender')
    srender.par.camera = scam.name
    srender.par.geometry = 'm[0-9]'
    srender.par.lights = 'key fill'
    srender.par.outputresolution = 'custom'
    srender.par.resolutionw, srender.par.resolutionh = 640, 360
    srender.par.format = 'rgba16float'
    srender.par.bgcolorr, srender.par.bgcolorg, srender.par.bgcolorb, srender.par.bgcolora = 0, 0, 0, 0
    srender.nodeX, srender.nodeY = -250, -200

    text = scene.create(td.textTOP, 'text')
    # two phrases stacked, so the tile is full of letters wherever the raster looks
    trow = "int(%s['take']) %% %d" % (S, NT)
    text.par.text.expr = ("(op('dwords')[%s, 1 + int(%s)].val + chr(10)"
                          " + op('dwords')[%s, 1 + (int(%s) + max(1, int(%s) // 2)) %% int(%s)].val)"
                          " if parent().par.Describe else "
                          "(op('phrases')[int(%s), 0].val + chr(10) + op('phrases')[(int(%s) + 5) %% %d, 0].val)"
                          % (trow, c('dph'), trow, c('dph'), c('dn'), c('dn'),
                             c('phrase'), c('phrase'), len(PHRASES)))
    text.par.fontfile.expr = FONT
    text.par.fontsizex = 50
    text.par.fontautosize = 'fitiffat'
    text.par.alignx = 'center'
    text.par.aligny = 'center'
    text.par.outputresolution = 'custom'
    text.par.resolutionw, text.par.resolutionh = 384, 360   # narrow tile: src.frag repeats it
    text.par.bgalpha = 1
    text.nodeX, text.nodeY = -250, -60

    src = _glsl_top(scene, 'src', 'src.frag', -100, -60, 640, 360)
    src.par.inputextenduv = 'repeat'
    # Input: another scene's picture takes the place of the model render (and of the text and
    # most of the oscillators) as the thing the scan lines are deflected by
    insel = scene.create(td.selectTOP, 'insel')
    insel.par.top.expr = "%s if %s > 0.5 else 'wblack'" % (_IP, c('inp'))
    insel.par.outputresolution = 'custom'
    insel.par.resolutionw, insel.par.resolutionh = 640, 360
    insel.nodeX, insel.nodeY = -250, 80
    srcsw = scene.create(td.switchTOP, 'srcsw')
    srcsw.inputConnectors[0].connect(srender)
    srcsw.inputConnectors[1].connect(insel)
    srcsw.par.index.expr = "int(%s)" % c('inp')
    srcsw.nodeX, srcsw.nodeY = -170, -200
    src.inputConnectors[0].connect(srcsw)
    src.inputConnectors[1].connect(text)

    # spectrum waterfall: its own little feedback loop holding about three seconds of spectra
    wblack = scene.create(td.constantTOP, 'wblack')
    wblack.par.colorr, wblack.par.colorg, wblack.par.colorb, wblack.par.alpha = 0, 0, 0, 1
    wblack.par.outputresolution = 'custom'
    wblack.par.resolutionw, wblack.par.resolutionh = 256, 128
    wblack.par.format = 'rgba16float'
    wblack.nodeX, wblack.nodeY = -400, 500
    wfb = scene.create(td.feedbackTOP, 'wfb')
    wfb.par.format = 'rgba16float'
    wfb.inputConnectors[0].connect(wblack)
    wfb.nodeX, wfb.nodeY = -250, 500
    wfall = _glsl_top(scene, 'wfall', 'wfall.frag', -100, 500, 256, 128)
    wfall.inputConnectors[0].connect(scene.op('spectrum'))
    wfall.inputConnectors[1].connect(wfb)
    wfb.par.top = wfall.name
    # x stays 0: on a cut back to this scene the old ridges scroll away, which reads better than
    # the two seconds of flat field a cleared history gives (tried: ad5 take_4.png before this)
    _vecs(wfall, [('uW', (0.0, 0.0, 1.0, 0.0))])
    wfb.par.resetpulse.pulse()
    src.inputConnectors[2].connect(wfall)
    _vecs(src, [
        ('uMix', ("%s * %s" % (k('wm'), k('mgain')), k('wt'), k('wo'), "%s['evolve']" % H)),
        ('uTx', (k('tzoom'), c('tsx'), 0.0, c('oscf'))),
        ('uMix2', (k('ww'), k('wk'), 0.0, 0.0)),
        ('uAud', ("min(float(%s['bass']), 1.7)" % H, c('en'), SEED, "%s['beat_pos']" % H)),
        ('uIn', (c('inp'), k('igain'), k('iscroll'), 0.0)),
    ])
    sblur = scene.create(td.blurTOP, 'srcblur')
    sblur.par.size.expr = k('sblur')
    sblur.inputConnectors[0].connect(src)
    sblur.nodeX, sblur.nodeY = 50, -60

    # ---- the raster: one ribbon instanced once per scan line ----
    rv = _dat(scene, 'raster_vs', 'raster.vert', 200, -330)
    rp = _dat(scene, 'raster_px', 'raster.frag', 330, -330)
    mats = {}
    for name, solid in (('line_mat', 0.0), ('solid_mat', 1.0)):
        m = scene.create(td.glslMAT, name)
        m.par.vdat = rv.name
        m.par.pdat = rp.name
        m.seq.sampler.numBlocks = 3
        m.par.sampler0name = 'sSrc'
        m.par.sampler0top = sblur.path
        m.par.sampler0extendu = 'zero'
        m.par.sampler0extendv = 'zero'
        m.par.sampler1name = 'sSpec'
        m.par.sampler1top = scene.op('spectrum').path
        m.par.sampler1extendu = 'hold'
        m.par.sampler2name = 'sIn'
        m.par.sampler2top = insel.path
        m.par.sampler2extendu = 'zero'
        m.par.sampler2extendv = 'zero'
        m.par.cullface = 'neither'
        _vecs(m, [
            ('uRas', (c('lines'), float(SEG), k('width'), solid)),
            ('uDisp', (c('dy'), c('dz'), k('spec'), c('arr'))),
            ('uWob', (c('bend'), "%s * 0.04" % c('tear'), "%s['evolve']" % H, k('osc'))),
            ('uSrcXf', ("%s if %s > 0.5 else %s" % (k('iz'), c('inp'), k('szoom')),
                        "0.0 if %s > 0.5 else %s" % (c('inp'), k('sox')),
                        "0.0 if %s > 0.5 else %s" % (c('inp'), k('soy')), k('vert'))),
            ('uGeo', (1.7778, k('rh'), k('dist'), SEED)),
            ('uCol', (k('cr'), k('cg'), k('cb'), "%s * (0.85 + 0.3 * %s)" % (k('gain'), c('en')))),
            ('uCol2', (k('hr'), k('hg'), k('hb'), c('flash'))),
            ('uHue', (k('hspread'), "%s + %s + 0.05 * float(%s['evolve'])" % (k('hoff'), seedf(1.9), H), k('hamt'), 0.0)),
            ('uInt', (k('base'), k('lumi'), c('brk'), "%s['evolve']" % H)),
            ('uIn', ("%s * %s" % (k('icol'), c('inp')), 0.0, 0.0, 0.0)),
        ])
        mats[name] = m
    lm, sm = mats['line_mat'], mats['solid_mat']
    lm.par.blending = True
    lm.par.srcblend = 'one'
    lm.par.destblend = 'one'
    lm.par.depthwriting = False
    lm.nodeX, lm.nodeY = 200, -200
    sm.nodeX, sm.nodeY = 330, -200

    lines = scene.create(td.geometryCOMP, 'lines')
    for child in lines.children:
        child.destroy()
    g = lines.create(td.gridSOP, 'ribbon')
    g.par.rows, g.par.cols = 2, SEG + 1
    g.par.sizex, g.par.sizey = 1, 1
    g.render = True
    g.display = True
    lines.par.material = lm.path
    lines.par.instancing = True
    lines.par.instancecountmode = 'manual'
    lines.par.numinstances.expr = "int(%s)" % c('lines')
    lines.par.drawpriority = -10
    lines.nodeX, lines.nodeY = 200, -460

    solid = scene.create(td.geometryCOMP, 'solid')
    for child in solid.children:
        child.destroy()
    g = solid.create(td.gridSOP, 'sheet')
    g.par.rows, g.par.cols = 160, 256
    g.par.sizex, g.par.sizey = 1, 1
    g.render = True
    g.display = True
    solid.par.material = sm.path
    solid.par.render.expr = "%s > 0.5" % k('hidden')
    solid.par.drawpriority = 10
    solid.nodeX, solid.nodeY = 330, -460

    for geo in (lines, solid):
        geo.par.rx.expr = c('rx')
        geo.par.ry.expr = c('ry')
        geo.par.rz.expr = c('rz')

    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.fov = 50
    cam.par.near, cam.par.far = 0.05, 50
    cam.par.tx.expr = c('camx')
    cam.par.ty.expr = k('camy')
    cam.par.tz.expr = c('dist')
    cam.nodeX, cam.nodeY = 460, -460

    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.name
    render.par.geometry = 'lines solid'
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.bgcolorr, render.par.bgcolorg, render.par.bgcolorb, render.par.bgcolora = 0, 0, 0, 0
    render.nodeX, render.nodeY = 460, -60

    # ---- camera-at-monitor feedback loop ----
    black = scene.create(td.constantTOP, 'black')
    black.par.colorr, black.par.colorg, black.par.colorb, black.par.alpha = 0, 0, 0, 1
    black.par.outputresolution = 'custom'
    black.par.resolutionw, black.par.resolutionh = 1280, 720
    black.par.format = 'rgba16float'
    black.nodeX, black.nodeY = 460, 200
    fbk = scene.create(td.feedbackTOP, 'fbk')
    fbk.par.format = 'rgba16float'
    fbk.inputConnectors[0].connect(black)
    fbk.nodeX, fbk.nodeY = 600, 200
    loop = _glsl_top(scene, 'loop', 'loop.frag', 740, -60)
    loop.inputConnectors[0].connect(render)
    loop.inputConnectors[1].connect(fbk)
    loop.par.inputextenduv = 'mirror'
    fbk.par.top = loop.name
    _vecs(loop, [
        ('uFb', (c('fbgain'), c('fbrot'), c('fbzoom'), c('fbhue'))),
        ('uFb2', (k('fbcut'), 0.0, k('fbin'), k('fbmirror'))),
    ])
    fbk.par.resetpulse.pulse()

    # Describe mode caption: three lines of type on a dark strip, laid over the finished
    # picture after the output chain. (Tried first: keying it into the signal before the output
    # chain so it tore and glowed with the picture; at 22 px it was unreadable, d1 in NOTES.)
    # With Describe off the 'fin' switch passes the output chain straight through.
    label = scene.create(td.textTOP, 'label')
    label.par.text.expr = ("op('dlabel')[%s, int(%s)].val.format(n=int(%s), sym=int(%s), tiles=int(%s) ** 2,"
                           " src=('another picture' if %s > 0.5 else 'a 3D model'),"
                           " page=('another picture' if %s > 0.5 else 'a page of words'))"
                           " if parent().par.Describe else ''"
                           % (trow, c('inp'), c('lines'), c('sym'), c('wall'), c('inp'), c('inp')))
    label.par.fontfile.expr = FONT
    label.par.fontsizex = LABEL_PX
    label.par.fontautosize = 'fitiffat'    # a caption too wide for the frame shrinks instead of being cut off
    label.par.alignx = 'center'
    label.par.aligny = 'center'
    label.par.outputresolution = 'custom'
    label.par.resolutionw, label.par.resolutionh = 1280, LABEL_H
    label.par.bgalpha = 0
    label.nodeX, label.nodeY = 600, 330
    glow = scene.create(td.blurTOP, 'glow')
    glow.par.outputresolution = 'quarter'
    glow.par.size = 9
    glow.inputConnectors[0].connect(loop)
    glow.nodeX, glow.nodeY = 880, 100

    crt = _glsl_top(scene, 'crt', 'crt.frag', 1020, -60)
    crt.inputConnectors[0].connect(loop)
    crt.inputConnectors[1].connect(glow)
    crt.inputConnectors[2].connect(sblur)
    _vecs(crt, [
        ('uSync', (c('tear'), c('roll'), "%s['t']" % H, c('flag'))),
        ('uColz', (k('colz'), k('pal'), k('bands'), k('key'))),
        ('uLook', (k('neg'), k('interlace'), k('bleed'), k('snow'))),
        ('uAud', ("%s['pulse']" % H, "%s['hit_high']" % H, c('en'), c('field'))),
        ('uWall', (c('wall'), SEED, k('glow'), k('expo'))),
    ])
    title_b = _glsl_top(scene, 'title_b', 'titler.frag', 1020, 200)
    title_b.inputConnectors[0].connect(crt)
    title_b.inputConnectors[1].connect(label)
    _vecs(title_b, [('uT', (LABEL_H / 720.0, LABEL_Y / 720.0, 0.82, 1.0)), ('uTc', (0.93, 0.89, 0.8, 0.0))])
    fin = scene.create(td.switchTOP, 'fin')
    fin.inputConnectors[0].connect(crt)
    fin.inputConnectors[1].connect(title_b)
    fin.par.index.expr = "1 if parent().par.Describe else 0"
    fin.nodeX, fin.nodeY = 1110, 100
    scene.op('out1').inputConnectors[0].connect(fin)
    return scene.path
