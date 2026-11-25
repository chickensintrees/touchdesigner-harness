# Review tool, not part of the scene: arm a one-shot capture that fires on a feed condition.
# A normal capture call cannot be aimed at a 0.1 s event, so a temporary Execute DAT inside the scene's own
# COMP watches the feed each frame, captures once, stores the feed in COMP storage and switches itself off.
#     g = {'op': op, 'td': td}; exec(open(project.folder + '/experiments/sc_kifs_office/ad_shot.py').read(), g)
#     g['arm']('name', "ring > 0.85")        # then, in a later call:  op(S).fetch('ad_shot', None)
# build.py destroys the COMP, so the DAT never survives a rebuild.
S = '/project1/sc_kifs_office'

CODE = '''
import tdh
def onFrameEnd(frame):
    s = op('%s')
    h = s.op('hub')
    ring = float(s.op('ring')[0])
    v = {k: float(h[k]) for k in ('t', 'energy', 'section', 'beat', 'hit_low', 'hits_low', 'hit_mid', 'hit_high', 'bass', 'vocals', 'bar_pulse', 'pulse')}
    hit_low, hit_mid, hit_high, bar_pulse, energy = v['hit_low'], v['hit_mid'], v['hit_high'], v['bar_pulse'], v['energy']
    if __COND__:
        me.par.active = False
        tdh.capture(s.path + '/out1', 'experiments/sc_kifs_office/captures/__NAME__.png', max_size=1280)
        v = {k: round(x, 3) for k, x in v.items()}
        v['ring'] = round(ring, 3)
        g = s.op('kifs')
        v['fold'] = [round(float(g.par.vec1valuex.eval()), 3), round(float(g.par.vec1valuey.eval()), 3)]
        s.store('ad_shot', str(v))
    return
''' % S


def arm(name, cond):
    s = op(S)
    d = s.op('ad_shot') or s.create(td.executeDAT, 'ad_shot')
    d.par.active = False
    d.text = CODE.replace('__COND__', cond).replace('__NAME__', name)
    s.store('ad_shot', 'waiting')
    d.par.frameend = True
    d.par.active = True
    return d.path
