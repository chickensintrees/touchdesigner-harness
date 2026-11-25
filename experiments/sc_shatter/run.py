# Helper used through execute_python_script while developing:
#   exec(open(project.folder + '/experiments/sc_shatter/run.py', encoding='utf-8').read()); r = rebuild()
# and for stills: shot(take, seed, phase, subject, 'name.png')
import tdh

_HERE = project.folder + '/experiments/sc_shatter'  # the repository is where the open project is saved


def rebuild():
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(_HERE + '/build.py', encoding='utf-8').read(), g)
    path = g['build']()
    s = op(path)
    s.op('out1').cook(force=True)
    return {'path': path, 'baked': str(s.fetch('baked_now', None)), 'errors': str(tdh.errors(path))}


def setup(take=0, seed=0.0, phase=None, subject=-1):
    s = op('/project1/sc_shatter')
    s.par.Take = take
    s.par.Seed = seed
    s.par.Subject = subject
    s.par.Manual = phase is not None
    if phase is not None:
        s.par.Phase = phase
    s.par.Shotstart = absTime.seconds - 10
    return s


def shot(take=0, seed=0.0, phase=None, subject=-1, name=None, max_size=1280):
    s = setup(take, seed, phase, subject)
    s.op('out1').cook(force=True)
    out = None
    if name:
        out = tdh.capture(s.op('out1').path, 'experiments/sc_shatter/captures/' + name, max_size=max_size)
    h = s.op('hub')
    feed = {k: round(float(h[k]), 3) for k in ('t', 'bar', 'energy', 'section', 'hit_low', 'pulse')}
    return {'file': str(out), 'feed': feed, 'subj': int(s.op('ctl')['subj']), 'q': round(float(s.op('ctl')['q']), 3),
            'errors': str(tdh.errors(s.path))}


def sheet_setup(take, phase, seed=0.0, subject=-1):
    """Set a state now; capture it in a LATER call (one call renders one state)."""
    setup(take, seed, phase, subject)
    return {'take': take, 'phase': phase}


def strip(take, phases, seed=0.0, subject=-1, prefix='x', max_size=640):
    out = []
    for q in phases:
        x = shot(take, seed, q, subject, '%s_t%d_q%03d.png' % (prefix, take, int(round(q * 100))), max_size)
        out.append(x['errors'] + ' subj %d' % x['subj'])
    return out


_SEQ = '''
import tdh
s = op('/project1/sc_shatter')
s.par.Take = {take}; s.par.Seed = {seed}; s.par.Subject = {subject}; s.par.Manual = False
s.op('out1').cook(force=True)
tdh.capture(s.op('out1').path, 'experiments/sc_shatter/captures/{name}', max_size=640)
h = s.op('hub')
d = s.fetch('seq', {{}})
d['{name}'] = dict((k, round(float(h[k]), 3)) for k in ('t', 'bar_pos', 'energy', 'section', 'hit_low', 'hit_high', 'pulse', 'vocals'))
d['{name}']['q'] = round(float(s.op('ctl')['q']), 3)
d['{name}']['age'] = round(float(s.op('shot')['age']), 2)
d['{name}']['subj'] = int(s.op('ctl')['subj'])
s.store('seq', d)
'''


def seq(take, seed, subject, prefix, delays, fresh_cut=True):
    """Live captures at several frame delays from now (one call cannot hold more than one moment)."""
    s = op('/project1/sc_shatter')
    s.par.Take = take
    s.par.Seed = seed
    s.par.Subject = subject
    s.par.Manual = False
    s.par.Shotstart = absTime.seconds if fresh_cut else absTime.seconds - 10
    s.store('seq', {})
    names = []
    for i, d in enumerate(delays):
        name = '%s_%d.png' % (prefix, i)
        names.append(name)
        run(_SEQ.format(take=take, seed=seed, subject=subject, name=name), delayFrames=d)
    return names
