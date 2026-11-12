# Builder for /project1/sc_spectral_terrain. Run inside TouchDesigner:
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open(project.folder + '/experiments/sc_spectral_terrain/build.py', encoding='utf-8').read(), g)
#   path = g['build']()
# Idempotent: destroys and rebuilds the whole scene.
import math
import td

SLUG = 'sc_spectral_terrain'
# Every file parameter is an expression on the scaffold's paths module (local/modules/paths), so
# the saved .tox holds no folder. With no assets both fonts are '' (TouchDesigner's default face).
FONT = "mod.paths.font('archivo')"        # the extruded words
CHICAGO = "mod.paths.font('chicago')"     # the caption

COLS, ROWS = 256, 192          # history texture: frequency across, time (frames) deep
WIDTH, DEPTH = 18.0, 44.0

H = "op('hub')"
C = "op('ctl')"
K = "op('tk')"
S = "op('shot')"
DESC_ON = "parent().par.Describe"
# 1 when Input names a TOP that exists and is not this scene's own output
IN_OK = ("(lambda o: 1.0 if (o is not None and o.isTOP and o.path != parent().path + '/out1') else 0.0)"
         "(op(parent().par.Input.eval()) if parent().par.Input.eval() else None)")

GREEN = (0.22, 1.0, 0.42)
AMBER = (1.0, 0.58, 0.10)
ICE = (0.50, 0.80, 1.0)
RED = (1.0, 0.17, 0.10)
WARM = (1.0, 0.95, 0.80)

# Everything the scene says that is content rather than technique. A pack may replace either name
# with its own scenes/sc_spectral_terrain/words.json (read once in build() through scene_words).
#   WORDS: the eight extruded phrases that can stand in the terrain: operator name (must start
#          'w_'), text, width in world units at wscale 1. A take's `hero` picks them by position.
#   LABELS: the small captions, by take name; the seed picks one.
CONTENT = {
    'WORDS': [
        ['w_signal', 'SIGNAL\nNOISE', 9.2],
        ['w_here', 'HERE.\nNOW.', 7.0],
        ['w_sound', 'NO\nPICTURE\nWITHOUT\nSOUND', 6.0],
        ['w_touch', 'DO NOT\nTOUCH', 7.0],
        ['w_frame', 'EVERY\nFRAME IS\nMADE NOW.', 7.0],
        ['w_loud', 'LOUD IS\nBRIGHT', 8.0],
        ['w_origin', 'ORIGIN:\nUNKNOWN', 7.5],
        ['w_nothing', 'NOTHING\nIS\nPRERENDERED.', 7.5],
    ],
    'LABELS': {
        'skim': ['SIGNAL LINK ..... OPEN', 'SOUND IN. PICTURE OUT.', 'CHANNEL 07 OPEN'],
        'map': ['PLATE 07   SURVEY OF A SOUND, FROM ABOVE.', 'SHEET 12-B   LOUD GROUND IS HIGH GROUND.',
                'CATALOGUE NO. 0047   TERRAIN OF UNKNOWN USE'],
        'chart': ['PLATE 07', 'FRAME. FRAME. FRAME.', 'FOUND, NOT MADE.', 'LISTEN WITH YOUR EYES.'],
        'planet': ['EXHIBIT 12-B: UNRECORDED.', 'OBJECT OF UNKNOWN USE. HANDLE WITH CARE.',
                   'PAST. PRESENT. LATER. STILL TURNING.'],
    },
}
NWORDS = 8      # the takes' hero / dhero numbers count on this many phrases before the Describe ones

# Describe mode (parent().par.Describe): the same monoliths, but the words say what the technique
# is. Built beside the content phrases at build time, so the toggle only changes which one renders.
# Indexed after CONTENT['WORDS']: 8, 9, 10 ...
DWORDS = [
    ('w_d_name', 'SPECTRUM\nTERRAIN', 9.2),
    ('w_d_loud', 'LOUDER IS\nHIGHER', 8.6),
    ('w_d_bass', 'BASS BUILDS\nWALLS', 9.0),
    ('w_d_height', 'HEIGHT IS\nLOUDNESS', 7.5),
    ('w_d_row', 'ONE ROW\nPER FRAME', 7.5),
    ('w_d_solid', 'SHADED\nSOLID', 6.5),
    ('w_d_now', 'NOW IS\nTHE CENTRE', 8.0),
    ('w_d_rings', 'KICKS MAKE\nRINGS', 8.0),
]

# Every key a take can set, with the value a take gets when it does not mention it.
# Bodies (shape): 0 plane, 1 tunnel, 2 planet, 3 disc, 4 flat stack.
# Looks: 0 ridge lines, 1 solid lit mountains in fog, 2 contour map.
# Sky: 0 horizon spectrogram sun, 1 flat bg colour, 2 dusk + small sun, 3 stars, 4 full-circle sun.
# Post: 0 CRT tube, 1 paper, 2 one-bit dither.
# "...s" keys are spreads multiplied by a seed value; "...g" keys apply only when the seed gate g is 1.
DEFAULTS = dict(
    shape=0, look=0, sky=0, post=0,
    xmap=0, xmaps=0,              # 1 = ridge (bass in the middle); xmaps 1 lets the seed choose
    floor=0.18, amp=3.0, lines=96.0, fog=2.3, fogd=0.05,
    radius=4.5, twist=0.0, twists=0.0, spin=0.0, contours=2.2,
    col=GREEN, acc=WARM, wcol=AMBER, bg=(0.0, 0.0, 0.0), labcol=(1.0, 1.0, 1.0),
    swap=0,                       # 1 lets the seed swap col and wcol
    camx=0.0, camxs=0.0, camxg=0.0, ridgex=0.0,
    camy=1.5, camys=0.0, camz=4.3, camzg=0.0,
    camrx=-4.0, camrxs=0.0, camry=0.0, camrys=0.0, ridgery=0.0,
    camrz=0.0, camrzg=0.0, fov=62.0, fovg=0.0,
    drift=1.0, roll=2.5, punch=0.45, arrz=1.5,
    sunaz=0.0, sunazs=0.0, sunel=0.22,
    comet=0, bloom=0.6, scan=0.28, barrel=0.16, expo=1.0, inverts=0,
    wscale=1.0, wx=0.0, wxs=0.0, wz=-12.5, wlift=0.7,
    lab=0.0, labx=40.0, laby=34.0, labsize=22.0,
    hero=(-1,),
    strip=0.100,                  # height of the caption strip (paper and one-bit finishes)
    # Describe mode. A "d..." key replaces its plain key while Describe is on; None = keep the plain one.
    dhero=None, dlabels=None, dwlift=None, dwscale=None, dlab=1.0, dlabx=40.0, dlaby=30.0, dlabsize=24.0, dlabcol=None,
    dstrip=0.125, halo=0.85,      # halo: dark outline behind the caption on the CRT finish
    # Input (parent().par.Input names a TOP): the picture is laid on the body and drawn by it.
    # Picture u = inua * x + inub * y + inuo, v = inva * x + invb * y + invo, where x is the grid's
    # frequency axis and y its time axis, both 0..1 (negative flips, above 1 tiles, a/b swapped turns).
    # inamp: relief from the picture's brightness. inmix / inpk: how much of the spectrum relief the
    # picture's dark / bright parts keep. ingain: brightness of the picture in the lines, rock or ink.
    inua=1.0, inub=0.0, inuo=0.0, inva=0.0, invb=1.0, invo=0.0,
    # inlines: ridge-line count while a picture is given (0 = the take's own count).
    inamp=0.35, inmix=0.35, inpk=1.0, ingain=1.2, inlines=0.0,
    # inplanar 1 (the disc): the picture lies flat on the ground, u = inua * world x + inuo,
    # v = invb * world z + invo, so it reads as one picture and the rings ripple through it.
    # ingate 1: while the seed gate g is on (the take's either/or variant) the g... values
    # replace the six above, so a picture stays upright when the camera turns on its side.
    inplanar=0.0, ingate=0.0, gua=0.0, gub=0.0, guo=0.0, gva=0.0, gvb=0.0, gvo=0.0,
)
DESC = dict(lab='dlab', labx='dlabx', laby='dlaby', labsize='dlabsize', labcol='dlabcol', strip='dstrip',
            wlift='dwlift', wscale='dwscale')     # the Describe monolith stands higher so both lines read
SKIP = ('hero', 'dhero', 'dlabels') + tuple(DESC.values())

# One line per take: what you see. Selected by op('shot')['take'] % len(TAKES).
TAKES = [
    # 0 VALLEY: the original. A phrase monolith in a line-drawn valley, spectrogram sun, green/amber.
    dict(name='valley', hero=(0, 1, 2), swap=1, comet=1, dhero=(8, 9, 10), dwlift=2.4,
         invb=1.67, inamp=0.22, inmix=0.3, inpk=0.6,
         dlabels=('EVERY FRAME THE SOUND SPECTRUM BECOMES THE FRONT ROW OF A HEIGHT MAP.\n'
                  'OLDER ROWS SLIDE AWAY. BASS BUILDS THE WALLS, A KICK IS A WHITE RIDGE.',),
         camxs=3.3, camys=2.7, camrxs=-8.0, camrys=13.0),
    # 1 SKIM: no word. Head-height forward flight in ice blue; the live edge is the horizon and the
    #   rows rush at the lens. The seed picks valley or central ridge and the side.
    dict(name='skim', col=ICE, acc=(1.0, 1.0, 1.0), wcol=ICE, xmaps=1, floor=0.30, amp=3.6,
         lines=128.0, fog=0.35, camy=1.5, camys=0.7, camz=-37.5, camrx=2.0, camry=180.0,
         camxs=1.2, ridgex=5.4, ridgery=-13.0, fov=100.0, drift=0.5, roll=6.0, punch=-0.8,
         arrz=-3.0, comet=1, bloom=0.7,
         lab=0.8, labx=44.0, laby=660.0, labsize=18.0, labcol=ICE,
         dlaby=636.0, inua=-1.0, inuo=1.0, invb=-1.67, invo=1.67, inamp=0.06, inpk=0.6,
         dlabels=('256 BY 192 HEIGHT MAP OF THE SPECTRUM, ONE NEW ROW EVERY FRAME.\n'
                  'THE HORIZON IS NOW. THE ROWS FLYING PAST ARE THE LAST FEW SECONDS.',
                  'EACH LINE RUSHING AT THE LENS IS ONE FRAME OF SOUND, NEWEST AT THE\n'
                  'HORIZON. THE RIBBON OVERHEAD HANGS AT THE PITCH OF THE VOICE.')),
    # 2 TUNNEL: the terrain rolled into a bore, red phosphor, camera inside, rolling with the bar.
    dict(name='tunnel', shape=1, sky=4, col=RED, acc=(1.0, 0.9, 0.6), radius=4.6, twists=3.0,
         spin=0.5, floor=0.45, amp=1.9, fog=2.4, camx=0.0, camxs=1.3, camy=-1.1, camz=-0.6,
         camrx=0.0, fov=104.0, drift=0.5, roll=16.0, punch=1.4, arrz=4.0, bloom=0.8,
         dlabcol=(1.0, 0.9, 0.6), inua=2.0, invb=3.0, inamp=0.1, inmix=0.3, inpk=0.5,
         dlabels=('THE SAME HEIGHT MAP ROLLED INTO A TUBE: FREQUENCY RUNS ROUND THE WALL,\n'
                  'TIME RUNS DOWN THE BORE. KICKS ARE WHITE RINGS. THE BAR ROLLS THE CAMERA.',)),
    # 3 MAP: daylight. Straight down on cream paper, ink contours, blue height tint, red kick stamps.
    dict(name='map', look=2, sky=1, post=1, floor=0.55, amp=3.0, bg=(0.93, 0.89, 0.78),
         col=(0.10, 0.17, 0.23), acc=(0.36, 0.52, 0.62), camy=30.0, camz=-17.0, camzg=6.0,
         camrx=-90.0, camry=90.0, fov=59.0, fovg=-25.0, drift=0.25, roll=0.0, punch=0.0,
         arrz=0.0, sunaz=2.3, sunel=0.8, bloom=0.0, contours=1.5,
         lab=1.0, labx=40.0, laby=30.0, labsize=24.0, labcol=(0.10, 0.17, 0.23),
         dlaby=16.0, inua=0.0, inub=1.37, inva=-1.0, invb=0.0, invo=1.0, inamp=0.5, inmix=0.2, inpk=0.3,
         dlabels=('CONTOUR MAP OF SOUND FROM STRAIGHT ABOVE: LINES JOIN EQUAL LOUDNESS,\n'
                  'BLUER IS LOUDER. RED HATCHED BANDS ARE KICK DRUMS CROSSING THE SHEET.',
                  'THE SPECTRUM HISTORY PRINTED AS A SURVEY SHEET: TIME ALONG ONE AXIS,\n'
                  'FREQUENCY ALONG THE OTHER. A SNARE KNOCKS THE INK OUT OF REGISTER.')),
    # 4 DUSK: solid lit mountains in pink fog under a small sun; a phrase stands small and far off.
    dict(name='dusk', look=1, sky=2, floor=0.22, amp=3.5, fogd=0.032,
         bg=(0.80, 0.40, 0.40), col=(1.0, 0.70, 0.40), acc=(1.0, 0.80, 0.30),
         wcol=(1.0, 0.86, 0.55), hero=(4, 6, 7), wscale=0.8, wxs=2.2, wz=-19.0, wlift=2.1,
         camy=2.6, camys=2.2, camz=4.6, camrx=-4.0, camrxs=-5.0, camxs=2.0, camrys=6.0,
         fov=58.0, drift=0.8, sunazs=0.42, sunel=0.20, bloom=0.10, scan=0.06, barrel=0.05,
         dhero=(11, 12, 13), dwscale=1.0, dwlift=2.6, invb=1.67, inamp=0.3, ingain=1.6,
         dlabels=('THE SAME SPECTRUM HEIGHT MAP SHADED AS SOLID ROCK: ONE SUN, DISTANCE FOG.\n'
                  'THE THIN STRATA ARE ITS ROWS. A KICK DRUM IS A GLOWING BAND ROLLING AWAY.',)),
    # 5 CHART: no perspective. The rows stacked flat like a seismograph, one-bit black and white,
    #   Chicago caption. The seed inverts it and turns it on its side.
    dict(name='chart', shape=4, sky=1, post=2, xmap=1, floor=0.10, amp=1.7, lines=48.0, fog=0.0,
         radius=10.5, col=(1.0, 1.0, 1.0), acc=(1.0, 1.0, 1.0), camx=0.0, camy=0.5, camz=40.0,
         camrx=0.0, fov=28.0, camrzg=90.0, fovg=-9.0, drift=0.0, roll=0.0, punch=2.0, arrz=0.0,
         bloom=0.5, expo=1.3, inverts=1,
         lab=1.0, labx=36.0, laby=28.0, labsize=24.0,
         dlaby=14.0, inamp=0.12, inmix=0.18, inpk=0.1, ingain=1.6, inlines=96.0,
         ingate=1, gub=1.0, gva=-2.38, gvo=1.69,      # turned 90 degrees and cropped: turn the picture too
         dlabels=('ONE TRACE PER FRAME OF SOUND, STACKED FLAT WITH NO PERSPECTIVE.\n'
                  'BASS IS IN THE MIDDLE. EACH TRACE HIDES THE ONES BEHIND IT.',
                  'THE SPECTRUM HISTORY AS A SEISMOGRAPH IN PURE BLACK AND WHITE:\n'
                  'ORDERED DITHER AT 640 BY 360. THE BEAT THICKENS THE DOTS.')),
    # 6 PLANET: the terrain wrapped on a globe turning in a star field, amber. Whole, or close limb.
    dict(name='planet', shape=2, sky=3, col=(1.0, 0.74, 0.36), acc=(1.0, 1.0, 1.0), radius=5.0,
         spin=0.35, floor=0.40, amp=1.25, fog=0.0, camx=0.0, camxs=3.0, camxg=3.5, camy=3.5,
         camz=23.0, camzg=-11.5, camrx=-8.0, camrys=6.0, fov=50.0, drift=0.4, roll=4.0,
         punch=0.8, arrz=6.0, bloom=0.7,
         lab=0.7, labx=44.0, laby=40.0, labsize=18.0, labcol=(1.0, 0.74, 0.36),
         dlabcol=(1.0, 0.86, 0.56), inua=-2.0, invb=-1.0, invo=1.0, inamp=0.25, inmix=0.2, inpk=0.35,
         dlabels=('THE HEIGHT MAP WRAPPED ON A SPHERE: FREQUENCY IS LONGITUDE, NEW SOUND\n'
                  'ENTERS AT THE NORTH POLE AND TRAVELS SOUTH. A KICK SWELLS ONE LATITUDE.',
                  'SPECTRUM PLANET: A 256 BY 192 GRID PUSHED OUT BY THE LAST SECONDS OF\n'
                  'SOUND. IT TURNS FASTER WHEN THE MUSIC IS LOUD.')),
    # 7 POND: a spiral disc of ripples spreading from a red phrase at its centre, cream on black.
    dict(name='pond', shape=3, sky=3, col=(0.93, 0.85, 0.66), acc=RED, wcol=(0.95, 0.16, 0.10),
         hero=(3, 5), wscale=0.8, wz=0.0, wlift=0.9, radius=15.0, twist=1.6, spin=0.22,
         floor=0.5, amp=1.8, lines=64.0, fog=1.3, camy=8.0, camys=7.0, camz=17.0,
         camrx=-23.0, camrxs=-17.0, camxs=2.5, camrys=8.0, fov=62.0, drift=0.6, roll=3.0,
         punch=0.9, arrz=5.0, bloom=0.65, dhero=(14, 15), dwscale=0.95, dwlift=2.6,
         inplanar=1, inua=0.0294, inuo=0.5, invb=-0.0385, invo=0.5, inamp=0.35, inmix=0.15, inpk=0.25,
         dlabels=('THE HEIGHT MAP AS A SPIRAL DISC: FREQUENCY IS THE ANGLE, NEW SOUND STARTS\n'
                  'AT THE CENTRE AND SPREADS OUT. EACH KICK DRUM LEAVES THE MIDDLE AS A RING.',)),
]
N = len(TAKES)


def _take_rows():
    """Flatten TAKES into {key: (one number per take, the same for Describe mode or None)};
    colours become three keys."""
    rows = {}
    for key, dv in DEFAULTS.items():
        if key in SKIP:
            continue
        vals = [t.get(key, dv) for t in TAKES]
        dvals = None
        if key in DESC:
            dk = DESC[key]
            dvals = [v if t.get(dk, DEFAULTS[dk]) is None else t.get(dk, DEFAULTS[dk])
                     for t, v in zip(TAKES, vals)]
        if isinstance(dv, tuple):
            for i, comp in enumerate('rgb'):
                rows[key + comp] = (tuple(float(v[i]) for v in vals),
                                    tuple(float(v[i]) for v in dvals) if dvals else None)
        else:
            rows[key] = (tuple(float(v) for v in vals), tuple(float(v) for v in dvals) if dvals else None)
    return rows


def _tk_expr(vals, dvals, take):
    if dvals is None or dvals == vals:
        return '%r[%s]' % (vals, take)
    return '(%r if %s else %r)[%s]' % (dvals, DESC_ON, vals, take)


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
    g.par.pixeldat = d.name
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    g.nodeX, g.nodeY = x, y
    return g


def _glsl_mat(scene, name, vert, frag, x, y):
    m = scene.create(td.glslMAT, name)
    m.par.vdat = vert.name
    m.par.pdat = frag.name
    m.nodeX, m.nodeY = x, y
    return m


def k(name):
    return "%s['%s']" % (K, name)


def gk(name, gname):
    """The take's value, or its gate-variant value while ingate and the seed gate are both on."""
    return "(%s if (%s > 0.5 and %s > 0.5) else %s)" % (k(gname), k('ingate'), k('g'), k(name))


def c(name):
    return "%s['%s']" % (C, name)


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 1500, -700)
    W = LIB['scene_words'](scene, CONTENT)
    WORDS = [(str(n), str(t), float(w)) for n, t, w in W['WORDS']]
    assert len(WORDS) == NWORDS and all(n.startswith('w_') for n, _, _ in WORDS), WORDS
    labels = {str(name): tuple(str(x) for x in rows) for name, rows in W['LABELS'].items()}
    # The scaffold's 512x1 spectex is the first 20% of a log-frequency spectrum: a smooth,
    # nearly empty ramp. Read the hub's full 24000x1 spectrum instead (see NOTES.md).
    scene.op('spectrum').par.top = '/project1/sw_hub/specraw'

    # ---- tk: the current take's row of TAKES, plus the seed split into independent values ----
    take = "int(%s['take']) %% %d" % (S, N)
    tk = scene.create(td.constantCHOP, 'tk')
    tk.nodeX, tk.nodeY = -250, 330
    rows = _take_rows()
    tchans = [(key, _tk_expr(vals, dvals, take)) for key, (vals, dvals) in rows.items()]
    seed = "float(%s['seed'])" % S
    pick = "(lambda L, s: L[min(int(s * len(L)), len(L) - 1)])"
    tchans += [
        ('s1', seed),
        ('s2', "(%s * 7.31 + 0.13) %% 1.0" % seed),
        ('s3', "(%s * 13.77 + 0.61) %% 1.0" % seed),
        ('g', "1.0 if (%s * 13.77 + 0.61) %% 1.0 > 0.6 else 0.0" % seed),      # gate for the ...g keys
        ('hero', "%s((%r if %s else %r)[%s], %s)" % (
            pick, tuple(t.get('dhero') or t.get('hero', (-1,)) for t in TAKES), DESC_ON,
            tuple(t.get('hero', (-1,)) for t in TAKES), take, seed)),
        ('desc', "1.0 if %s else 0.0" % DESC_ON),
        ('inon', IN_OK),
    ]
    tk.seq.const.numBlocks = len(tchans)
    for i, (n, e) in enumerate(tchans):
        tk.par['const%dname' % i] = n
        tk.par['const%dvalue' % i].expr = e

    # ---- ctl: everything the feed and the shot are turned into, in one place ----
    ctl = scene.create(td.constantCHOP, 'ctl')
    ctl.nodeX, ctl.nodeY = -100, 330
    sw = "(%s * (1.0 if %s > 0.5 else 0.0))" % (k('swap'), k('s1'))
    a01 = "min(float(%s['age']) / 0.5, 1.0)" % S
    chans = []
    for comp in 'rgb':
        chans.append(('t' + comp, "%s + (%s - %s) * %s" % (k('col' + comp), k('wcol' + comp), k('col' + comp), sw)))
        chans.append(('w' + comp, "%s + (%s - %s) * %s" % (k('wcol' + comp), k('col' + comp), k('wcol' + comp), sw)))
    # a Constant CHOP expression that reads its own channels is a cook loop: repeat the expression
    xmap_e = "max(%s, %s * (1.0 if %s > 0.5 else 0.0))" % (k('xmap'), k('xmaps'), k('s3'))
    chans += [
        ('xmap', xmap_e),
        # vocal pitch as 0..1 (MIDI 40..64, the range this track's analysis holds), 0 when not singing
        ('pitchn', "(min(max((%s['pitch'] - 40.0) / 24.0, 0.03), 1.0) if (%s['pitch'] > 0 and %s['pitch_conf'] > 0.2) else 0.0)" % (H, H, H)),
        ('cometx', "math.sin(%s['beat_pos'] * 1.5708) * 0.42 + math.sin(%s['evolve'] * 0.7) * 0.4" % (H, H)),
        ('flash', "min(float(%s['hit_low']) * 1.9, 1.6)" % H),
        # the arrival, from the shot's age: arr eases 0 -> 1 with a 10% overshoot in half a second,
        # spring lifts the terrain from 35% with a bigger overshoot, sweep is a bright row that
        # crosses the whole history, rise brings the word out of the ground
        ('arr', "(lambda a: 1.0 + 2.70158 * (a - 1.0) ** 3 + 1.70158 * (a - 1.0) ** 2)(%s)" % a01),
        ('spring', "0.35 + 0.65 * (lambda a: 1.0 + 4.0 * (a - 1.0) ** 3 + 3.0 * (a - 1.0) ** 2)(%s)" % a01),
        ('sweep', "min(float(%s['age']) * 2.6, 2.0)" % S),
        ('rise', "(lambda u: u * u * (3.0 - 2.0 * u))(min(float(%s['age']) / 0.4, 1.0))" % S),
        # bass note -> hue of the horizon (pitch class round the colour wheel)
        ('bhue', "(%s['bass_pitch'] %% 12) / 12.0" % H),
        ('bon', "1.0 if %s['bass_pitch'] > 0 else 0.0" % H),
        ('cx', "%s + %s * (2.0 * %s - 1.0) + %s * %s + %s * %s"
               % (k('camx'), k('camxs'), k('s2'), k('ridgex'), xmap_e, k('camxg'), k('g'))),
        ('wx', "%s + %s * (2.0 * %s - 1.0)" % (k('wx'), k('wxs'), k('s3'))),
        ('sunaz', "%s + %s * (2.0 * %s - 1.0)" % (k('sunaz'), k('sunazs'), k('s2'))),
        ('spin', "%s * float(%s['evolve'])" % (k('spin'), H)),
        ('twist', "%s + %s * (2.0 * %s - 1.0)" % (k('twist'), k('twists'), k('s2'))),
    ]
    ctl.seq.const.numBlocks = len(chans)
    for i, (n, e) in enumerate(chans):
        ctl.par['const%dname' % i] = n
        ctl.par['const%dvalue' % i].expr = e

    # ---- note history: 2 x ROWS. Column 0 is the voice, column 1 the bass. ----
    # The pitch channels are only non-zero about 7% (voice) and 10% (bass) of the time, in
    # bursts of ~50 ms, so the shader holds the last note and stores a decaying "spark".
    ninit = scene.create(td.constantTOP, 'notes_init')
    ninit.par.colorr, ninit.par.colorg, ninit.par.colorb, ninit.par.alpha = 0.5, 0, 0, 0
    ninit.par.outputresolution = 'custom'
    ninit.par.resolutionw, ninit.par.resolutionh = 2, ROWS
    ninit.par.format = 'rgba16float'
    ninit.nodeX, ninit.nodeY = -400, -520
    nfb = scene.create(td.feedbackTOP, 'notes_fb')
    nfb.par.format = 'rgba16float'
    nfb.inputConnectors[0].connect(ninit)
    nfb.nodeX, nfb.nodeY = -250, -520
    notes = _glsl_top(scene, 'notes', 'notes.frag', -100, -520, 2, ROWS)
    notes.par.inputfiltertype = 'nearest'
    notes.inputConnectors[0].connect(nfb)
    nfb.par.top = notes.name
    _vecs(notes, [
        ('uLive', (c('pitchn'), c('cometx'), "min(float(%s['vocals']), 1.5)" % H, 0.0)),
        ('uBass', (c('bhue'), c('bon'), "min(float(%s['bass']), 1.5)" % H, 0.0)),
    ])
    nfb.par.resetpulse.pulse()

    # ---- waterfall history ----
    init = scene.create(td.constantTOP, 'wf_init')
    init.par.colorr, init.par.colorg, init.par.colorb, init.par.alpha = 0, 0, 0, 0
    init.par.outputresolution = 'custom'
    init.par.resolutionw, init.par.resolutionh = COLS, ROWS
    init.par.format = 'rgba16float'
    init.nodeX, init.nodeY = -400, -260
    fb = scene.create(td.feedbackTOP, 'wf_fb')
    fb.par.format = 'rgba16float'
    fb.inputConnectors[0].connect(init)
    fb.nodeX, fb.nodeY = -250, -260
    wf = _glsl_top(scene, 'wf', 'waterfall.frag', -100, -260, COLS, ROWS)
    wf.par.inputfiltertype = 'nearest'
    wf.inputConnectors[0].connect(fb)
    wf.inputConnectors[1].connect(scene.op('spectrum'))
    fb.par.top = wf.name
    _vecs(wf, [
        ('uLive', (0.0, 0.0, c('flash'), 4.0)),
        ('uRes', (1.0 / ROWS, 0.6, 0.6, 0.0)),
    ])
    fb.par.resetpulse.pulse()

    # ---- Input: another scene's picture, laid on the body. Blank (or a bad path) = in_none. ----
    none = scene.create(td.constantTOP, 'in_none')
    none.par.colorr, none.par.colorg, none.par.colorb, none.par.alpha = 0, 0, 0, 1
    none.par.outputresolution = 'custom'
    none.par.resolutionw, none.par.resolutionh = 16, 16
    none.nodeX, none.nodeY = -400, -780
    pic = scene.create(td.selectTOP, 'in_pic')
    pic.par.top.expr = "parent().par.Input.eval() if %s > 0.5 else 'in_none'" % k('inon')
    pic.par.outputresolution = 'custom'
    pic.par.resolutionw, pic.par.resolutionh = 640, 360
    pic.nodeX, pic.nodeY = -250, -780
    soft = scene.create(td.blurTOP, 'in_soft')        # the relief is read from a softened copy
    soft.inputConnectors[0].connect(pic)
    soft.par.outputresolution = 'custom'
    soft.par.resolutionw, soft.par.resolutionh = 320, 180
    soft.par.size = 3
    soft.nodeX, soft.nodeY = -100, -780

    # ---- terrain ----
    tv = _dat(scene, 'terrain_vs', 'terrain.vert', 100, -390)
    tf = _dat(scene, 'terrain_px', 'terrain.frag', 250, -390)
    tmat = _glsl_mat(scene, 'terrain_mat', tv, tf, 250, -260)
    tmat.par.sampler0name = 'sWF'
    tmat.par.sampler0top = wf.path
    tmat.par.sampler0extendu = 'hold'
    tmat.par.sampler0extendv = 'hold'
    tmat.par.cullface = 'neither'
    tmat.seq.sampler.numBlocks = 3
    for i, (sn, st) in enumerate((('sIn', pic), ('sInH', soft))):
        tmat.par['sampler%dname' % (i + 1)] = sn
        tmat.par['sampler%dtop' % (i + 1)] = st.path
        tmat.par['sampler%dextendu' % (i + 1)] = 'repeat'
        tmat.par['sampler%dextendv' % (i + 1)] = 'repeat'

    # ---- words: every phrase stays loaded; the take and seed choose which one renders ----
    words = []
    for i, (name, text, target_w) in enumerate(WORDS + DWORDS):
        geo = scene.create(td.geometryCOMP, name)
        for child in geo.children:
            child.destroy()
        tp = geo.create(td.textPOP, 'text')
        tp.par.text = text
        tp.par.fontfile.expr = FONT
        tp.par.alignx = 'center'
        tp.par.aligny = 'bottom'
        tp.par.extrude = True
        tp.par.linespacing = -0.22
        tp.render = True
        tp.display = True
        geo.nodeX, geo.nodeY = 450 + 150 * (i % 8), -520 - 300 * (i // 8)
        words.append((geo, tp, target_w))

    # size each word from its measured bounds so the layout survives font changes
    depths, halfw, heights = [], [], []
    for i, (geo, tp, target_w) in enumerate(words):
        tp.par.extrudedepth = 0.22
        tp.cook(force=True)
        try:
            b = tp.computeBounds()
            bw = max(float(b.size.x), 1e-3)
            # a deep slab: the extrusion is 11% of the word's width
            tp.par.extrudedepth = bw * 0.11
            tp.cook(force=True)
            b = tp.computeBounds()
            bw = max(float(b.size.x), 1e-3)
            bh = float(b.size.y)
            by = float(b.min.y)
        except Exception:
            bw, bh, by = 1.0, 0.3, 0.0
        depths.append(float(tp.par.extrudedepth))
        s = target_w / bw
        geo.par.tx.expr = c('wx')
        geo.par.tz.expr = k('wz')
        # punch on the kick; sunk below the ground until the shot's first 0.4 s brings it up
        geo.par.scale.expr = "%r * %s * (1.0 + 0.05 * float(%s))" % (s, k('wscale'), c('flash'))
        geo.par.ty.expr = "%r * %s + %s - (%r * %s + 1.0) * (1.0 - float(%s))" % (
            -by * s, k('wscale'), k('wlift'), bh * s, k('wscale'), c('rise'))
        # turn the face a little toward the camera
        geo.par.ry.expr = "max(-25.0, min(25.0, (float(%s) - float(%s)) * 4.0))" % (c('cx'), c('wx'))
        geo.par.render.expr = "int(%s) == %d" % (k('hero'), i)
        halfw.append(target_w * 0.5 + 0.1)
        heights.append(bh)

    wv = _dat(scene, 'word_vs', 'word.vert', 450, -260)
    wp = _dat(scene, 'word_px', 'word.frag', 600, -260)
    for i, (geo, tp, target_w) in enumerate(words):
        wm = _glsl_mat(scene, 'word_mat%d' % i, wv, wp, 450 + 150 * (i % 8), -390 - 300 * (i // 8))
        wm.par.cullface = 'neither'
        _vecs(wm, [
            ('uCol', (c('wr'), c('wg'), c('wb'), c('flash'))),
            ('uFx', ("%s['beat_pos']" % H, "%s['energy']" % H, depths[i], heights[i])),
        ])
        geo.par.material = wm.path

    hw = "(%r[int(%s)] * float(%s) if %s >= 0 else 1.2)" % (tuple(halfw), k('hero'), k('wscale'), k('hero'))
    _vecs(tmat, [
        ('uDim', (WIDTH, DEPTH, k('amp'),
                  "(%s if (%s > 0.5 and %s > 0) else %s)" % (k('inlines'), k('inon'), k('inlines'), k('lines')))),
        # the word's footprint (parked far away when no word stands), w: valley floor height factor
        ('uMono0', (c('wx'), "%s if %s >= 0 else 500.0" % (k('wz'), k('hero')), hw, k('floor'))),
        ('uShape', (k('shape'), k('radius'), c('twist'), c('spin'))),
        ('uMap', (c('xmap'), c('arr'), c('spring'), 0.0)),
        ('uCol', (c('tr'), c('tg'), c('tb'), "1.1 + 0.8 * float(%s['energy'])" % H)),
        ('uCol2', (k('accr'), k('accg'), k('accb'), "%s['pulse']" % H)),
        ('uFx', (k('fog'), "%s['energy']" % H, "%s['beat_pos']" % H, "%s['hit_high']" % H)),
        ('uLook', (k('look'), k('contours'), k('shape'), c('sweep'))),
        ('uBg', (k('bgr'), k('bgg'), k('bgb'), k('fogd'))),
        ('uSun', ("math.sin(%s)" % c('sunaz'), k('sunel'), "-math.cos(%s)" % c('sunaz'), 0.0)),
        ('uCamP', ("op('cam').par.tx", "op('cam').par.ty", "op('cam').par.tz", 0.0)),
        ('uIn', (k('inon'), k('inamp'), k('inmix'), k('ingain'))),
        ('uInM', (gk('inua', 'gua'), gk('inub', 'gub'), gk('inva', 'gva'), gk('invb', 'gvb'))),
        ('uInO', (gk('inuo', 'guo'), gk('invo', 'gvo'), k('inpk'), k('inplanar'))),
    ])

    terrain = scene.create(td.geometryCOMP, 'terrain')
    for child in terrain.children:
        child.destroy()
    grid = terrain.create(td.gridSOP, 'grid')
    grid.par.orient = 'zx'
    grid.par.sizex, grid.par.sizey = 1, 1
    grid.par.rows, grid.par.cols = ROWS, COLS
    grid.render = True
    grid.display = True
    terrain.par.material = tmat.path
    terrain.nodeX, terrain.nodeY = 250, -520

    # ---- vocal pitch curtain ----
    cv = _dat(scene, 'comet_vs', 'comet.vert', 100, -650)
    cf = _dat(scene, 'comet_px', 'comet.frag', 250, -650)
    cmat = _glsl_mat(scene, 'comet_mat', cv, cf, 250, -780)
    cmat.par.sampler0name = 'sNotes'
    cmat.par.sampler0top = notes.path
    cmat.par.sampler0filter = 'nearest'
    cmat.par.cullface = 'neither'
    cmat.par.blending = True
    cmat.par.srcblend = 'one'
    cmat.par.destblend = 'one'
    cmat.par.depthwriting = False
    _vecs(cmat, [
        ('uDim', (WIDTH, DEPTH, float(ROWS), 0.45)),
        ('uRib', (1.5, 1.9, 4.2, 0.0)),
        ('uCol', (c('wr'), c('wg'), c('wb'), 1.0)),
        ('uFx', ("%s * 0.8" % k('fog'), "%s['beat_pos']" % H, 0.0, 0.0)),
    ])
    comet = scene.create(td.geometryCOMP, 'comet')
    for child in comet.children:
        child.destroy()
    strip = comet.create(td.gridSOP, 'strip')
    strip.par.orient = 'zx'
    strip.par.sizex, strip.par.sizey = 1, 1
    strip.par.rows, strip.par.cols = ROWS, 2
    strip.render = True
    strip.display = True
    comet.par.material = cmat.path
    comet.par.drawpriority = -10
    comet.par.render.expr = "%s > 0.5" % k('comet')
    comet.nodeX, comet.nodeY = 100, -520

    # ---- camera and render ----
    d = k('drift')
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.fov.expr = "%s + %s * %s" % (k('fov'), k('fovg'), k('g'))
    cam.par.near, cam.par.far = 0.1, 200
    cam.par.tx.expr = "%s + %s * 1.1 * math.sin(%s['evolve'] * 0.21)" % (c('cx'), d, H)
    cam.par.ty.expr = "%s + %s * %s + %s * (0.25 * math.sin(%s['evolve'] * 0.33) + 0.12 * float(%s['pulse']))" % (
        k('camy'), k('camys'), k('s3'), d, H, H)
    cam.par.tz.expr = "%s + %s * %s - %s * float(%s) + %s * (1.0 - float(%s))" % (
        k('camz'), k('camzg'), k('g'), k('punch'), c('flash'), k('arrz'), c('arr'))
    cam.par.rx.expr = "%s + %s * %s + %s * 1.2 * math.sin(%s['evolve'] * 0.27)" % (
        k('camrx'), k('camrxs'), k('s3'), d, H)
    cam.par.ry.expr = "%s + %s * (2.0 * %s - 1.0) + %s * %s + %s * 4.0 * math.sin(%s['evolve'] * 0.17)" % (
        k('camry'), k('camrys'), k('s2'), k('ridgery'), c('xmap'), d, H)
    cam.par.rz.expr = "%s + %s * %s + %s * math.sin(%s['bar_pos'] * math.pi * 0.5)" % (
        k('camrz'), k('camrzg'), k('g'), k('roll'), H)
    cam.nodeX, cam.nodeY = 700, -130

    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.name
    render.par.geometry = 'terrain comet w_*'
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.bgcolorr, render.par.bgcolorg, render.par.bgcolorb, render.par.bgcolora = 0, 0, 0, 0
    render.nodeX, render.nodeY = 700, 0

    # ---- sky ----
    sky = _glsl_top(scene, 'sky', 'sky.frag', 550, 150)
    sky.inputConnectors[0].connect(notes)
    sky.inputConnectors[1].connect(wf)
    _vecs(sky, [
        ('uCam', ("op('cam').par.rx", "op('cam').par.ry", "op('cam').par.rz",
                  "math.tan(math.radians(op('cam').par.fov) * 0.5) * 720.0 / 1280.0")),
        ('uFx', ("%s['bar_pulse']" % H, "%s['hit_high']" % H, "%s['evolve']" % H, "%s['energy']" % H)),
        ('uCol', (c('tr'), c('tg'), c('tb'), 1.0)),
        ('uHit', (c('flash'), "%s['hit_mid']" % H, 0.0, 0.0)),
        ('uSkyM', (k('sky'), c('sunaz'), 0.0, 0.0)),
        ('uBg', (k('bgr'), k('bgg'), k('bgb'), 0.0)),
    ])
    # hold-out: the render's alpha is 1 on the terrain surface, 0 on empty sky
    over = scene.create(td.overTOP, 'over')
    over.par.format = 'rgba16float'
    over.inputConnectors[0].connect(render)
    over.inputConnectors[1].connect(sky)
    over.nodeX, over.nodeY = 850, 0

    bloom = scene.create(td.bloomTOP, 'bloom')
    bloom.inputConnectors[0].connect(over)
    bloom.par.output = 'bloom'
    bloom.par.preblacklevel = 0.25
    bloom.nodeX, bloom.nodeY = 950, -130

    # ---- Chicago label: a caption typed on in the shot's first second (takes with lab > 0) ----
    label = scene.create(td.textTOP, 'label')
    label.par.fontfile.expr = CHICAGO
    label.par.outputresolution = 'custom'
    label.par.resolutionw, label.par.resolutionh = 1280, 720
    label.par.bgalpha = 0
    label.par.alignx = 'left'
    label.par.aligny = 'bottom'
    label.par.positionunit = 'pixels'
    label.par.fontsizexunit = 'pixels'
    label.par.positionx.expr = k('labx')
    label.par.positiony.expr = k('laby')
    label.par.fontsizex.expr = k('labsize')
    # Describe mode: the take's explanation instead of its caption, typed three times as fast
    label.par.text.expr = ("%s((%r if %s else %r)[%s], %s)"
                           "[:int(float(%s['age']) * 150.0 if %s else min(float(%s['age']), 2.0) * 50.0)]") % (
        pick, tuple(t.get('dlabels') or labels.get(t['name']) or ('',) for t in TAKES), DESC_ON,
        tuple(labels.get(t['name']) or ('',) for t in TAKES), take, k('s2'), S, DESC_ON, S)
    label.nodeX, label.nodeY = 950, 150

    crt = _glsl_top(scene, 'crt', 'crt.frag', 1050, 0)
    crt.inputConnectors[0].connect(over)
    crt.inputConnectors[1].connect(bloom)
    crt.inputConnectors[2].connect(label)
    _vecs(crt, [
        ('uFx', ("%s['pulse']" % H, "%s['hit_mid']" % H, "%s['t']" % H, "%s['energy']" % H)),
        ('uAmt', (k('bloom'), k('scan'), k('barrel'), 0.0035)),
        ('uPost', (k('post'), "%s * (1.0 if %s > 0.5 else 0.0)" % (k('inverts'), k('s2')), k('lab'), k('expo'))),
        ('uLab', (k('labcolr'), k('labcolg'), k('labcolb'), 0.0)),
        ('uPaper', (k('bgr'), k('bgg'), k('bgb'), 0.0)),
        ('uDesc', (k('strip'), "%s * %s" % (k('halo'), k('desc')), 0.0, 0.0)),
    ])
    scene.op('out1').inputConnectors[0].connect(crt)
    # force the word meshes to exist now, so a cut never waits for one
    for i, (geo, tp, target_w) in enumerate(words):
        tp.cook(force=True)
        scene.op('word_mat%d' % i).cook(force=True)
    return scene.path
