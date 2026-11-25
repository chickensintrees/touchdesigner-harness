# Development helpers (run inside TouchDesigner through execute_python_script):
#   g = {'op': op, 'td': td, 'run': run}
#   exec(open(project.folder + '/experiments/sc_exploded_view/dev.py', encoding='utf-8').read(), g); r = g['rebuild']()
import td
import tdh
HERE = td.project.folder.replace(chr(92), '/') + '/experiments/sc_exploded_view'
P = '/project1/sc_exploded_view'


def rebuild():
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(HERE + '/build.py', encoding='utf-8').read(), g)
    return g['build']()


def shot(take, seed=0.0, age=5.0):
    s = op(P)
    s.par.Take = take
    s.par.Seed = seed
    s.par.Shotstart = td.absTime.seconds - age
    s.par.Preview = True


def mode(describe=False, inp=''):
    """Describe toggle and Input path (blank = the scene's own picture)."""
    s = op(P)
    s.par.Describe = bool(describe)
    s.par.Input = inp


def status():
    s = op(P)
    r = {'errors': str(tdh.errors(P))[:2500]}
    for n in ('part_info', 'draw_info'):
        t = s.op(n).text
        if 'ERROR' in t or 'rror' in t:
            r[n] = t[:2500]
    h = s.op('hub')
    r['feed'] = {k: round(float(h[k]), 2) for k in ('t', 'section', 'bar', 'energy', 'hit_low', 'pulse')}
    r['shot'] = [int(s.par.Take), round(float(s.par.Seed), 3)]
    return r


def cap(name, take=None, seed=None, age=5.0):
    if take is not None:
        shot(take, seed or 0.0, age)
    op(P + '/out1').cook(force=True)
    tdh.capture(P + '/out1', 'experiments/sc_exploded_view/captures/' + name, max_size=1280)
    return status()


def takes(prefix='take_', seed=0.0, which=None):
    n = len(op(P + '/logic').module.TAKES)
    out = {}
    for t in (which or range(n)):
        shot(t, seed)
        op(P + '/out1').cook(force=True)
        tdh.capture(P + '/out1', 'experiments/sc_exploded_view/captures/' + prefix + str(t) + '.png', max_size=1280)
        out[t] = int(op(P + '/ctl')['take'])
    r = status()
    r['takes'] = str(out)
    return r


def burst(prefix, take, seed=0.0, n=6, gap=20, age0=None):
    """Schedule n captures 'gap' frames apart (returns at once; read op(P).fetch('burst') afterwards)."""
    s = op(P)
    s.store('burst', {})
    if age0 is not None:
        shot(take, seed, age0)
    for i in range(n):
        code = (
            "import tdh\n"
            "s = op('%s')\n"
            "s.par.Take = %d; s.par.Seed = %r; s.par.Preview = True\n"
            "s.op('out1').cook(force=True)\n"
            "tdh.capture('%s/out1', 'experiments/sc_exploded_view/captures/%s%d.png', max_size=1280)\n"
            "h = s.op('hub'); b = s.fetch('burst', {})\n"
            "b[%d] = {k: round(float(h[k]), 2) for k in ('t', 'section', 'bar', 'beat', 'energy', 'hit_low', 'hit_mid', 'pulse')}\n"
            "b[%d]['E'] = round(float(s.op('ctl')['E']), 2); b[%d]['age'] = round(float(s.op('shot')['age']), 2)\n"
            "s.store('burst', b)\n"
        ) % (P, take, seed, P, prefix, i, i, i, i)
        run(code, delayFrames=2 + i * gap)
    if age0 is None:
        shot(take, seed)
    return 'scheduled'
