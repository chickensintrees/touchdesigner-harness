# Capture every take without blocking TouchDesigner: schedules "set take" and "capture"
# on later frames with run(). Call from execute_python_script:
#   g = {'op': op, 'td': td, 'run': run, 'absTime': absTime}
#   exec(open('<repo>/experiments/sc_rutt_etra/shots.py', encoding='utf-8').read(), g)
#   g['shoot'](takes=range(8), seed=0.3, prefix='take_')
# Results (feed values at each capture) land in the scene COMP's storage under 'shots'.
SCENE = '/project1/sc_rutt_etra'
GAP = 45      # frames between takes: long enough for the feedback loop to develop

SET = """
s = op('%s')
s.par.Take = %d
s.par.Seed = %r
s.par.Shotstart = absTime.seconds - %r
"""
CAP = """
import tdh
s = op('%s')
h = s.op('hub')
tdh.capture(s.op('out1').path, 'experiments/sc_rutt_etra/captures/%s.png', max_size=%d)
d = s.fetch('shots', {})
d['%s'] = dict((n, round(float(h[n]), 3)) for n in ('t', 'bass', 'energy', 'hit_low', 'hit_mid', 'hit_high', 'pulse', 'bar_pulse', 'section', 'beat', 'hits_low', 'vocals'))
d['%s']['take'] = int(s.par.Take)
s.store('shots', d)
"""


def shoot(takes=range(8), seed=0.3, prefix='take_', age=5.0, size=1280, names=None, wait=None):
    op(SCENE).store('shots', {})
    gap = wait or GAP
    for i, t in enumerate(takes):
        name = names[i] if names else '%s%d' % (prefix, t)
        sd = seed[i] if isinstance(seed, (list, tuple)) else seed
        run(SET % (SCENE, t, sd, age), delayFrames=1 + i * gap)
        run(CAP % (SCENE, name, size, name, name), delayFrames=1 + i * gap + gap - 3)
    return len(list(takes)) * gap


def burst(take, seed, frames, prefix, size=1280):
    """One shot from its first frame: set the take now (age 0), capture at the given frame delays."""
    op(SCENE).store('shots', {})
    run(SET % (SCENE, take, seed, 0.0), delayFrames=1)
    for f in frames:
        name = '%s%03d' % (prefix, f)
        run(CAP % (SCENE, name, size, name, name), delayFrames=1 + f)
    return max(frames)
