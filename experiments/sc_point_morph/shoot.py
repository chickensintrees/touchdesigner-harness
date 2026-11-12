# Capture helper for reviewing takes: exec this file inside TouchDesigner, then
#     shoot([(take, seed, age, 'name'[, manual, describe, input]), ...])   # schedules; returns at once
# Each shot sets the scene's Take / Seed / Shotstart, waits a few frames so the picture is the
# new one (forcing cooks inside one script does not advance the frame, NOTES log 03), captures
# captures/<name>.png and records the feed in the scene's storage under 'shots'.
# The cutter may also be setting Take while we work, so the record says what Take was at capture.
import td

SCENE = '/project1/sc_point_morph'


def _set(take, seed, age, manual, describe=False, inp=''):
    s = td.op(SCENE)
    s.par.Take, s.par.Seed = take, seed
    s.par.Describe, s.par.Input = describe, inp
    s.par.Shotstart = td.absTime.seconds - age
    s.op('trail_fb').par.resetpulse.pulse()      # as a real cut does (the trail is emptied at age 0)
    if manual is None:
        s.par.Manual = False
    else:
        s.par.Manual = True
        s.par.Shape, s.par.Morph = manual
    return


def _grab(take, name, size):
    import tdh
    s = td.op(SCENE)
    tdh.capture(SCENE + '/out1', 'experiments/sc_point_morph/captures/' + name + '.png', max_size=size)
    h = s.op('hub')
    rec = {k: round(float(h[k][0]), 3) for k in ('t', 'section', 'section_pos', 'hit_low', 'pulse', 'energy', 'beat_pos', 'vocals')}
    rec['take_ok'] = int(s.par.Take) == take
    rec['age'] = round(float(s.op('shot')['age'][0]), 2)
    rec['shapes'] = [int(c[0]) for c in s.op('sel').chans()]
    # cost of everything in the scene that cooked this frame, and of the three heavy operators
    live = [o for o in s.findChildren(maxDepth=2) if td.absTime.frame - o.cookAbsFrame <= 1]
    rec['ms_all'] = round(float(sum(o.cpuCookTime + getattr(o, 'gpuCookTime', 0.0) for o in live)), 2)
    rec['ms'] = {n: [round(float(s.op(n).cpuCookTime), 2), round(float(s.op(n).gpuCookTime), 2)] for n in ('render', 'trail', 'post')}
    d = s.fetch('shots', {})
    d[name] = rec
    s.store('shots', d)
    return


def shoot(shots, gap=14, settle=9, size=640):
    td.op(SCENE).store('shots', {})
    me = td.op(SCENE + '/shoot_code')
    for i, sh in enumerate(shots):
        take, seed, age, name = sh[:4]
        manual = sh[4] if len(sh) > 4 else None
        describe = bool(sh[5]) if len(sh) > 5 else False
        inp = sh[6] if len(sh) > 6 else ''
        td.run("mod('" + me.path + "')._set(%r, %r, %r, %r, %r, %r)" % (take, seed, age, manual, describe, inp),
               delayFrames=1 + i * gap)
        td.run("mod('" + me.path + "')._grab(%r, %r, %r)" % (take, name, size), delayFrames=1 + i * gap + settle)
    return len(shots)
