# Dev helper: schedule captures with Describe and Input set per shot, without blocking TouchDesigner.
# Run inside TouchDesigner with globals SHOTS = [(take, seed, describe, input_path, 'file.png', gap_frames), ...]
# and optional SIZE (default 1280) and OUT (folder for the files, default this scene's captures). Each shot sets Take / Seed / Describe / Input / Shotstart, waits its gap,
# captures out1 and records the feed in the COMP's storage 'shots'. The last step restores Describe off and
# Input blank (Preview is left as it was).
S = '/project1/sc_kinetic_type'
_size = globals().get('SIZE', 1280)
_out = globals().get('OUT', 'experiments/sc_kinetic_type/captures')
op(S).store('shots', {})
_set = ("s=op('%s'); s.par.Preview=True; s.par.Take=%d; s.par.Seed=%f; s.par.Describe=%d; s.par.Input='%s'; "
        "s.par.Shotstart=absTime.seconds")
_cap = ("import tdh\ns=op('%s'); h=s.op('hub')\n"
        "s.par.Take=%d; s.par.Seed=%f\n"
        "tdh.capture(s.op('out1').path, '%s/%s', max_size=%d)\n"
        "d=s.fetch('shots', {}); d['%s']=dict(take=int(s.par.Take), t=round(float(h['t']),2), "
        "beat_pos=round(float(h['beat_pos']),2), hit_low=round(float(h['hit_low']),2), "
        "hit_mid=round(float(h['hit_mid']),2), pulse=round(float(h['pulse']),2), "
        "energy=round(float(h['energy']),2), section=int(h['section'])); s.store('shots', d)")
_f = 1
for (_take, _seed, _desc, _inp, _file, _gap) in SHOTS:
    run(_set % (S, _take, _seed, int(_desc), _inp), delayFrames=_f)
    run(_cap % (S, _take, _seed, _out, _file, _size, _file), delayFrames=_f + _gap)
    _f += _gap + 4
run("s=op('%s'); s.par.Describe=0; s.par.Input=''; s.store('shots_done', True)" % S, delayFrames=_f)
op(S).store('shots_done', False)
r = 'scheduled %d shots over %d frames' % (len(SHOTS), _f)
