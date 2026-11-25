# press_driver.py: the pressman. Text of the Execute DAT `cook_driver` in
# /project1/sc_riso_press (replaces the scaffold's driver). Once per frame, while the
# scene is on screen or Preview is on, it reads the shot (Take, Seed) and the audio feed,
# runs the press state (paper advance, roller passes, plate latches, register kicks) and
# writes every uniform and camera/model parameter, then cooks out1.
# The TAKES table and the words (the big words, the rows of phrases) live in build.py and
# reach this file through parent().fetch('TAKES') and parent().fetch('WORDS').
# see: experiments/sc_riso_press/NOTES.md (2026-11-10)
import math
import random

S = dict(last=-1e9, shot=None, sheet=0, bidx=None, section=None, t_adv=0.0, t_shot=0.0,
         slide=False, fast=True, laid=[True] * 4, t_latch=[0.0] * 4, hits={},
         pos=[[0.0, 0.0] for _ in range(4)], vel=[[0.0, 0.0] for _ in range(4)],
         bass=0.0, voc=0.0, model=None)
# ink triples for plates left on their default ink; the section and the seed pick one
INKSETS = [(0, 1, 2), (9, 5, 2), (0, 5, 2), (4, 1, 2), (10, 6, 9), (0, 6, 2), (9, 1, 0), (5, 4, 2)]
PARS = {}
UMAP = {}


def _h(*a):
    x = math.sin(sum((i + 1) * 12.9898 * float(v) for i, v in enumerate(a)) + 1.234) * 43758.5453
    return x - math.floor(x)


def _setp(o, name, v):
    key = (o.path, name)
    p = PARS.get(key)
    if p is None:
        p = PARS[key] = getattr(o.par, name)
    if p.val != v:
        p.val = v


def _setu(top, name, vals):
    m = UMAP.get(top.path)
    if m is None:
        m = UMAP[top.path] = {getattr(top.par, 'vec%dname' % i).eval(): i for i in range(top.seq.vec.numBlocks)}
    i = m[name]
    for c, v in zip('xyzw', vals):
        _setp(top, 'vec%dvalue%s' % (i, c), float(v))


def _kick(i, s, tk):
    a = random.random() * 6.2832
    m = tk['kick'] * s * 0.04 * S.get('kscale', 1.0)
    S['pos'][i][0] += math.cos(a) * m
    S['pos'][i][1] += math.sin(a) * m


def step(shot):
    hub = op('hub')

    def H(n, d=0.0):
        c = hub[n]
        if c is None:
            return d
        v = float(c[0])
        return v if v == v else d

    now = absTime.seconds
    gapd = now - S['last']
    dt = min(0.1, max(0.0, gapd))
    S['last'] = now
    takes = parent().fetch('TAKES')
    W = parent().fetch('WORDS')
    tk = takes[shot[0] % len(takes)]
    seed = shot[1]
    newshot = (shot != S['shot']) or gapd > 0.3
    S['shot'] = shot
    beat_pos, section, evolve = H('beat_pos'), int(H('section')), H('evolve')
    bidx = math.floor(beat_pos / tk['adv'])
    latch = [0, 0, 0, 0]
    latchprev = 0
    advance = newshot or bidx != S['bidx'] or section != S['section']
    S['bidx'], S['section'] = bidx, section
    plates = tk['plates']
    laidmask = [1, 1, 1, 1]
    if advance:
        # (the first sheet after a cut was exposed whole, so it is never masked: masking it
        # blanked every edition sheet when a beat line fell inside the arrival)
        if not newshot and not S['fast']:
            laidmask = [1 if v else 0 for v in S['laid']]
        S['sheet'] += 1
        S['t_adv'] = now
        S['laid'] = [False] * 4
        S['fast'] = newshot
        S['slide'] = not newshot and not tk['reprint']
        latchprev = 1
        if newshot:
            # a cut: expose everything now so the edition sheets already carry this take's
            # image; the live sheet still arrives blank and is rolled up plate by plate
            latch = [1, 1, 1, 1]
            S['t_shot'] = now
            for i in range(4):
                S['pos'][i] = [0.0, 0.0]
                S['vel'][i] = [0.0, 0.0]

    # ---- paper slide and roller passes ----
    age = now - S['t_adv']
    beat_s = 0.48
    slide_dur = 0.0 if (S['fast'] or tk['reprint']) else min(0.24, tk['adv'] * beat_s * 0.4)
    slide = 0.0
    if S['slide'] and slide_dur > 0 and age < slide_dur:
        slide = (1.0 - age / slide_dur) ** 3
    layint = 0.085 if S['fast'] else tk['lay'] * beat_s
    sweep = 0.12 if S['fast'] else min(0.16, max(0.06, layint * 0.9))
    lay = []
    flash = 0.0
    n = 0
    for i in range(4):
        if plates[i]['mode'] > 2.5:
            lay.append(1.0)
            S['laid'][i] = True
            continue
        st = slide_dur * 0.5 + 0.02 + n * layint
        n += 1
        v = 1.0 if tk['inst'] else min(1.0, max(0.0, (age - st) / sweep))
        if v > 0 and not S['laid'][i]:
            S['laid'][i] = True
            latch[i] = 1
            S['t_latch'][i] = now
            _kick(i, 0.6, tk)
        if age > st and not tk['inst']:
            flash = max(flash, math.exp(-(age - st) * 14.0))
        lay.append(v)

    # ---- drum hits re-expose a plate and knock it out of register ----
    for nm, env, pls in (('hits_low', 'hit_low', (0, 3)), ('hits_mid', 'hit_mid', (1,)), ('hits_high', 'hit_high', (2,))):
        v = H(nm)
        pv = S['hits'].get(nm)
        S['hits'][nm] = v
        if pv is not None and 0 < v - pv < 4:
            stg = min(1.3, max(0.3, H(env)))
            for i in pls:
                if S['laid'][i] and lay[i] >= 1.0:
                    latch[i] = 1
                    S['t_latch'][i] = now
                    _kick(i, stg, tk)
    for i in range(4):
        if S['laid'][i] and lay[i] >= 1.0 and (tk['live'] or now - S['t_latch'][i] > tk['relatch']):
            latch[i] = 1
            S['t_latch'][i] = now
    # register springs back (under-damped, so it rings once)
    for _ in range(2):
        h = dt * 0.5
        for i in range(4):
            for a in (0, 1):
                acc = -260.0 * S['pos'][i][a] - 15.0 * S['vel'][i][a]
                S['vel'][i][a] += acc * h
                S['pos'][i][a] += S['vel'][i][a] * h

    S['bass'] += (min(1.6, H('bass')) - S['bass']) * min(1.0, dt * 9.0)
    gain = tk['gain'] * (0.70 + 0.60 * S['bass'])
    energy = min(1.0, max(0.0, (H('energy') - 0.33) / 0.32))
    S['kscale'] = 0.65 + 0.7 * energy
    S['voc'] += (min(1.3, H('vocals')) - S['voc']) * min(1.0, dt * 6.0)
    hl = min(1.2, H('hit_low'))
    flash = max(flash, 0.45 * hl)

    # ---- view ----
    # D = this take's Describe words (build.py TAKES 'describe') while the Describe toggle is on
    D = (tk.get('describe') or {}) if shot[3] else None
    r1, r2, r3, r4 = _h(seed, 1), _h(seed, 2), _h(seed, 3), _h(seed, 4)
    snap = math.exp(-(now - S['t_shot']) * 9.0) * tk['snap']
    zoom = tk['zoom'] * (1 + 0.03 * math.sin(evolve * 0.9 + seed * 9)) * (1 + 0.22 * snap) * (1 - 0.03 * hl)
    rot0 = (D.get('rot', tk['rot']) if D else tk['rot']) + (r1 - 0.5) * 2 * tk['rotjit']
    rotd = rot0 + 1.2 * math.sin(evolve * 0.5 + seed * 5) + 7 * snap * (1 if r2 > 0.5 else -1)
    cx0 = tk['centre'][0] + (r2 - 0.5) * 2 * tk['jit'][0]
    cy0 = tk['centre'][1] + (r3 - 0.5) * 2 * tk['jit'][1]
    cx = cx0 + tk['pan'][0] * math.sin(evolve * 0.33 + seed * 6.28)
    cy = cy0 + tk['pan'][1] * math.cos(evolve * 0.27 + seed * 3.1)
    cy -= 0.006 * zoom * min(1.2, H('hit_low'))

    # ---- model, camera, lights ----
    names = tk['models']
    mname, msize = names[(int(seed * 97) + section) % len(names)]      # a row: [model, size]
    if mname != S['model']:
        for g in parent().findChildren(name='m_*', maxDepth=1):
            _setp(g, 'render', g.name == 'm_' + mname)
        S['model'] = mname
    g = op('m_' + mname)
    if g is not None:
        _setp(g, 'scale', (D or tk).get('mscale', tk['mscale']) * msize * (1 + 0.05 * min(1.2, H('hit_low'))))
        _setp(g, 'ry', (tk['az'] + r4 * 360.0 * tk['azjit'] + evolve * tk['spin']) % 360.0)
        _setp(g, 'rx', tk['tilt'] + 6 * math.sin(evolve * 0.7 + seed * 4))
    cam = op('cam')
    dist, elev = tk['cam']
    e = math.radians(elev + (r1 - 0.5) * 14)
    _setp(cam, 'ty', dist * math.sin(e))
    _setp(cam, 'tz', dist * math.cos(e))
    mpos = (D or tk).get('mpos', tk['mpos'])
    _setp(cam, 'winx', -mpos[0])
    _setp(cam, 'winy', -mpos[1])
    # three lights laid out relative to the camera (which sits on +z): left-front, right,
    # top-back. The rig swings, it does not orbit, so every face keeps a different mix.
    a0 = (r2 - 0.5) * 1.2 + 0.55 * math.sin(evolve * 0.45 * tk['lightspin'] + seed * 6.2832)
    ce, se = math.cos(a0), math.sin(a0)
    for i, (x, y, z) in enumerate(((-2.6, 1.3, 2.4), (3.0, -0.2, 1.2), (0.3, 3.2, -1.6))):
        l = op('light%d' % i)
        _setp(l, 'tx', x * ce + z * se)
        _setp(l, 'tz', -x * se + z * ce)
        _setp(l, 'ty', y)

    # Input: another TOP in place of the three-light render (never one of this scene's own)
    src_top = op(shot[4]) if shot[4] else None
    use_in = (src_top is not None and src_top.isTOP and not src_top.path.startswith(parent().path + '/'))

    # ---- type ----
    tb, trw, tsl = op('t_big'), op('t_rows'), op('t_slug')
    mpx = tk['margin'] * 640.0     # (mpx * 0.5 - 11 below is the slug's old margin * 0.5 * 640 - 11)
    bside = tk['big']['alignx'] if r3 > 0.3 else ('right' if tk['big']['alignx'] == 'left' else 'left')
    words = (D.get('big') or ['']) if D is not None else (tk['words'] or W['BIG'])
    word = words[(section + int(seed * 31)) % len(words)]
    _setp(tb, 'text', word)
    _setp(op('fontsel'), 'value0', 1.0 if tk['bigfont'] == 'chicago' else 0.0)   # t_big's fontfile expression reads it
    if D is not None and D.get('bigfit', True) and word:
        # Describe: the whole word must be readable, so fit it to the part of the image area
        # that the view shows (widths were measured at build time: fetch('DW'))
        w100 = parent().fetch('DW', {}).get((tk['bigfont'], word), 70.0 * len(word))
        iw, ih = 1024.0 - 2 * mpx, 640.0 - 2 * mpx
        vw, vh = min(iw, tk['zoom'] * 1138.0 * 0.88), min(ih, tk['zoom'] * 640.0 * 0.88)
        vx = min(max(cx0 * 640.0, -(iw - vw) * 0.5), (iw - vw) * 0.5)
        vy = min(max(cy0 * 640.0, -(ih - vh) * 0.5), (ih - vh) * 0.5)
        size = min(D.get('bigmax', tk['big']['size']), 100.0 * (vw - 40.0) / max(w100, 1.0), vh / 0.95)
        slack = max(0.0, (vw - 40.0 - w100 * size / 100.0) * 0.5)
        freey = max(0.0, (vh - size * 0.95) * 0.5)
        base = {'top': freey, 'bottom': -freey}.get(D.get('aligny', tk['big']['aligny']), 0.0)
        _setp(tb, 'fontsizex', round(size, 1))
        _setp(tb, 'alignx', 'center')
        _setp(tb, 'aligny', 'center')
        _setp(tb, 'positionx', round(vx + (slack if bside == 'right' else -slack), 1))
        _setp(tb, 'positiony', round(vy + min(max(base + (r2 - 0.5) * tk['big']['yjit'], -freey), freey), 1))
    else:
        _setp(tb, 'fontsizex', tk['big']['size'])
        _setp(tb, 'alignx', bside)
        _setp(tb, 'aligny', tk['big']['aligny'])
        _setp(tb, 'positionx', 0)
        _setp(tb, 'positiony', tk['big']['y'] + (r2 - 0.5) * tk['big']['yjit'])
    src = D['rows'] if (D is not None and D.get('rows')) else W['PHRASES']
    k0 = (section * 3 + int(seed * 17)) % len(src)
    rsize = D.get('rowsize', tk['rowsize']) if D is not None else tk['rowsize']
    rowx, evrow = 0.0, evolve
    if D is not None and D.get('rowlines'):
        # Describe: one sentence per line, starting at the left edge of what the view shows and
        # small enough that the widest line fits across it; the scroll restarts with the shot
        vw = tk['zoom'] * 1138.0 - 110.0
        rsize = min(rsize, 100.0 * vw / max(parent().fetch('DW', {}).get(('rows', shot[0] % len(takes)), 1500.0), 1.0))
        rowx = min(max(512.0 + cx0 * 640.0 - vw * 0.5, 0.0), 1024.0 - vw)
        rows = chr(10).join((src[k0:] + src[:k0]) * 3)
        if newshot:
            S['ev_shot'] = evolve
        evrow = evolve - S.get('ev_shot', evolve)
    else:
        rows = '  '.join((src[k0:] + src[:k0]) * 2)
    _setp(trw, 'text', rows)
    _setp(trw, 'fontsizex', round(rsize, 1) if D is not None else rsize)
    _setp(trw, 'positionx', round(rowx, 1))
    _setp(trw, 'linespacing', round(-14.0 * rsize / 92.0, 1) if D is not None else -14)
    slug, ssize = '%s  SHEET %%04d' % tk['name'].upper(), 24
    if D is not None and D.get('slug'):
        # a Describe slug must stop short of the register cross in the middle of the bottom margin
        slug = D['slug']
        ssize = int(max(14, min(24, 100.0 * (446.0 - 0.36 * mpx) / (75.0 * (len(slug) + 2)))))
    _setp(tsl, 'text', slug % (S['sheet'] % 10000))
    _setp(tsl, 'fontsizex', ssize)
    _setp(tsl, 'positiony', mpx * 0.5 - 11)
    lab = D.get('label') if D is not None else None
    tcp = op('t_cap')
    if lab:
        # a caption printed by the key plate, placed on the paper where the view will see it
        if lab['at'][0] == 'view':
            a = math.radians(rot0)
            lx, ly = lab['at'][1] * tk['zoom'], lab['at'][2] * tk['zoom']
            X, Y = cx0 + math.cos(a) * lx - math.sin(a) * ly, cy0 + math.sin(a) * lx + math.cos(a) * ly
        else:
            X, Y = lab['at'][1], lab['at'][2]
        ax, ay = lab.get('alignx', 'center'), lab.get('aligny', 'center')
        _setp(tcp, 'text', (lab.get('intext', lab['text']) if use_in else lab['text']).replace('|', chr(10)))
        _setp(tcp, 'fontsizex', lab.get('size', 24))
        _setp(tcp, 'alignx', ax)
        _setp(tcp, 'aligny', ay)
        _setp(tcp, 'positionx', round(X * 640.0 + {'left': 512.0, 'right': -512.0}.get(ax, 0.0), 1))
        _setp(tcp, 'positiony', round(Y * 640.0 + {'bottom': 320.0, 'top': -320.0}.get(ay, 0.0), 1))
    else:
        _setp(tcp, 'text', '')
    tp = op('typepack')
    _setu(tp, 'uScroll', (tk['rowscroll'][0] * evrow, tk['rowscroll'][1] * evrow, 0, 0))

    # ---- separation ----
    sep = op('sep')
    _setp(op('in_sel'), 'top', src_top.path if use_in else 'black')
    _setp(op('src_sw'), 'index', 1 if use_in else 0)
    _setu(sep, 'uIn', (1 if use_in else 0, 1 if D is not None else 0, 0, 0))
    _setu(sep, 'uLatch', latch)
    _setu(sep, 'uImg', (tk['margin'], tk['tiles'][0], tk['tiles'][1], (section * 0.37 + seed * 11.0) % 17.0))
    sun = tk['sun']
    _setu(sep, 'uSun', (sun[0] + (r4 - 0.5) * tk['sunjit'], sun[1] + (r1 - 0.5) * tk['sunjit'] * 0.6, sun[2] * (1 + 0.10 * energy + 0.22 * S['voc']), tk['outline']))
    for i, pl in enumerate(plates):
        wob = pl['wob']
        bigw = D['bigamt'] if (D is not None and 'bigamt' in D and pl['big'] > 0) else pl['big']
        scl, off = pl['scale'], pl['off']
        if use_in:
            bigw *= tk['inbig']
            if tk['inscale'] is not None:
                scl, off = tk['inscale'], (0.0, 0.0)
        _setu(sep, 'uPa%d' % i, (pl['src'], pl['mode'], bigw, pl['rows']))
        _setu(sep, 'uPb%d' % i, (pl['flood'], pl['grad'], scl, pl['ko']))
        _setu(sep, 'uPc%d' % i, (off[0] + wob * math.sin(evolve * 0.8 + i * 2.1 + seed * 6), off[1] + wob * 0.6 * math.cos(evolve * 0.6 + i * 1.3), math.radians(pl['prot']), pl['gamma']))
    _setu(sep, 'uAmt', [pl['amt'] for pl in plates])
    _setu(op('hold'), 'uLatch', (latchprev, 0, 0, 0))
    _setu(op('hold'), 'uLaid', laidmask)

    # ---- press ----
    pr = op('press')
    _setu(pr, 'uView', (cx, cy, zoom, math.radians(rotd)))
    _setu(pr, 'uFeed', (slide, tk['axis'], S['sheet'] % 1000, tk['gap']))
    _setu(pr, 'uLay', lay)
    _setu(pr, 'uRegA', S['pos'][0] + S['pos'][1])
    _setu(pr, 'uRegB', S['pos'][2] + S['pos'][3])
    iset = INKSETS[(section + int(seed * 23)) % len(INKSETS)]
    for i, pl in enumerate(plates):
        ink = iset[i] if (pl['swap'] and i < 3) else pl['ink']
        dens = pl['dens'] * ((1.0 - 0.35 * min(1.0, S['voc'])) if i == 1 else 1.0)
        _setu(pr, 'uPl%d' % i, (ink, pl['screen'], math.radians(pl['ang']), dens))
    _setu(pr, 'uInkB', [pl['inkb'] for pl in plates])
    _setu(pr, 'uCam', (tk['persp'], tk['pile'], tk['pilespread'][0], tk['pilespread'][1]))
    # after a cut the first pass still rolls onto blank paper (the arrival); later passes overprint
    _setu(pr, 'uMode', (1 if (tk['reprint'] and not S['fast']) else 0, tk['negalt'], 1 if D is not None else 0, 0))
    _setu(pr, 'uTone', (tk['freq'], gain, tk['rough'], tk['streak'] * (0.5 + 1.0 * energy)))
    _setu(pr, 'uFm', [pl['fm'] for pl in plates])
    _setu(pr, 'uPaper', tuple(tk['paper']) + (tk['opaque'],))
    _setu(pr, 'uBed', tuple(tk['bed']) + (tk['lanes'],))
    _setu(pr, 'uMisc', (tk['marks'], tk['margin'], evolve % 100.0, (section * 0.61 + seed * 7.0) % 13.0))
    _setu(pr, 'uFx', (tk['skew'], tk['colourway'], tk['misreg'], flash * tk['flash']))

    ctl = op('ctl')
    for i, v in enumerate((shot[0] % len(takes), S['sheet'], slide, lay[0], lay[1], lay[2], lay[3], sum(latch), gain,
                           math.hypot(*S['pos'][0]), math.hypot(*S['pos'][1]))):
        _setp(ctl, 'value%d' % i, float(v))


def onFrameStart(frame):
    par = parent().par
    hubc = op('/project1/sw_hub')
    on = par.Preview.eval()
    if hubc is not None:
        on = on or hubc.par.Solo.eval() or hubc.par.Scene.eval() == parent().name
    # Describe and Input are part of the shot: changing either re-exposes every plate at once
    shot = (int(par.Take.eval()), round(float(par.Seed.eval()), 5), round(float(par.Shotstart.eval()), 3),
            bool(par.Describe.eval()), str(par.Input.eval()).strip())
    if not on:
        S['last'] = -1e9      # the next frame on screen counts as a new shot
        return
    try:
        import time
        t0 = time.perf_counter()
        step(shot)
        S['ms'] = S.get('ms', 0.0) * 0.95 + (time.perf_counter() - t0) * 50.0   # smoothed, in ms
        _setp(op('ctl'), 'value11', S['ms'])
        if parent().fetch('driver_error', '') != '':
            parent().store('driver_error', '')
    except Exception as e:
        import traceback
        parent().store('driver_error', traceback.format_exc()[-900:])
    if on:
        op('hub').cook(force=True)
        op('out1').cook(force=True)
    return
