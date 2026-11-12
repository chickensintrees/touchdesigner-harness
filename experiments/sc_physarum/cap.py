# Dev helper, run inside TouchDesigner: capture out1 and return the feed at that moment.
#   g = {'op': op, 'NAME': '03a'}; exec(open('<this file>').read(), g); r = g['r']
import tdh
_s = op('/project1/sc_physarum')
_h = _s.op('hub')
tdh.capture('/project1/sc_physarum/out1', 'experiments/sc_physarum/captures/%s.png' % NAME, max_size=1280)
r = str({'err': tdh.errors('/project1/sc_physarum'),
     'take': int(_s.par.Take), 'seed': round(float(_s.par.Seed), 3), 'age': round(float(_s.op('shot')['age']), 2),
     'ev': {c.name: round(float(c[0]), 3) for c in _s.op('ev').chans()},
     'species': [round(float(_s.op('agents').par['vec0value' + c].eval()), 3) for c in 'xyzw'],
     'feed': {k: round(float(_h[k]), 3) for k in ['t', 'energy', 'bass', 'vocals', 'other', 'drums', 'section', 'section_pos', 'hit_low', 'hit_mid', 'hit_high', 'pulse']}})
