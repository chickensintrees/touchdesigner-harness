# Dev helper, run inside TouchDesigner: capture out1 and return the feed at that moment.
#   g = {'op': op, 'NAME': '03a'}; exec(open('<this file>').read(), g); r = g['r']
import tdh
_s = op('/project1/sc_rd_stamp')
_h = _s.op('hub')
tdh.capture('/project1/sc_rd_stamp/out1', 'experiments/sc_rd_stamp/captures/%s.png' % NAME, max_size=1280)
r = {'err': str(tdh.errors('/project1/sc_rd_stamp')),
     'ctl': {c.name: round(float(c[0]), 3) for c in _s.op('ctl').chans()},
     'feed': {k: round(float(_h[k]), 3) for k in ['t', 'energy', 'bass', 'vocals', 'section', 'section_pos', 'hit_low', 'hit_mid', 'hit_high', 'hits_low', 'pulse', 'beat_pos']},
     'phrase': _s.op('phrase').par.text.eval().replace('\n', ' / ')}
