# Review helper (2026-11-11): set Take / Seed / Describe / Input, capture, return the feed read in the same call.
#     g = {'op': op, 'absTime': absTime}
#     exec(open(project.folder + '/experiments/sc_kifs_office/dcap.py').read(), g); r = g['cap']('d_take0', 0, 0.3, describe=1)
# The cutter may change Take and Seed between calls, so everything is set here, right before the capture.
import tdh

S = '/project1/sc_kifs_office'


def cap(name, take, seed, describe=0, inp='', age=5.0, size=1280):
    s = op(S)
    s.par.Preview = True
    s.par.Take = take
    s.par.Seed = seed
    s.par.Describe = bool(describe)
    s.par.Input = inp
    s.par.Shotstart = absTime.seconds - age
    h = op(S + '/hub')
    g = op(S + '/kifs')
    g.cook(force=True)
    tdh.capture(S + '/out1', 'experiments/sc_kifs_office/captures/%s.png' % name, max_size=size)
    r = {k: round(float(h[k]), 3) for k in ('t', 'section', 'hit_low', 'hit_mid', 'hit_high', 'bar_pulse')}
    r['ring'] = round(float(op(S + '/ring')[0]), 3)
    r['gpu_ms'] = round(float(g.gpuCookTime), 2)
    r['err'] = str(tdh.errors(S))
    return r


def many(prefix, jobs, describe=0, inp='', size=1280):
    out = {}
    for take, seed in jobs:
        out['%s%d' % (prefix, take)] = str(cap('%s%d' % (prefix, take), take, seed, describe, inp, size=size))
    return out
