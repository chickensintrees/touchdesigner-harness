# Dev helper, run inside TouchDesigner: capture a list of shots one after another without
# blocking. JOBS = [(name, take, seed, when), ...]; when is 'full' (all plates down, paper
# still), 'roll', 'slide', 'kick', 'arrive', 'keep:<seconds>' (same shot) or 'now'. Results land in
# op('/project1/sc_riso_press').fetch('batch') as {name: info}; 'batch_done' turns True.
#   g = {'op': op, 'run': run, 'absTime': absTime, 'JOBS': [...]}; exec(open('<this file>').read(), g)
import tdh

_s = op('/project1/sc_riso_press')
_s.par.Preview = True
_s.par.Describe = bool(globals().get('DESCRIBE', False))     # optional globals: DESCRIBE, INPUT
_s.par.Input = globals().get('INPUT', '')
_s.store('batch', {})
_s.store('batch_done', False)
_minage = globals().get('MINAGE', 1.0)
_size = globals().get('SIZE', 1280)
_st = {'i': -1, 't0': 0.0, 'n': 0}
# a newer batch (or a rebuild, which clears storage) retires this one: two batches fight over Take
_id = absTime.frame
_s.store('batch_id', _id)


def _next():
    if _s.fetch('batch_id', None) != _id:
        return
    _st['i'] += 1
    if _st['i'] >= len(JOBS):
        _s.store('batch_done', True)
        return
    name, take, seed, when = JOBS[_st['i']]
    _s.par.Take = take
    _s.par.Seed = seed
    if not str(when).startswith('keep'):      # 'keep:0.2' = same shot, 0.2 s after the last capture
        _s.par.Shotstart = absTime.seconds
    _st['t0'] = absTime.seconds
    _st['n'] = 600
    run("args[0]()", _poll, delayFrames=2)


def _poll():
    if _s.fetch('batch_id', None) != _id:
        return
    name, take, seed, when = JOBS[_st['i']]
    # the cutter may be driving this scene too: put the shot back
    if int(_s.par.Take.eval()) != take or abs(float(_s.par.Seed.eval()) - seed) > 1e-6:
        _s.par.Take = take
        _s.par.Seed = seed
    c = _s.op('ctl')
    h = _s.op('hub')
    age = absTime.seconds - _st['t0']
    lays = [float(c['lay%d' % i]) for i in range(4)]
    sl = float(c['slide'])
    if when == 'full':
        ok = min(lays) >= 1 and sl == 0 and age > _minage
    elif when == 'roll':
        ok = any(0.25 < v < 0.75 for v in lays) and age > _minage
    elif when == 'slide':
        ok = 0.15 < sl < 0.7
    elif when == 'kick':
        ok = min(lays) >= 1 and sl == 0 and age > _minage and max(float(c['reg0']), float(c['reg1'])) > 0.006
    elif str(when).startswith('keep'):
        ok = age > float(when.split(':')[1])
    elif when == 'arrive':
        ok = age > 0.2
    else:
        ok = age > _minage
    _st['n'] -= 1
    if ok or _st['n'] <= 0:
        tdh.capture(_s.path + '/out1', 'experiments/sc_riso_press/captures/%s.png' % name, max_size=_size)
        b = _s.fetch('batch')
        b[name] = {'ok': bool(ok), 'take': take, 'seed': seed,
                   'ctl': {ch.name: round(float(ch[0]), 3) for ch in c.chans()},
                   'feed': {k: round(float(h[k]), 3) for k in ['t', 'energy', 'bass', 'section', 'hit_low', 'hit_mid', 'hit_high', 'hits_low', 'vocals', 'beat', 'pulse', 'beat_pos']},
                   'err': _s.fetch('driver_error', '')}
        _s.store('batch', b)
        run("args[0]()", _next, delayFrames=1)
    else:
        run("args[0]()", _poll, delayFrames=1)


_next()
