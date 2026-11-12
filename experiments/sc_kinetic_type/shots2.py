# Dev helper (review pass): two captures per shot, a few seconds apart, with the feed recorded.
# Run inside TouchDesigner with globals SHOTS = [(take, seed, 'stem'), ...], optional GAP1 (frames from
# the cut to the first capture, default 45), GAP2 (frames between the two captures, default 150; 0 = one
# capture only) and SIZE (default 1280). Writes captures/<stem>_a.png and <stem>_b.png and stores the
# feed readings in the COMP's storage under 'shots'.
S = '/project1/sc_kinetic_type'
_g1 = globals().get('GAP1', 45)
_g2 = globals().get('GAP2', 150)
_size = globals().get('SIZE', 1280)
op(S).store('shots', {})
_set = ("s=op('%s'); s.par.Preview=True; s.par.Take=%d; s.par.Seed=%f; s.par.Shotstart=absTime.seconds")
_cap = ("import tdh\ns=op('%s'); h=s.op('hub')\n"
        "tdh.capture(s.op('out1').path, 'experiments/sc_kinetic_type/captures/%s.png', max_size=%d)\n"
        "d=s.fetch('shots', {}); d['%s']=dict(take=int(s.par.Take), seed=round(float(s.par.Seed),2), "
        "t=round(float(h['t']),2), energy=round(float(h['energy']),2), section=int(h['section']), "
        "beat=round(float(h['beat']),2), hit_low=round(float(h['hit_low']),2), hits_low=int(h['hits_low']), "
        "hit_mid=round(float(h['hit_mid']),2), bass=round(float(h['bass']),2), vocals=round(float(h['vocals']),2), "
        "age=round(float(s.op('shot')['age']),2), bar_i=int(h['bar_i']), beat_i=int(h['beat_i']), "
        "hit_high=round(float(h['hit_high']),2), pulse=round(float(h['pulse']),2)); s.store('shots', d)")
_per = _g1 + _g2 + 6
for _i, (_take, _seed, _stem) in enumerate(SHOTS):
    run(_set % (S, _take, _seed), delayFrames=1 + _i * _per)
    if _g2:
        run(_cap % (S, _stem + '_a', _size, _stem + '_a'), delayFrames=1 + _i * _per + _g1)
        run(_cap % (S, _stem + '_b', _size, _stem + '_b'), delayFrames=1 + _i * _per + _g1 + _g2)
    else:
        run(_cap % (S, _stem, _size, _stem), delayFrames=1 + _i * _per + _g1)
r = 'scheduled %d shots over %d frames' % (len(SHOTS), len(SHOTS) * _per)
