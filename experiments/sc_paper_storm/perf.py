# Measure each take's own cook cost. exec this file's text inside TouchDesigner, wait ~6 s, then read
# op('/project1/sc_paper_storm').fetch('perf'). Each take is held for 40 frames and measured on the last.
# (Sum of cpuCookTime + gpuCookTime over every operator in the scene that cooked in the last 2 frames;
# File In POPs and Movie File Ins are left out because their cpuCookTime keeps the load-time value.)
SC = '/project1/sc_paper_storm'
SET = "op('%s').par.Take = %d; op('%s').par.Seed = 0.4"
MEAS = '''
s = op('%s')
cpu = gpu = 0.0; n = 0; worst = []
for o in s.findChildren(maxDepth=3):
    if o.OPType in ('fileinPOP', 'moviefileinTOP'):
        continue
    if absTime.frame - o.cookAbsFrame > 2:
        continue
    c = o.cpuCookTime; g = getattr(o, 'gpuCookTime', 0.0) or 0.0
    cpu += c; gpu += g; n += 1
    worst.append((round(c + g, 3), o.name))
worst.sort(reverse=True)
d = s.fetch('perf', {})
d[%d] = (round(cpu, 2), round(gpu, 2), n, worst[:4], round(float(s.op('bloom').gpuCookTime), 3))
s.store('perf', d)
'''
op(SC).store('perf', {})
for i in range(8):
    run(SET % (SC, i, SC), delayFrames=1 + i * 40)
    run(MEAS % (SC, i), delayFrames=38 + i * 40)
started = True
