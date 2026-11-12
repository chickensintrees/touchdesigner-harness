# Review tool, not part of the scene: when a feed condition comes true, capture every take in that one frame.
# A temporary Execute DAT inside the scene's own COMP watches the feed, captures once and switches itself off.
#     g = {'op': op, 'td': td}; exec(open(project.folder + '/experiments/sc_kifs_office/take_shot.py').read(), g)
#     g['arm']('rb', "ring > 0.55")     # later:  op(S).fetch('take_shot', None)
# build.py destroys the COMP, so the DAT never survives a rebuild.
S = '/project1/sc_kifs_office'

CODE = '''
def onFrameEnd(frame):
    s = op('%s')
    h = s.op('hub')
    ring = float(s.op('ring')[0])
    hit_low, hit_mid, hit_high = float(h['hit_low']), float(h['hit_mid']), float(h['hit_high'])
    bar_pulse, pulse, energy = float(h['bar_pulse']), float(h['pulse']), float(h['energy'])
    if __COND__:
        me.par.active = False
        g = {'op': op, 'absTime': absTime}
        exec(open(project.folder + '/experiments/sc_kifs_office/take_cap.py').read(), g)
        seeds = __SEEDS__
        out = {}
        for i in range(len(seeds)):
            x = g['cap']('__NAME___take%%d' %% i, i, seeds[i], age=5)
            if i == 0:
                out = {k: x[k] for k in ('t', 'energy', 'section', 'hit_mid', 'hit_high', 'bar_pulse', 'pulse', 'fold', 'ring')}
        s.store('take_shot', str(out))
    return
''' % S


def arm(name, cond, seeds=(0.3, 0.47, 0.71, 0.55, 0.12, 0.71, 0.55)):
    s = op(S)
    d = s.op('take_shot') or s.create(td.executeDAT, 'take_shot')
    d.par.active = False
    d.text = CODE.replace('__COND__', cond).replace('__NAME__', name).replace('__SEEDS__', str(list(seeds)))
    s.store('take_shot', 'waiting')
    d.par.frameend = True
    d.par.active = True
    return d.path
