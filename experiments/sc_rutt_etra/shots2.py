# Like shots.py, but each shot also sets Describe and Input. Call from execute_python_script:
#   g = {'op': op, 'td': td, 'run': run, 'absTime': absTime}
#   exec(open('<repo>/experiments/sc_rutt_etra/shots2.py', encoding='utf-8').read(), g)
#   g['shoot']([(name, take, seed, describe, input_path), ...])
# The last shot leaves Describe off and Input blank. Feed values land in storage 'shots'.
SCENE = '/project1/sc_rutt_etra'
GAP = 45

SET = """
s = op('%s')
s.par.Take = %d
s.par.Seed = %r
s.par.Describe = %r
s.par.Input = %r
s.par.Shotstart = absTime.seconds - 5.0
"""
CAP = """
import tdh
s = op('%s')
h = s.op('hub')
tdh.capture(s.op('out1').path, 'experiments/sc_rutt_etra/captures/%s.png', max_size=1280)
d = s.fetch('shots', {})
d['%s'] = dict((n, round(float(h[n]), 3)) for n in ('t', 'bass', 'energy', 'hit_low', 'hit_mid', 'hit_high', 'section', 'section_pos'))
d['%s']['take'] = int(s.par.Take)
d['%s']['label'] = s.op('label').par.text.eval()
d['%s']['text'] = s.op('text').par.text.eval()
s.store('shots', d)
if %r:
    s.par.Describe = False
    s.par.Input = ''
"""


def shoot(shots, gap=GAP):
    op(SCENE).store('shots', {})
    for i, (name, take, seed, desc, inp) in enumerate(shots):
        run(SET % (SCENE, take, seed, bool(desc), inp), delayFrames=1 + i * gap)
        run(CAP % (SCENE, name, name, name, name, name, i == len(shots) - 1), delayFrames=1 + i * gap + gap - 3)
    return len(shots) * gap
