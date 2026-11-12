# Dev helper: capture the frame on which a feed condition first holds (a snare, a phase of the bar).
# Run inside TouchDesigner with globals TAKE, SEED, COND (python expression over h = the hub CHOP and
# age = seconds since the take was set), FILE (name in captures/), optional SIZE.
# A temporary Execute DAT in the scene does the watching and switches itself off after the capture.
S = '/project1/sc_kinetic_type'
_s = op(S)
_old = _s.op('kt_watch')
if _old:
    _old.destroy()
_s.par.Preview = True
_s.par.Take = TAKE
_s.par.Seed = SEED
_s.par.Shotstart = absTime.seconds - globals().get('BACKDATE', 0.0)
_s.store('watch', None)
_d = _s.create(td.executeDAT, 'kt_watch')
_d.nodeX, _d.nodeY = -400, -220
_d.text = '''import tdh
def onFrameEnd(frame):
    s = parent(); h = s.op('hub')
    age = absTime.seconds - %f
    if age > 20:
        me.par.active = False
        return
    if %s:
        tdh.capture(s.op('out1').path, 'experiments/sc_kinetic_type/captures/%s', max_size=%d)
        s.store('watch', dict(file='%s', t=round(float(h['t']), 2), beat_pos=round(float(h['beat_pos']), 2),
                bar_pos=round(float(h['bar_pos']), 2), hit_low=round(float(h['hit_low']), 2),
                hit_mid=round(float(h['hit_mid']), 2), hit_high=round(float(h['hit_high']), 2),
                pulse=round(float(h['pulse']), 2), energy=round(float(h['energy']), 2), age=round(age, 2)))
        me.par.active = False
    return
''' % (absTime.seconds, COND, FILE, globals().get('SIZE', 1280), FILE)
_d.par.frameend = True
_d.par.active = True
r = 'watching'
