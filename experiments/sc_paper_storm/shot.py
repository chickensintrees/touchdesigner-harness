# Helper for looking: capture out1 to captures/<name>.png and return the feed at that moment.
# Use: exec(open(...shot.py).read()); r = shot('05_auto', take=3, seed=0.4)
# take/seed (and Describe/Input) are set in the same call because the cutter changes them while we work.
import tdh
TESTCARD = '/project1/sw_testcard/out1'
def shot(name, take=None, seed=None, size=1280, age=None, describe=None, inp=None):
    s = op('/project1/sc_paper_storm')
    if take is not None:
        s.par.Take = take
    if seed is not None:
        s.par.Seed = seed
    if age is not None:   # pretend the cut was this many seconds ago
        s.par.Shotstart = absTime.seconds - age
    if describe is not None:
        s.par.Describe = bool(describe)
    if inp is not None:   # '' = the scene's own source
        s.par.Input = inp
    s.op('out1').cook(force=True)
    tdh.capture(s.op('out1').path, 'experiments/sc_paper_storm/captures/%s.png' % name, max_size=size)
    h = s.op('hub')
    keys = ('t', 'section', 'beat', 'bar_pos', 'energy', 'hit_low', 'hit_mid', 'hit_high', 'bass')
    d = {k: round(float(h[k][0]), 3) for k in keys}
    d['take'] = int(s.par.Take.eval()); d['seed'] = round(float(s.par.Seed.eval()), 3)
    d['age'] = round(float(s.op('shot')['age'][0]), 2)
    d['kick'] = round(float(s.op('ctl')['kick'][0]), 3)
    d['ring'] = round(float(s.op('ctl')['ring'][0]), 3)
    d['describe'] = int(s.op('mode')['describe'][0]); d['inp'] = int(s.op('mode')['inp'][0])
    d['err'] = str(tdh.errors(s.path))
    return d
