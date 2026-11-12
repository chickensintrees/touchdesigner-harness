# Describe / Input pass helper (2026-11-11). Used through execute_python_script:
#   exec(open(project.folder + '/experiments/sc_shatter/dx.py', encoding='utf-8').read()); r = shots([...])
# One call can only render one state, so every shot is two scheduled jobs: set the state, then
# (a few frames later, so the shadow map is current) set it again and capture.
import tdh

_HERE = project.folder + '/experiments/sc_shatter'  # the repository is where the open project is saved

_SET = '''
s = op('/project1/sc_shatter')
s.par.Take = {take}; s.par.Seed = {seed}; s.par.Subject = {subject}
s.par.Manual = {manual}; s.par.Phase = {phase}
s.par.Describe = {describe}; s.par.Input = {inp!r}
s.par.Shotstart = absTime.seconds - {age}
'''

_CAP = _SET + '''
import tdh
s.op('out1').cook(force=True)
tdh.capture(s.op('out1').path, 'experiments/sc_shatter/captures/{name}', max_size={size})
h = s.op('hub')
d = s.fetch('seq', {{}})
e = dict((k, round(float(h[k]), 3)) for k in ('t', 'bar_pos', 'energy', 'section', 'hit_low'))
e['q'] = round(float(s.op('ctl')['q']), 3)
e['subj'] = int(s.op('ctl')['subj'])
d['{name}'] = e
s.store('seq', d)
'''


def shots(jobs, size=1280, gap=10, settle=6):
    """jobs: dicts with name and any of take, seed, phase (None = live), subject, describe, inp, age."""
    s = op('/project1/sc_shatter')
    s.par.Preview = True
    s.store('seq', {})
    for i, j in enumerate(jobs):
        phase = j.get('phase', 0.3)
        kw = dict(take=j.get('take', 0), seed=j.get('seed', 0.3), subject=j.get('subject', -1),
                  manual=(phase is not None), phase=(phase if phase is not None else 0.3),
                  describe=bool(j.get('describe', False)), inp=j.get('inp', ''), age=j.get('age', 10.0),
                  name=j['name'], size=size)
        run(_SET.format(**kw), delayFrames=1 + i * gap)
        run(_CAP.format(**kw), delayFrames=1 + i * gap + settle)
    return len(jobs)


def got():
    s = op('/project1/sc_shatter')
    d = s.fetch('seq', {})
    return '\n'.join('%s %s' % (k, v) for k, v in sorted(d.items()))


def rebuild():
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(_HERE + '/build.py', encoding='utf-8').read(), g)
    path = g['build']()
    s = op(path)
    s.par.Preview = True
    s.op('out1').cook(force=True)
    return str({'path': path, 'baked': str(s.fetch('baked_now', None)), 'errors': str(tdh.errors(path))})
