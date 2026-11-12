# Capture helper for reviewing this scene: saves captures/<name>.png and returns the feed read in the same call.
#     g = {'op': op}; exec(open(project.folder + '/experiments/sc_kifs_office/ad_cap.py').read(), g); r = g['cap']('name')
import tdh


def cap(name):
    S = '/project1/sc_kifs_office'
    h = op(S + '/hub')
    tdh.capture(S + '/out1', 'experiments/sc_kifs_office/captures/%s.png' % name, max_size=1280)
    r = {k: round(float(h[k]), 3) for k in ('t', 'energy', 'section', 'beat', 'hit_low', 'hits_low', 'hit_mid',
                                             'hit_high', 'bass', 'vocals', 'bar_pulse', 'pulse')}
    g = op(S + '/kifs')
    r['fold'] = str([round(float(g.par.vec1valuex.eval()), 3), round(float(g.par.vec1valuey.eval()), 3)])
    r['ring'] = round(float(op(S + '/ring')[0]), 3)
    r['gpu_ms'] = round(float(g.gpuCookTime), 2)
    r['err'] = str(tdh.errors(S))
    return r
