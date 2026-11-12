# Builder for /project1/sc_vector_scope. Run inside TouchDesigner (see sw_hub/SCENE_BRIEF.md).
# Idempotent: destroys and rebuilds the whole scene.
# The beam paths come from paths.npz, baked offline by bake_paths.py (plain python) and committed,
# so the scene needs nothing from <assets>/ to draw its words and wireframes. A pack may hold its
# own scenes/sc_vector_scope/paths.npz, paths.json and words.json; then those are used instead.
# see: experiments/sc_vector_scope/NOTES.md (2026-11-10; Portability and Packs 2026-11-11)
import json

try:
    import td
except ImportError:          # bake_paths.py imports this file outside TouchDesigner to read TAKES
    td = None

SLUG = 'sc_vector_scope'
if td is not None:              # inside TouchDesigner the repository is where the project file is saved
    REPO = td.project.folder.replace(chr(92), '/')
else:                           # plain python: this file is <repo>/experiments/<slug>/build.py
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2].as_posix()
HERE = REPO + '/experiments/' + SLUG
NSEG = 4096                     # beam samples per gun (bake_paths.N)
MAXGUNS = 9                     # eight for the pictures, one spare for the Describe label

# Everything the scene says and every model it shows. A pack's scenes/sc_vector_scope/words.json may
# replace any of these names (read once in build() through scene_lib's scene_words).
# WORDS, BLOCKS, GLYPHS, FORM and MODELS are what bake_paths.py bakes into paths.npz / paths.json,
# in this order; build() refuses to build when the loaded paths.json was baked from other ones.
#   MODELS rows: [model, 'slices', {slice_strokes arguments}] or [model, 'edges', cells, feature angle]
#   SCAN_MODELS rows: [model, size in the scan take's picture]
DEFAULTS = {
    'WORDS': [
        'LIVE SIGNAL', 'HERE. NOW.', 'DO NOT TOUCH', 'PLATE 07', 'CATALOGUE 0047', 'FEEDBACK',
        'LOUD IS BRIGHT.', 'LOOP. LOOP.',
    ],
    'BLOCKS': [
        'EVERY FRAME\nIS MADE NOW.', 'SOUND IN.\nPICTURE OUT.', 'ORIGIN UNKNOWN.\nDO NOT TOUCH.',
        'HANDLE WITH\nBOTH HANDS.', 'SIGNAL\nACQUIRED...', 'AN OBJECT WAS FOUND.\nIT HAS NO NAME.',
        'NOTHING ON THIS TUBE\nIS PRERENDERED.', 'BEAM LINK\n....... OPEN',
    ],
    'GLYPHS': ['&', '?', 'R', '07', 'S', 'O'],
    'FORM': 'CATALOGUE CARD',           # the name of the one drawn row (bake_paths.form_strokes)
    'MODELS': [
        ['amphora', 'slices', {'levels': 12, 'min_len': 0.2}],
        ['lander', 'edges', 16, 36],
        ['marble_bust', 'slices', {'levels': 18}],
        ['gramophone', 'slices', {'levels': 12, 'axis': 2, 'extra': [[0, 0.5], [1, 0.3]]}],
        ['hourglass', 'slices', {'levels': 10, 'min_len': 0.2}],
        ['space_helmet', 'slices', {'levels': 9, 'axis': 2, 'min_len': 0.3, 'extra': [[0, 0.5], [1, 0.5]]}],
        ['ribbon_loop', 'slices', {'levels': 10, 'axis': 0, 'min_len': 0.2, 'extra': [[2, 0.5], [1, 0.1]]}],
        ['skeleton_key', 'slices', {'levels': 16}],
        ['traffic_cone', 'slices', {'levels': 10, 'min_len': 0.25}],
        ['astrolabe', 'slices', {'levels': 10, 'min_len': 0.2, 'extra': [[0, 0.5], [2, 0.5], [0, 0.35], [2, 0.35]]}],
        ['rubber_duck', 'slices', {'levels': 12}],
        ['broken_column', 'slices', {'levels': 14}],
        ['pierced_stone', 'slices', {'levels': 14}],
        ['wire_cage', 'edges', 14, 36],
        ['balanced_solids', 'slices', {'levels': 16}],
        ['crystal_cluster', 'slices', {'levels': 10, 'axis': 0, 'min_len': 0.2, 'extra': [[2, 0.5], [1, 0.4]]}],
    ],
    # pictures the scan take pushes its raster out with: phrases (Archivo Black) and lit library models
    'SCAN_WORDS': ['HERE.\nNOW.', 'DO NOT\nTOUCH', 'PLATE\n07', 'REAL\nTIME', 'NOW', 'LOUD.\nLOUD.', '12-B'],
    'SCAN_MODELS': [['marble_bust', 1.1], ['rubber_duck', 1.2], ['space_helmet', 0.95]],
}
BAKED = (('word', 'WORDS'), ('block', 'BLOCKS'), ('glyph', 'GLYPHS'), ('model', 'MODELS'))   # paths.json group, DEFAULTS name
WORD, BLOCK, GLYPH, FORM, MODEL = 'word', 'block', 'glyph', 'form', 'model'     # groups of paths.json, by name

# phosphors: (beam colour, per-channel fraction kept each frame)
P31 = dict(tint=(0.22, 1.0, 0.36), decay=(0.80, 0.93, 0.84), grat=(0.25, 0.9, 0.45))      # green
AMBER = dict(tint=(1.0, 0.56, 0.10), decay=(0.94, 0.88, 0.70), grat=(0.9, 0.55, 0.2))
P4 = dict(tint=(0.62, 0.80, 1.0), decay=(0.80, 0.86, 0.92), grat=(0.45, 0.6, 0.8))        # blue-white
P7 = dict(tint=(0.55, 0.75, 1.0), decay=(0.955, 0.94, 0.70), grat=(0.7, 0.75, 0.4))       # radar: blue flash, long yellow afterglow
AQUA = dict(tint=(0.16, 1.0, 0.82), decay=(0.70, 0.90, 0.93), grat=(0.2, 0.8, 0.7))
ROSE = dict(tint=(1.0, 0.36, 0.60), decay=(0.84, 0.60, 0.80), grat=(0.9, 0.4, 0.6))        # hot pink, white where it piles up
VIOLET = dict(tint=(1.0, 0.72, 1.0), decay=(0.972, 0.90, 0.985), grat=(0.6, 0.4, 0.9))     # pink-white flash, long violet afterglow

# the scan take's picture slot in Describe mode: what the scan take is, in two short lines
SCAN_DESCRIBE = ['SCAN\nLINES', '64\nLINES', 'BRIGHT\nLIFTS', 'RUTT-\nETRA']
# What a library model becomes when <assets>/models is not there: TouchDesigner's bundled teapot,
# which is 2 units wide and sits on the floor; library models are 1 unit and centred. (scale, lift)
TEAPOT_FIT = (0.5, -0.23)

TAKE_DEFAULT = dict(
    kind=0, group=WORD, stride=1, guns=1, group2=(0, 1), alt=0, beats=4,
    scale=1.0, offx=0.0, offy=0.0, roll=0.0, yaw=0.0, tilt=0.0, persp=0.0,
    aud=0.05, audsmooth=1.0, audspan=1.0,
    sigma=0.0032, gain=1.0, retrace=0.12, trace=1.0, head=0.25, dissolve=0.0, blob=0.45,
    phos=P31, tintb=None, arcade=0,
    glow=0.9, wide=0.8, expo=1.0, core=0.6,
    grat=1, gratlum=0.10, invert=0, bezel=1,
    # the small label gun of the gonio, timebase and waterfall takes: size, brightness, offset multipliers
    lblscale=1.0, lblpen=1.0, lblox=1.0, lbloy=1.0,
    # the extra Describe label gun (lgn 0 = none): rows, position, size, brightness, beam width
    lg0=0, lgn=0, lx=0.0, ly=0.0, lsize=0.4, lpen=1.0, lsigma=0.0022,
    steady=0,                   # 1: hits and section changes do not shake the drawing (so its words can be read)
    lthin=0,                    # 1: the take's own label gun (its last) is drawn with the lsigma beam width
    # 1: the take uses the picture named by Input, in its own way (see path.frag); 0: it ignores it.
    # Tried and dropped 2026-11-11: the picture as beam brightness on gonio, macro and wall (i1_sheet.png): unrecognisable.
    inmode=0,
)

# One row per take: the same machine pointed at a different picture.
# kind selects the composition code in shaders/path.frag.
# describe: what the take shows when the scene's Describe toggle is on. `words` are baked into
# paths.npz as group 'd_<name>' by `python bake_paths.py --describe` (re-run it after editing them).
#   as_='main'  : they replace the take's own phrases.
#   as_='label' : the take has no words of its own, so one extra gun draws them small at `pos`.
#   glyphs      : replaces the giant letters of the macro take.
#   over        : take values that differ in Describe mode (mostly: make the words legible).
TAKES = [
    dict(name='word', kind=0, group=WORD, beats=4, scale=1.02, offx=-0.42, offy=-0.36,
         aud=0.05, audsmooth=1.2, gain=0.2, dissolve=1.0, phos=P31, grat=1, gratlum=0.5,
         describe=dict(as_='main', words=[
             'VECTOR SCOPE', 'ONE BEAM\nDRAWS THIS', 'AUDIO SHAKES\nTHE LINE', 'SLOW BEAM =\nBRIGHT LINE',
             'EVERY 4 BEATS\nIT LETS GO', 'THE GLOW IS\nFADING PHOSPHOR'])),
    dict(name='gonio', kind=1, group=WORD, guns=2, beats=8, aud=1.2, sigma=0.0045, gain=0.09,
         phos=AMBER, grat=2, gratlum=0.6, wide=1.2,
         describe=dict(as_='main', words=['STEREO FIELD', 'RAW AUDIO\nSAMPLES', 'LEFT AGAINST\nRIGHT', '800 SAMPLES\nPER FRAME'],
                       over=dict(lblscale=1.5, lblpen=3.5, lblox=0.9, lbloy=0.86, lthin=1, lsigma=0.0024))),
    dict(name='wire', kind=2, group=MODEL, stride=0, guns=3, beats=8, scale=1.36, offx=0.5, offy=-0.02, yaw=0.9, tilt=0.38,
         persp=1.0, aud=0.02, audsmooth=2.0, sigma=0.0024, gain=0.3, phos=P4, grat=1, gratlum=0.4,
         describe=dict(as_='label', pos=(-1.14, -0.84), size=0.46, pen=0.7, words=[
             'A 3D MODEL\nTRACED BY THE BEAM', 'ONE TURNING VIEW\nFRONT AND TOP', 'NEW MODEL\nEVERY 8 BEATS'])),
    dict(name='macro', kind=3, group=GLYPH, beats=8, scale=3.6, aud=0.16, audsmooth=2.5, audspan=0.5,
         sigma=0.011, gain=0.3, trace=0.55, head=0.125, phos=P7, grat=0, bezel=0, wide=1.5, glow=1.2,
         describe=dict(as_='label', pos=(-1.1, -0.8), size=0.5, pen=0.9, glyphs=['X', 'Y', 'XY', 'S', 'O'], words=[
             'MACRO: ONE LETTER\nOUTLINE, VERY CLOSE', 'A WIDE BEAM\nOUT OF FOCUS', 'BLUE FLASH\nYELLOW AFTERGLOW'])),
    dict(name='arcade', kind=4, group=MODEL, stride=2, guns=8, beats=4, scale=0.62, persp=0.8, aud=0.012,
         sigma=0.0019, gain=0.55, retrace=0.05, phos=dict(tint=(1, 1, 1), decay=(0.6, 0.6, 0.6), grat=(0.3, 0.3, 0.4)),
         arcade=1, grat=0, bezel=0, glow=0.7, wide=0.6, core=0.2,
         describe=dict(as_='label', pos=(0.0, 0.0), size=0.62, pen=0.8, words=[
             'EIGHT BEAMS, EIGHT 3D MODELS', 'THE BOARD SHUFFLES EVERY BAR', '4096 POINTS PER MODEL'])),
    dict(name='timebase', kind=5, group=WORD, guns=3, beats=4, aud=0.42, sigma=0.0030, gain=0.16,
         phos=P4, grat=1, gratlum=0.6, inmode=1,
         describe=dict(as_='main', words=['LEFT AND RIGHT\nWAVEFORMS', 'TIME RUNS\nLEFT TO RIGHT', 'ONE FRAME\nOF AUDIO'],
                       over=dict(lblscale=1.5, lblpen=1.4, lblox=0.9, lbloy=0.9, lthin=1, lsigma=0.0024))),
    dict(name='lissajous', kind=6, group=WORD, guns=4, beats=8, scale=0.86, yaw=0.35, tilt=0.5, persp=0.6,
         aud=0.03, audsmooth=3.0, sigma=0.0026, gain=0.3, phos=AMBER, tintb=(1.0, 0.16, 0.05), grat=2, gratlum=0.35, bezel=0,
         describe=dict(as_='label', pos=(-1.15, -0.8), size=0.5, pen=0.8, words=[
             'LISSAJOUS KNOTS', 'SINE WAVES\nON X, Y AND Z', 'NEW RATIOS\nEVERY 8 BEATS'])),
    dict(name='wall', kind=7, group=BLOCK, stride=1, guns=8, beats=8, scale=0.6, aud=0.012, audsmooth=1.0,
         sigma=0.0021, gain=1.0, trace=0.5, head=0.0625, phos=P31, grat=0, invert=1, bezel=1, glow=0.4, wide=0.3,
         describe=dict(as_='main', over=dict(trace=1.0, scale=0.44, gain=0.4, steady=1), words=[
             'ONE BEAM\nDRAWS IT ALL.', 'SLOW BEAM:\nBRIGHT LINE.', 'CORNERS BURN\nAS DOTS.', 'THE SCREEN\nIS INVERTED.',
             '4096 POINTS\nPER BLOCK.', 'LEFT AUDIO\nMOVES X.', 'RIGHT AUDIO\nMOVES Y.', 'EIGHT BLOCKS,\nEIGHT BEAMS.'])),
    dict(name='dial', kind=8, group=WORD, stride=1, guns=6, beats=4, scale=1.0, persp=0.7, aud=0.03, audsmooth=3.0,
         sigma=0.0026, gain=0.3, phos=AQUA, tintb=(1.0, 1.0, 1.0), grat=0, bezel=0, glow=1.0, wide=0.9,
         describe=dict(as_='main', words=[
             'TEXT BENT ROUND A RING', 'ONE NOTCH PER BEAT', 'THREE RINGS', 'KICKS PART THE RINGS',
             'WAVEFORM AT THE HUB', 'POLAR COORDINATES', 'SIX BEAMS', 'MIDDLE RING TURNS BACK'])),
    dict(name='scan', kind=9, group=WORD, guns=8, beats=8, scale=1.0, persp=0.55, aud=0.11, audsmooth=2.0,
         sigma=0.0019, gain=1.6, retrace=0.0, phos=ROSE, grat=0, bezel=1, glow=0.8, wide=0.7, core=0.9, inmode=1,
         describe=dict(as_='label', pos=(-0.95, 0.8), size=0.55, pen=0.5, words=[
             'PICTURE BRIGHTNESS\nLIFTS 64 SCAN LINES', 'A RUTT-ETRA SCAN\nSEEN AT A SLANT'])),
    dict(name='waterfall', kind=10, group=WORD, guns=2, beats=4, aud=0.9, sigma=0.0022, gain=0.22,
         phos=VIOLET, grat=0, bezel=0, glow=0.9, wide=1.0, inmode=1,
         describe=dict(as_='main', words=['WATERFALL', 'ONE TRACE\nCLIMBS', 'AFTERGLOW\nKEEPS THE PAST', '30 STEPS\nPER 4 BEATS'],
                       over=dict(lblscale=1.5, lblpen=2.5, lblox=0.9, lbloy=0.9, lthin=1))),
]


def describe_words(t):
    """Every word take `t` can show in Describe mode, in the order used (preset.json mirrors this)."""
    d = t.get('describe') or {}
    w = list(d.get('words', []))
    if t['name'] == 'scan':
        w = list(SCAN_DESCRIBE) + w
    return w


def baked_names(words):
    """The row names bake_paths.py writes for a words dict, per group of paths.json."""
    out = {g: [w if isinstance(w, str) else w[0] for w in words[k]] for g, k in BAKED}
    out['block'] = [b.replace('\n', ' / ') for b in out['block']]
    out['form'] = [words['FORM']]
    return out


def _check_baked(words, meta, where):
    """The loaded paths.json must have been baked from these words and models, in this order."""
    for group, want in baked_names(words).items():
        have = [meta['names'][i] for i in meta['groups'].get(group, [])]
        if have != want:
            raise RuntimeError('%s: group %r holds %r but the words say %r; run python bake_paths.py '
                               '(a pack with its own words.json needs its own paths.npz and paths.json)'
                               % (where, group, have[:3], want[:3]))


def _describe_row(t, d, META):
    """The take's values with Describe on. Fails loudly if paths.npz was not re-baked for the words."""
    NAMES = META['names']
    dd = dict(d)
    ds = t.get('describe')
    if not ds:
        return dd
    dd.update(ds.get('over', {}))
    name = 'd_' + t['name']
    if ds.get('words'):
        baked = [NAMES[i] for i in META['groups'].get(name, [])]
        want = [w.replace('\n', ' / ') for w in ds['words']]
        if baked != want:
            raise RuntimeError('%s: Describe words changed; run python bake_paths.py --describe' % t['name'])
    if ds.get('glyphs'):
        if [NAMES[i] for i in META['groups'].get(name + '_glyph', [])] != list(ds['glyphs']):
            raise RuntimeError('%s: Describe glyphs changed; run python bake_paths.py --describe' % t['name'])
        dd['group'] = name + '_glyph'
    if ds['as_'] == 'main':
        dd['group'] = name
    else:
        dd.update(guns=d['guns'] + 1, lg0=META['groups'][name][0], lgn=len(META['groups'][name]), lx=ds['pos'][0], ly=ds['pos'][1],
                  lsize=ds.get('size', 0.4), lpen=ds.get('pen', 1.0), lsigma=min(d['sigma'], 0.0024))
    return dd


def _rows(META):
    """The takes table. META is the loaded paths.json: a take names its group, the rows come from there."""
    G = {k: (v[0], len(v)) for k, v in META['groups'].items()}   # group -> (first row, count)
    span = lambda g: G[g] if isinstance(g, str) else g
    cols = ['kind', 'g0', 'gn', 'stride', 'guns', 'g0b', 'gnb', 'alt', 'beats', 'scale', 'offx', 'offy', 'roll',
            'yaw', 'tilt', 'persp', 'aud', 'audsmooth', 'audspan', 'sigma', 'gain', 'retrace', 'trace', 'head', 'dissolve', 'blob',
            'dr', 'dg', 'db', 'tar', 'tag', 'tab', 'tbr', 'tbg', 'tbb', 'arcade', 'glow', 'wide', 'expo', 'core',
            'grat', 'gratlum', 'invert', 'bezel', 'gr', 'gg', 'gb',
            'lblscale', 'lblpen', 'lblox', 'lbloy', 'lg0', 'lgn', 'lx', 'ly', 'lsize', 'lpen', 'lsigma', 'lthin', 'steady', 'inmode']
    # every column twice: the take as it is, and ('d_' + column) the take with Describe on
    rows = [['name'] + cols + ['d_' + c for c in cols]]
    for t in TAKES:
        base = dict(TAKE_DEFAULT)
        base.update(t)
        vals = []
        for d in (base, _describe_row(t, base, META)):
            ph = d['phos']
            tb = d['tintb'] or ph['tint']
            v = dict(d, g0=span(d['group'])[0], gn=span(d['group'])[1], g0b=span(d['group2'])[0], gnb=span(d['group2'])[1],
                     dr=ph['decay'][0], dg=ph['decay'][1], db=ph['decay'][2],
                     tar=ph['tint'][0], tag=ph['tint'][1], tab=ph['tint'][2], tbr=tb[0], tbg=tb[1], tbb=tb[2],
                     gr=ph['grat'][0], gg=ph['grat'][1], gb=ph['grat'][2])
            vals += [v[c] for c in cols]
        rows.append([t['name']] + vals)
    return cols, rows


def _file_dat(scene, name, rel, x, y):
    """A Text DAT kept in step with a file of this folder (rel is relative to it)."""
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here(%r)" % rel
    d.par.syncfile = True
    d.text = open(HERE + '/' + rel, encoding='utf-8').read()     # the DAT loads its file a frame late
    d.nodeX, d.nodeY = x, y
    return d


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


def _glsl(scene, name, frag, x, y, fmt='rgba16float', w=1280, h=720):
    g = scene.create(td.glslTOP, name)
    for d in list(g.docked):
        d.destroy()
    g.par.pixeldat = _file_dat(scene, name + '_frag', 'shaders/' + frag, x, y - 130).path
    g.par.format = fmt
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = w, h
    g.nodeX, g.nodeY = x, y
    return g


def build():
    LIB = {'op': op}
    exec(open(REPO + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 1750, -1100)
    H = "op('hub')"
    NT = len(TAKES)
    # the pack's words and baked paths if it has its own, else the ones of this folder
    W = LIB['scene_words'](scene, DEFAULTS)
    where = LIB['scene_paths'](scene).scene_file('paths.json')
    META = json.load(open(where, encoding='utf-8'))
    _check_baked(W, META, where)

    # ---- the TAKES table and the current take's row as channels
    cols, rows = _rows(META)
    tbl = scene.create(td.tableDAT, 'takes')
    tbl.clear()
    for r in rows:
        tbl.appendRow(r)
    tbl.nodeX, tbl.nodeY = -800, 500
    tk = scene.create(td.constantCHOP, 'tk')
    tk.seq.const.numBlocks = len(cols)
    for i, c in enumerate(cols):
        getattr(tk.par, 'const%dname' % i).val = c
        getattr(tk.par, 'const%dvalue' % i).expr = (     # not op('shot'): its age channel cooks every frame
            "float(op('takes')[int(parent().par.Take)%%%d+1,('d_%s' if parent().par.Describe else '%s')])" % (NT, c, c))
    tk.nodeX, tk.nodeY = -600, 500
    T = lambda c: "op('tk')['%s']" % c

    # ---- baked paths
    cb = _file_dat(scene, 'load_paths', 'load_paths.py', -800, 330)      # reads paths.npz (the pack's, if it has one)
    shapes = scene.create(td.scriptTOP, 'shapes')
    for d in list(shapes.docked):
        d.destroy()
    shapes.par.callbacks = cb.path
    shapes.nodeX, shapes.nodeY = -600, 330
    shapes.cook(force=True)

    # ---- the music itself: this frame's stereo samples as a texture (read-only select of the hub's player)
    aud = scene.create(td.selectCHOP, 'aud')
    aud.par.chop = '/project1/sw_hub/audio'
    aud.nodeX, aud.nodeY = -800, 200
    audtex = scene.create(td.choptoTOP, 'audtex')
    audtex.par.chop = aud.path
    audtex.par.dataformat = 'rg'
    audtex.par.format = 'rgba32float'
    audtex.nodeX, audtex.nodeY = -600, 200

    # ---- hits ring like a damped spring
    hits = scene.create(td.selectCHOP, 'hits')
    hits.par.chop = 'hub'
    hits.par.channames = 'hit_low hit_mid'
    hits.nodeX, hits.nodeY = -800, 60
    spring = scene.create(td.springCHOP, 'spring')
    hits.outputConnectors[0].connect(spring)
    # The hit envelope is a force on a light mass, so the output starts at rest, swings out and
    # rings back through zero at about 5 Hz. (Method 'disp' only followed the envelope: min -0.05.)
    spring.par.method = 'force'
    spring.par.mass = 0.002
    spring.par.springk = 1.92
    spring.par.dampingk = 0.01
    spring.nodeX, spring.nodeY = -600, 60
    SP = lambda c: "max(-1.5, min(1.5, op('spring')['%s']))" % c

    # ---- a section change: 1 at the change, gone in about 0.4 s (section minus a lagged copy of itself)
    sec = scene.create(td.selectCHOP, 'sec')
    sec.par.chop = 'hub'
    sec.par.channames = 'section'
    sec.nodeX, sec.nodeY = -800, -60
    seclag = scene.create(td.lagCHOP, 'seclag')
    sec.outputConnectors[0].connect(seclag)
    seclag.par.lag1, seclag.par.lag2 = 0.7, 0.7     # measured: lag 0.3 left 0.2 of the kick after 0.2 s; lag 1.0 left 0.24 after 0.6 s
    seclag.nodeX, seclag.nodeY = -600, -60
    SECKICK = "max(0, min(1, abs(op('sec')['section'] - op('seclag')['section'])))"

    # ---- the scan take's picture: a phrase or a lit, turning model, 512 x 288. Black on other takes,
    # so nothing here cooks unless the scan take is up.
    KIND9 = "(int(op('tk')['kind']) == 9)"
    SEEDI = "int(parent().par.Seed*997)"
    stext = scene.create(td.textTOP, 'scan_text')
    stext.par.outputresolution = 'custom'
    stext.par.resolutionw, stext.par.resolutionh = 512, 288
    stext.par.fontfile.expr = "mod.paths.font('archivo')"     # '' (the default face) with no assets
    stext.par.fontsizex = 120
    stext.par.fontautosize = 'fitiffat'
    stext.par.alignx, stext.par.aligny = 'center', 'center'
    stext.par.linespacing = -0.12
    stext.par.text.expr = ("(lambda w: w[(%s + int(op('hub')['beat_pos']//8) + 2*int(op('hub')['section'])) %% len(w)])"
                           "(%r if parent().par.Describe else %r)" % (SEEDI, tuple(SCAN_DESCRIBE), tuple(W['SCAN_WORDS'])))
    stext.nodeX, stext.nodeY = -1250, -250
    stblur = scene.create(td.blurTOP, 'scan_text_soft')
    stext.outputConnectors[0].connect(stblur)
    stblur.par.size = 7
    stblur.nodeX, stblur.nodeY = -1100, -250
    SCAN_MODELS = W['SCAN_MODELS']
    for i, (slug, size) in enumerate(SCAN_MODELS):
        geo = LIB['import_model'](scene, 'sm%d' % i, slug)
        geo.nodeX, geo.nodeY = -1400, -400 - i * 110
        geo.par.render.expr = "(%s//2) %% %d == %d" % (SEEDI, len(SCAN_MODELS), i)
        geo.par.ry.expr = "op('hub')['evolve']*40 + 50*math.sin(op('hub')['beat_pos']*math.pi/4)"
        geo.par.scale.expr = "%r*(1 + 0.10*max(-1, min(1.5, op('spring')['hit_low'])))" % float(size)
        geo.op('mat').par.roughness = 0.5
        # With no library the mesh is the teapot: untextured, and brought to the library's size and centre.
        HAVE = "mod.paths.have('models/%s/model.obj')" % slug
        geo.op('mat').par.basecolormap.expr = "'tex' if mod.paths.model_texture(%r) else ''" % slug
        # an empty file warns, so the unused `tex` then keeps the Movie File In's own default picture
        geo.op('tex').par.file.expr = "mod.paths.model_texture(%r) or app.samplesFolder + '/Map/Banana.tif'" % slug
        fit = geo.create(td.transformPOP, 'fit')
        geo.op('mesh').outputConnectors[0].connect(fit)
        fit.par.scale.expr = "1 if %s else %r" % (HAVE, TEAPOT_FIT[0])
        fit.par.ty.expr = "0 if %s else %r" % (HAVE, TEAPOT_FIT[1])
        geo.op('mesh').render = geo.op('mesh').display = False
        fit.render = fit.display = True
        geo.op('mesh').cook(force=True)     # load now, not on the cut that first shows it
        geo.op('tex').cook(force=True)
        fit.cook(force=True)
    scam = scene.create(td.cameraCOMP, 'scan_cam')
    scam.par.tz = 3.0
    scam.par.fov = 42
    scam.nodeX, scam.nodeY = -1250, -400
    skey = scene.create(td.lightCOMP, 'scan_key')
    skey.par.tx, skey.par.ty, skey.par.tz = -2.2, 2.0, 2.6
    skey.par.dimmer = 2.6
    skey.nodeX, skey.nodeY = -1250, -510
    sfill = scene.create(td.lightCOMP, 'scan_fill')
    sfill.par.tx, sfill.par.ty, sfill.par.tz = 2.5, -0.5, 2.0
    sfill.par.dimmer = 0.5
    sfill.nodeX, sfill.nodeY = -1250, -620
    srender = scene.create(td.renderTOP, 'scan_render')
    srender.par.camera = scam.path
    srender.par.geometry = 'sm*'
    srender.par.lights = 'scan_key scan_fill'
    srender.par.outputresolution = 'custom'
    srender.par.resolutionw, srender.par.resolutionh = 512, 288
    srender.nodeX, srender.nodeY = -1100, -400
    srblur = scene.create(td.blurTOP, 'scan_render_soft')
    srender.outputConnectors[0].connect(srblur)
    srblur.par.size = 4
    srblur.nodeX, srblur.nodeY = -950, -400
    sblack = scene.create(td.constantTOP, 'scan_black')
    sblack.par.colorr, sblack.par.colorg, sblack.par.colorb = 0, 0, 0
    sblack.par.outputresolution = 'custom'
    sblack.par.resolutionw, sblack.par.resolutionh = 16, 16
    sblack.nodeX, sblack.nodeY = -950, -150
    # ---- Input: the TOP named by the scene's Input parameter (another scene's out1), read only.
    # `inp` is 1 when it names a TOP that is not this scene's own output; blank or wrong = 0 = the scene as it was.
    inp = scene.create(td.constantCHOP, 'inp')
    inp.par.name0 = 'has'
    inp.par.value0.expr = ("int(bool(parent().par.Input.eval()) and getattr(op(parent().par.Input.eval()), 'isTOP', False)"
                           " and op(parent().par.Input.eval()).path != op('out1').path)")
    inp.nodeX, inp.nodeY = -1250, -30
    insel = scene.create(td.selectTOP, 'in_sel')
    insel.par.top.expr = "parent().par.Input.eval() if op('inp')['has'] else 'scan_black'"
    insel.par.outputresolution = 'custom'
    insel.par.resolutionw, insel.par.resolutionh = 512, 288
    insel.nodeX, insel.nodeY = -1100, -30
    insoft = scene.create(td.blurTOP, 'in_soft')
    insel.outputConnectors[0].connect(insoft)
    insoft.par.size = 3
    insoft.nodeX, insoft.nodeY = -950, -30
    ssrc = scene.create(td.switchTOP, 'scan_src')
    sblack.outputConnectors[0].connect(ssrc)
    stblur.outputConnectors[0].connect(ssrc)
    srblur.outputConnectors[0].connect(ssrc)
    insoft.outputConnectors[0].connect(ssrc)
    # three shots in five show a model, two a phrase; a take that can use the Input picture gets that instead
    USEIN = "(op('inp')['has'] and op('tk')['inmode'] > 0)"
    ssrc.par.index.expr = "3 if %s else ((1 + (%s %% 5 > 1)) if %s else 0)" % (USEIN, SEEDI, KIND9)
    ssrc.nodeX, ssrc.nodeY = -800, -250

    # ---- where the beam is
    path = _glsl(scene, 'path', 'path.frag', -300, 250, 'rgba32float', 1024, 4 * MAXGUNS)
    path.par.inputfiltertype = 'linear'
    shapes.outputConnectors[0].connect(path.inputConnectors[0])
    audtex.outputConnectors[0].connect(path.inputConnectors[1])
    ssrc.outputConnectors[0].connect(path.inputConnectors[2])
    loud = "min(1.6, " + H + "['rms'])"
    _vecs(path, [
        ('uGroup', (T('g0'), T('gn'), T('stride'), T('guns'))),
        ('uGroup2', (T('g0b'), T('gnb'), T('alt'), T('kind'))),
        ('uStep', (T('beats'), "op('shot')['seed']", "op('shot')['age']", H + "['beat_pos']")),
        ('uXform', (T('scale'), T('offx'), T('offy'), T('roll'))),
        ('uRot', (T('yaw'), T('tilt'), T('persp'), H + "['section']")),
        # the louder the passage, the more of the waveform gets into the beam
        ('uAud', (T('aud') + "*(0.5+1.2*smoothstep_(" + H + "['energy']))", T('audsmooth'), T('audspan'), H + "['level']")),
        ('uHit', (SP('hit_low'), SP('hit_mid'), "min(1.2, " + H + "['hit_high'])", H + "['pulse']")),
        ('uTrace', (T('trace'), T('head'), T('dissolve'), T('blob'))),
        ('uTime', (H + "['evolve']", H + "['bar_pos']", H + "['energy']", SECKICK)),
        # the scan take's label stays off while its own big Describe words are the picture (they explain it already)
        ('uDesc', (T('lg0'), T('lgn'), T('lsize'), T('lpen') + "*(0 if (int(op('tk')['kind']) == 9 and op('scan_src').par.index == 1) else 1)")),
        ('uDescB', (T('lx'), T('ly'), "int(parent().par.Describe)", T('steady'))),
        ('uDescC', (T('lblscale'), T('lblpen'), T('lblox'), T('lbloy'))),
        ('uIn', ("int(op('tk')['inmode'] > 0 and op('inp')['has'] > 0)", 0, 0, 0)),
    ])
    # smoothstep_ is not a Python builtin: expand it
    p = path.par.vec5valuex
    p.expr = T('aud') + "*(0.25+1.6*max(0, min(1, (" + H + "['energy']-0.33)/0.32)))"

    # ---- the beam: one instanced quad per segment, additive
    geo = scene.create(td.geometryCOMP, 'beam')
    for c in geo.children:
        c.destroy()
    quad = geo.create(td.rectanglePOP, 'quad')
    quad.render = True
    quad.display = True
    geo.par.instancing = True
    geo.par.instancecountmode = 'manual'
    geo.par.numinstances.expr = "%d*int(op('tk')['guns'])" % NSEG
    geo.nodeX, geo.nodeY = 0, 250
    mat = scene.create(td.glslMAT, 'beam_mat')
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = _file_dat(scene, 'beam_vertex', 'shaders/beam_vertex.glsl', -100, -80).path
    mat.par.pdat = _file_dat(scene, 'beam_pixel', 'shaders/beam_pixel.glsl', 60, -80).path
    mat.seq.sampler.numBlocks = 1
    mat.par.sampler0name = 'sPath'
    mat.par.sampler0top = path.path
    mat.par.sampler0filter = 'nearest'
    mat.par.blending = True
    mat.par.srcblend = 'one'
    mat.par.destblend = 'one'
    mat.par.depthtest = False
    mat.par.depthwriting = False
    mat.par.cullface = 'neither'
    _vecs(mat, [
        # hats fatten the beam for an instant; kicks brighten it
        ('uBeam', (T('sigma') + "*(1+0.5*min(1.2, " + H + "['hit_high']))",
                   T('gain') + "*(0.8+0.8*min(1.2, " + H + "['hit_low']))", T('retrace'), T('guns'))),
        ('uTintA', (T('tar'), T('tag'), T('tab'), "math.floor(op('shot')['seed']*6)")),
        ('uTintB', (T('tbr'), T('tbg'), T('tbb'), T('arcade'))),
        ('uLabel', (T('lgn'), T('lsigma'), T('lthin'), 0)),
    ])
    mat.nodeX, mat.nodeY = 0, 80
    geo.par.material = mat.path
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.nodeX, cam.nodeY = 0, 400
    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.path
    render.par.geometry = geo.path
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.antialias = '1x'
    render.nodeX, render.nodeY = 200, 250

    # ---- phosphor persistence
    fb = scene.create(td.feedbackTOP, 'phos_fb')
    phos = _glsl(scene, 'phos', 'phosphor.frag', 500, 250)
    render.outputConnectors[0].connect(fb)
    render.outputConnectors[0].connect(phos.inputConnectors[0])
    fb.outputConnectors[0].connect(phos.inputConnectors[1])
    fb.par.top = phos.path
    fb.par.format = 'rgba16float'
    fb.nodeX, fb.nodeY = 350, 100
    _vecs(phos, [
        ('uDecay', (T('dr'), T('dg'), T('db'), "math.floor((parent().par.Shotstart*0.618+parent().par.Take*0.131+parent().par.Seed*0.71)%1*255)/255")),
        ('uFrame', ("absTime.stepSeconds*60", 0, 0, 0)),
    ])

    # ---- glow: two reduced-size blurs
    def glow(name, w, h, size, x):
        r = scene.create(td.resolutionTOP, name + '_small')
        r.par.outputresolution = 'custom'
        r.par.resolutionw, r.par.resolutionh = w, h
        phos.outputConnectors[0].connect(r)
        b = scene.create(td.blurTOP, name)
        b.par.size = size
        r.outputConnectors[0].connect(b)
        r.nodeX, r.nodeY = x, 60
        b.nodeX, b.nodeY = x + 150, 60
        return b
    tight = glow('glow_tight', 640, 360, 5, 650)
    wide = glow('glow_wide', 320, 180, 20, 650)
    wide.nodeY = -60
    scene.op('glow_wide_small').nodeY = -60

    post = _glsl(scene, 'post', 'post.frag', 1000, 250, 'rgba8fixed')
    phos.outputConnectors[0].connect(post.inputConnectors[0])
    tight.outputConnectors[0].connect(post.inputConnectors[1])
    wide.outputConnectors[0].connect(post.inputConnectors[2])
    _vecs(post, [
        ('uGlow', (T('glow'), T('wide'), T('expo'), T('core'))),
        ('uGrat', (T('grat'), T('gratlum'), T('invert'), T('bezel'))),
        ('uGratCol', (T('gr'), T('gg'), T('gb'), 0)),
        ('uLive', (H + "['pulse']", "min(1.2, " + H + "['hit_high'])", H + "['energy']", "absTime.seconds%100")),
    ])
    post.outputConnectors[0].connect(scene.op('out1'))
    fb.par.resetpulse.pulse()
    return scene.path
