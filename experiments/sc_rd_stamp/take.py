# Dev helper, run inside TouchDesigner: start a shot (Take, Seed, Shotstart = now) and
# capture out1 some frames later, with the feed at that moment kept in the COMP's storage.
#   g = {'op': op, 'td': td, 'TAKE': 2, 'SEED': 0.3, 'SHOTS': [('take_2', 150)]}
#   exec(open('<this file>').read(), g)
# then, a few seconds later:  op('/project1/sc_rd_stamp').fetch('caps')
# SHOTS is a list of (capture name, frames after the cut). The cutter may change Take
# while this waits, so each capture re-asserts Take and Seed and reports what it saw.
import td
_s = op('/project1/sc_rd_stamp')
_s.par.Preview = True
_s.par.Take = TAKE
_s.par.Seed = SEED
_s.par.Shotstart = td.absTime.seconds
_s.store('caps', {})
_code = '''
import tdh
s = op('/project1/sc_rd_stamp')
h = s.op('hub')
ok = int(s.par.Take.eval()) == {take} and abs(s.par.Seed.eval() - {seed}) < 1e-6
tdh.capture('/project1/sc_rd_stamp/out1', 'experiments/sc_rd_stamp/captures/{name}.png', max_size=1280)
d = s.fetch('caps', {{}})
d['{name}'] = dict(take_held=ok, age=round(float(s.op('shot')['age']), 2),
    phrase=s.op('phrase').par.text.eval().replace(chr(10), ' / '),
    ctl={{c.name: round(float(c[0]), 3) for c in s.op('ctl').chans()}},
    feed={{k: round(float(h[k]), 3) for k in ['t', 'energy', 'bass', 'vocals', 'section', 'section_pos', 'hit_low', 'hit_mid', 'hit_high', 'pulse']}})
s.store('caps', d)
'''
for _name, _frames in SHOTS:
    td.run(_code.format(take=TAKE, seed=SEED, name=_name), delayFrames=_frames)
r = 'scheduled'
