# cap2.py plus Describe and Input per shot (2026-11-11): SHOTS = [(take, seed, 'file.png', hold_seconds, describe, input_path), ...]
# Leaves Describe and Input as the last shot set them: set them back when you are done.
# Time-based capture helper for the MCP bridge (nothing in the scene depends on it).
# The shared instance swings between 5 and 60 cooked frames a second, so cap.py's frame counts
# give anything from 0.2 s to 20 s per shot. This one waits in seconds.
# Before exec, define SHOTS = [(take, seed, 'file.png', hold_seconds), ...]; optional SIZE, NEWSHOT (default True:
# a new Shotstart per shot; False keeps the shot running so two captures show one shot at two moments).
# Results (the feed at each capture) land in comp storage 'caps'.
SCENE = '/project1/sc_vector_scope'
_s = op(SCENE)
for _r in list(td.runs):                 # drop this helper's own pending calls only
    try:
        _src = _r.source or ''
        if "op('/project1/sc_vector_scope')" in _src and ('capq' in _src or 'tdh.capture' in _src or 's.par.Shotstart = absTime' in _src):
            _r.kill()
    except Exception:
        pass
_s.store('caps', {})
_s.store('capq', [dict(take=a, seed=b, file=c, hold=d, t0=None, desc=e, inp=f) for a, b, c, d, e, f in SHOTS])
_s.store('capsize', globals().get('SIZE', 1280))
_s.store('capnew', globals().get('NEWSHOT', True))
TICK = '''
import tdh
s = op('/project1/sc_vector_scope')
q = s.fetch('capq', [])
if q:
    j = q[0]
    s.par.Preview = True
    s.par.Take = j['take']; s.par.Seed = j['seed']; s.par.Describe = j['desc']; s.par.Input = j['inp']
    if j['t0'] is None:
        j['t0'] = absTime.seconds
        if s.fetch('capnew', True) or s.fetch('caplast', None) != (j['take'], j['seed'], j['desc'], j['inp']):
            s.par.Shotstart = absTime.seconds
        s.store('caplast', (j['take'], j['seed'], j['desc'], j['inp']))
        j['ss'] = s.par.Shotstart.eval()
    else:
        s.par.Shotstart = j['ss']
        if absTime.seconds - j['t0'] >= j['hold']:
            h = s.op('hub')
            tdh.capture(s.op('out1').path, 'experiments/sc_vector_scope/captures/' + j['file'], max_size=s.fetch('capsize', 1280))
            d = s.fetch('caps', {})
            d[j['file']] = dict((k, round(float(h[k]), 3)) for k in ('t', 'energy', 'rms', 'hit_low', 'hit_mid', 'hit_high', 'hits_low', 'pulse', 'beat_pos', 'section', 'vocals', 'bass'))
            d[j['file']]['seckick'] = round(float(s.op('path').par.vec8valuew.eval()), 3)
            d[j['file']]['step'] = round(absTime.stepSeconds, 3)
            s.store('caps', d)
            q.pop(0)
    s.store('capq', q)
    if q:
        run(s.fetch('captick'), delayFrames=1)
'''
_s.store('captick', TICK)
run(TICK, delayFrames=1)
queued = len(SHOTS)
