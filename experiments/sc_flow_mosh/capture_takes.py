# Capture every take of sc_flow_mosh without blocking TouchDesigner. Run inside TD:
#   g = {'op': op, 'td': td, 'run': run, 'absTime': absTime}
#   exec(open(project.folder + '/experiments/sc_flow_mosh/capture_takes.py', encoding='utf-8').read(), g)
#   g['schedule'](takes=range(7), seed=0.37, tag='take', delays=(26, 85), describe=False, inp='')
# Each take gets a shot of `gap` frames: Take, Seed and Shotstart are set (as the cutter
# does), then out1 is captured `delays` frames later. File names: captures/<tag>_<n>.png for
# the last delay, <tag>_<n>_a.png, _b.png ... for earlier ones. The feed at each capture is
# stored on the COMP: op('/project1/sc_flow_mosh').fetch('caplog').
SCENE = "/project1/sc_flow_mosh"
OUT = "experiments/sc_flow_mosh/captures/"

SET = """
s = op('%s')
s.par.Describe = %r; s.par.Input = %r
s.par.Take = %d; s.par.Seed = %r; s.par.Shotstart = absTime.seconds
"""

CAP = """
import tdh
s = op('%s')
h = s.op('hub'); c = s.op('ctl')
tdh.capture(s.op('out1').path, '%s', max_size=1280)
log = s.fetch('caplog', {})
log['%s'] = dict(take=int(s.par.Take.eval()), seed=round(float(s.par.Seed.eval()), 3), shot_age=round(float(s.op('shot')['age'][0]), 2),
    since_iframe=round(float(c['age'][0]), 2), t=round(float(h['t'][0]), 2), section=int(h['section'][0]),
    energy=round(float(h['energy'][0]), 2), hit_low=round(float(h['hit_low'][0]), 2), hit_mid=round(float(h['hit_mid'][0]), 2),
    vocals=round(float(h['vocals'][0]), 2), pulse=round(float(h['pulse'][0]), 2))
s.store('caplog', log)
"""


def schedule(takes=range(7), seed=0.37, tag="take", delays=(26, 85), gap=100, number=False,
             describe=False, inp="", start=0):
    """number=True names files by position in `takes` instead of by take (for seed sweeps).
    describe and inp set the COMP's Describe toggle and Input path for every shot.
    start delays the whole run by that many frames, so several runs can be queued."""
    if not start:
        op(SCENE).store("caplog", {})
    for i, n in enumerate(takes):
        sd = seed[i] if isinstance(seed, (list, tuple)) else seed
        run(SET % (SCENE, bool(describe), inp, n, sd), delayFrames=start + 1 + i * gap)
        for j, d in enumerate(delays):
            last = j == len(delays) - 1
            name = "%s_%d%s.png" % (tag, i if number else n, "" if last else "_" + "abcdef"[j])
            run(CAP % (SCENE, OUT + name, name), delayFrames=start + 1 + i * gap + d)
    return start + len(list(takes)) * gap
