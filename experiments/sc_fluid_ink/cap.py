# Dev helper, run inside TouchDesigner: capture out1 and return the feed at that moment.
# Optional globals: NAME (capture name), TAKE, SEED (set before capture; with RESTART the shot restarts)
#   g = {'op': op, 'absTime': absTime, 'NAME': '03a'}; exec(open('<this file>').read(), g); r = g['r']
import tdh
_s = op('/project1/sc_fluid_ink')
_h = _s.op('hub')
r = {}
if 'TAKE' in globals():
    if int(_s.par.Take.eval()) != TAKE or ('SEED' in globals() and abs(_s.par.Seed.eval() - SEED) > 1e-6) or globals().get('RESTART'):
        _s.par.Take = TAKE
        if 'SEED' in globals():
            _s.par.Seed = SEED
        _s.par.Shotstart = absTime.seconds
        r['restarted'] = True
if 'NAME' in globals():
    tdh.capture('/project1/sc_fluid_ink/out1', 'experiments/sc_fluid_ink/captures/%s.png' % NAME, max_size=1280)
r.update({'err': str(tdh.errors('/project1/sc_fluid_ink')),
     'take': int(_s.par.Take.eval()), 'seed': round(float(_s.par.Seed.eval()), 3), 'age': round(float(_s.op('shot')['age']), 2),
     'cooks': int(_s.op('dye').totalCooks),
     'feed': {k: round(float(_h[k]), 3) for k in ['t', 'energy', 'bass', 'vocals', 'pitch', 'section', 'hit_low', 'hit_mid', 'hit_high', 'hits_low', 'pulse']},
     'phrase': _s.op('phrase').par.text.eval().replace('\n', ' / ')})
