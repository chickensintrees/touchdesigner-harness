# Test helper, exec'd inside TouchDesigner with TAKE, SEED, CHAN, THRESH, PREFIX, OFFS (cook offsets).
# Waits for hub[CHAN] > THRESH (CHAN 'cut' = fake a cut now instead), then captures out1 at each
# offset in OFFS (counted in cooks of this scene), so a hit's travel down the levels can be seen in stills.
# The Execute DAT it makes ('evcap') deletes itself when done; scene.fetch('ev_log') has the feed values.
DAT = '''
ST = {'n': -1, 'i': 0}
def onFrameEnd(frame):
    import tdh
    s = parent()
    cfg = s.fetch('ev_cfg')
    s.par.Take = cfg['take']; s.par.Seed = cfg['seed']
    h = op('hub')
    if ST['n'] < 0:
        ST['w'] = ST.get('w', 0) + 1
        if ST['w'] < 40:
            return
        if cfg['chan'] == 'cut':
            s.par.Shotstart = absTime.seconds
            op('fb').par.resetpulse.pulse()
            ST['n'] = 0
        elif float(h[cfg['chan']]) > cfg['thresh']:
            ST['n'] = 0
        else:
            return
    offs = cfg['offs']
    if ST['i'] < len(offs) and ST['n'] >= offs[ST['i']]:
        f = '%s_%02d.png' % (cfg['prefix'], ST['i'])
        tdh.capture(s.path + '/out1', 'experiments/sc_droste_crt/captures/' + f, max_size=640)
        s.fetch('ev_log').append('%s n=%d t=%.2f hl=%.2f hm=%.2f age=%.2f' % (f, ST['n'], float(h['t']), float(h['hit_low']), float(h['hit_mid']), float(op('shot')['age'])))
        ST['i'] += 1
    ST['n'] += 1
    if ST['i'] >= len(offs):
        s.store('ev_done', 1)
        s.par.Shotstart = 0
        run("op('%s').destroy()" % me.path, delayFrames=1)
'''
s = op('/project1/sc_droste_crt')
if s.op('evcap'):
    s.op('evcap').destroy()
s.par.Preview = True
s.store('ev_cfg', {'take': TAKE, 'seed': SEED, 'chan': CHAN, 'thresh': THRESH, 'prefix': PREFIX, 'offs': OFFS})
s.store('ev_log', []); s.store('ev_done', 0)
d = s.create(td.executeDAT, 'evcap')
d.text = DAT
d.par.frameend = True
d.par.active = True
