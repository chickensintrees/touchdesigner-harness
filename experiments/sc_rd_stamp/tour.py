# Dev helper, run inside TouchDesigner: visit takes one after another and capture each.
#   g = {'op': op, 'td': td, 'TAKES': [0, 1, 2], 'SEED': 0.3, 'PREFIX': 'take_',
#        'AT': [(200, '')], 'EVERY': 240}
#   exec(open('<this file>').read(), g)
# Each take starts EVERY frames after the last; AT lists (frames after the cut, suffix).
# Files: captures/<PREFIX><take><suffix>.png. Results: op(scene).fetch('caps').
import td
_s = op('/project1/sc_rd_stamp')
_s.par.Preview = True
_s.store('caps', {})
_cut = '''
s = op('/project1/sc_rd_stamp')
s.par.Take = {take}
s.par.Seed = {seed}
s.par.Shotstart = absTime.seconds
'''
_cap = '''
import tdh
s = op('/project1/sc_rd_stamp')
h = s.op('hub')
ok = int(s.par.Take.eval()) == {take} and abs(s.par.Seed.eval() - {seed}) < 1e-6
tdh.capture('/project1/sc_rd_stamp/out1', 'experiments/sc_rd_stamp/captures/{name}.png', max_size=1280)
d = s.fetch('caps', {{}})
d['{name}'] = dict(take_held=ok, age=round(float(s.op('shot')['age']), 2),
    phrase=s.op('phrase').par.text.eval().replace(chr(10), ' / '),
    mat=float(s.op('ctl')['mat']),
    feed={{k: round(float(h[k]), 3) for k in ['t', 'energy', 'bass', 'section', 'section_pos', 'hit_low', 'hit_mid', 'hit_high']}})
s.store('caps', d)
'''
for _i, _t in enumerate(TAKES):
    _seed = SEED[_i] if isinstance(SEED, (list, tuple)) else SEED
    td.run(_cut.format(take=_t, seed=_seed), delayFrames=1 + _i * EVERY)
    for _f, _suf in AT:
        td.run(_cap.format(take=_t, seed=_seed, name='%s%d%s%s' % (PREFIX, _t, TAG[_i] if 'TAG' in globals() else '', _suf)), delayFrames=1 + _i * EVERY + _f)
r = 'scheduled'
