# Per-take cook cost of sc_flow_mosh, without blocking TouchDesigner. Run inside TD:
#   g = {'op': op, 'td': td, 'run': run, 'absTime': absTime}
#   exec(open(project.folder + '/experiments/sc_flow_mosh/measure_takes.py', encoding='utf-8').read(), g)
#   g['schedule']()          # then, a few seconds later: op('/project1/sc_flow_mosh').fetch('cost')
# For each take: sets Take, waits, then sums cpuCookTime and gpuCookTime (ms) of every
# operator that cooked within the last 3 frames, three samples 10 frames apart.
SCENE = "/project1/sc_flow_mosh"

SET = "s = op('%s'); s.par.Take = %d; s.par.Seed = 0.37; s.par.Shotstart = absTime.seconds"

MEAS = """
s = op('%s')
cpu = 0.0; gpu = 0.0; top = []
for o in s.findChildren(maxDepth=2):
    if absTime.frame - o.cookAbsFrame > 3:
        continue
    c = float(o.cpuCookTime); g = float(getattr(o, 'gpuCookTime', 0.0) or 0.0)
    cpu += c; gpu += g; top.append((round(c + g, 3), o.name))
cost = s.fetch('cost', {})
cost.setdefault(%d, []).append(dict(take=int(s.par.Take.eval()), cpu=round(cpu, 3), gpu=round(gpu, 3), top=sorted(top, reverse=True)[:4]))
s.store('cost', cost)
"""


def schedule(takes=range(7), gap=70):
    op(SCENE).store("cost", {})
    for i, n in enumerate(takes):
        run(SET % (SCENE, n), delayFrames=1 + i * gap)
        for d in (40, 50, 60):
            run(MEAS % (SCENE, n), delayFrames=1 + i * gap + d)
    return len(list(takes)) * gap
