# Capture helper (nothing in the scene depends on it): waits for the next section change and
# captures out1 on N cooked frames from it, so the section kick can be seen in stills.
# Before exec: TAKE, SEED, PREFIX ('sec_'), optional N (default 6). Feed per capture lands in comp storage 'seccaps'.
_s = op('/project1/sc_vector_scope')
_s.store('seccaps', {})
_s.store('secjob', dict(take=TAKE, seed=SEED, prefix=PREFIX, n=globals().get('N', 6), sec=None, got=0, t0=absTime.seconds, ss=absTime.seconds))
TICK = '''
import tdh
s = op('/project1/sc_vector_scope')
j = s.fetch('secjob', None)
if j is not None:
    h = s.op('hub')
    s.par.Preview = True
    s.par.Take = j['take']; s.par.Seed = j['seed']; s.par.Shotstart = j['ss']
    sec = int(h['section'])
    if j['sec'] is None:
        j['sec'] = sec
    go = j['got'] > 0 or (sec != j['sec'] and absTime.seconds - j['t0'] > 1.5)
    if absTime.seconds - j['t0'] > 25:
        j = None
    elif go:
        f = '%s%d.png' % (j['prefix'], j['got'])
        tdh.capture(s.op('out1').path, 'experiments/sc_vector_scope/captures/' + f, max_size=960)
        d = s.fetch('seccaps', {})
        d[f] = dict(t=round(float(h['t']), 3), section=sec, kick=round(float(s.op('path').par.vec8valuew.eval()), 3),
                    hit_low=round(float(h['hit_low']), 3), step=round(absTime.stepSeconds, 3))
        s.store('seccaps', d)
        j['got'] += 1
        if j['got'] >= j['n']:
            j = None
    else:
        j['sec'] = sec
    s.store('secjob', j)
    if j is not None:
        run(s.fetch('sectick'), delayFrames=1)
'''
_s.store('sectick', TICK)
run(TICK, delayFrames=1)
started = True
