# Dev helper: schedule captures of several takes without blocking TouchDesigner.
# Run inside TouchDesigner with globals SHOTS = [(take, seed, 'file.png'), ...] and optional GAP (frames
# between setting the take and capturing it, default 80) and SIZE (default 1280).
# Each shot sets Take / Seed / Shotstart, waits GAP frames, captures, and records the feed in storage 'shots'.
S = '/project1/sc_kinetic_type'
_gap = globals().get('GAP', 80)
_size = globals().get('SIZE', 1280)
op(S).store('shots', {})
_set = ("s=op('%s'); s.par.Preview=True; s.par.Take=%d; s.par.Seed=%f; s.par.Shotstart=absTime.seconds")
_cap = ("import tdh\ns=op('%s'); h=s.op('hub')\n"
        "tdh.capture(s.op('out1').path, 'experiments/sc_kinetic_type/captures/%s', max_size=%d)\n"
        "d=s.fetch('shots', {}); d['%s']=dict(take=int(s.par.Take), t=round(float(h['t']),2), "
        "beat_pos=round(float(h['beat_pos']),2), hit_low=round(float(h['hit_low']),2), "
        "hit_mid=round(float(h['hit_mid']),2), pulse=round(float(h['pulse']),2), "
        "energy=round(float(h['energy']),2), section=int(h['section'])); s.store('shots', d)")
for _i, (_take, _seed, _file) in enumerate(SHOTS):
    run(_set % (S, _take, _seed), delayFrames=1 + _i * (_gap + 4))
    run(_cap % (S, _file, _size, _file), delayFrames=1 + _i * (_gap + 4) + _gap)
r = 'scheduled %d shots over %d frames' % (len(SHOTS), len(SHOTS) * (_gap + 4))
