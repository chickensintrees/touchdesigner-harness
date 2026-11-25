# Review helper: set Take / Seed / shot age on the scene, capture, and return the feed read in the same call.
#     g = {'op': op, 'absTime': absTime}
#     exec(open(project.folder + '/experiments/sc_kifs_office/take_cap.py').read(), g); r = g['cap']('take_0', 0, 0.3)
# The cutter may change Take and Seed between calls, so they are always set here, right before the capture.
import tdh

S = '/project1/sc_kifs_office'


def cap(name, take, seed, age=5.0, size=1280):
    s = op(S)
    s.par.Preview = True
    s.par.Take = take
    s.par.Seed = seed
    s.par.Shotstart = absTime.seconds - age
    h = op(S + '/hub')
    g = op(S + '/kifs')
    g.cook(force=True)
    tdh.capture(S + '/out1', 'experiments/sc_kifs_office/captures/%s.png' % name, max_size=size)
    r = {k: round(float(h[k]), 3) for k in ('t', 'energy', 'section', 'beat', 'hit_low', 'hit_mid', 'hit_high',
                                             'bar_pulse', 'pulse')}
    r['fold'] = str([round(float(g.par.vec1valuex.eval()), 3), round(float(g.par.vec1valuey.eval()), 3)])
    r['ring'] = round(float(op(S + '/ring')[0]), 3)
    r['gpu_ms'] = round(float(g.gpuCookTime), 2)
    r['cpu_ms'] = round(float(g.cpuCookTime), 3)
    r['mean'] = str(tdh.stats(S + '/out1'))[:160]
    r['err'] = str(tdh.errors(S))
    return r
