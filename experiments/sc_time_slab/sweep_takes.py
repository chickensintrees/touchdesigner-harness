# Capture takes of sc_time_slab without blocking TouchDesigner: for each one it
# schedules a cut to that take (Take, Seed, Shotstart = now, as the cutter does) and,
# `age` seconds later, a capture.
# Run inside TouchDesigner:
#   g = {'op': op, 'run': run, 'td': td}
#   exec(open(project.folder + '/experiments/sc_time_slab/sweep_takes.py', encoding='utf-8').read(), g)
#   g['sweep'](takes=range(8), seed=0.0, prefix='take_', age=1.5)
# seeds=[...] gives each entry of takes its own seed and adds it to the file name.
# The feed at each capture lands in the COMP's storage under 'sweep'.
SCENE = '/project1/sc_time_slab'

# The cutter sets Take, Seed and Shotstart whenever it cuts to this scene, which can
# land in the second the slab needs to fill. While a sweep runs, this DAT puts the
# values under test back at the start of every frame; the sweep deletes it at the end.
LOCK = '''def onFrameStart(frame):
    want = parent().fetch('lock', None)
    if want:
        for k, v in want.items():
            p = getattr(parent().par, k)
            if p.eval() != v:
                p.val = v
    return
'''


def sweep(takes=range(8), seed=0.0, prefix='take_', age=1.5, seeds=None, gap=None):
    takes = list(takes)
    wait = max(1, int(age * 60))
    gap = gap or wait + 10
    scene = op(SCENE)
    scene.store('sweep', {})
    lock = scene.op('take_lock') or scene.create(td.executeDAT, 'take_lock')
    lock.text = LOCK
    lock.par.framestart = True
    lock.par.active = True
    run("s = op('%s'); s.unstore('lock'); s.op('take_lock').destroy()" % SCENE, delayFrames=len(takes) * gap + 5)
    for k, tk in enumerate(takes):
        sd = seeds[k] if seeds else seed
        name = '%s%d' % (prefix, tk) if not seeds else '%s%d_s%03d' % (prefix, tk, int(round(sd * 1000)))
        run("import td; op('%s').store('lock', {'Take': %d, 'Seed': %r, 'Shotstart': td.absTime.seconds})" % (SCENE, tk, sd),
            delayFrames=1 + k * gap)
        cap = (
            "import tdh\n"
            "s = op('%s')\n"
            "h = s.op('hub')\n"
            "ok = int(s.par.Take.eval()) == %d\n"
            "tdh.capture(s.path + '/out1', 'experiments/sc_time_slab/captures/%s.png', max_size=1280)\n"
            "import td\n"
            "live = [o for o in s.findChildren(maxDepth=2) if td.absTime.frame - o.cookAbsFrame <= 1]\n"
            "cpu = sum(float(o.cpuCookTime or 0) for o in live)\n"
            "gpu = sum(float(getattr(o, 'gpuCookTime', 0) or 0) for o in live)\n"
            "worst = max(live, key=lambda o: float(o.cpuCookTime or 0) + float(getattr(o, 'gpuCookTime', 0) or 0))\n"
            "d = s.fetch('sweep', {})\n"
            "d['%s'] = dict(take_held=ok, cpu_ms=round(cpu, 2), gpu_ms=round(gpu, 2), ops=len(live), worst=worst.name, "
            "age=round(float(s.op('shot')['age']), 2), "
            "**{c: round(float(h[c]), 2) for c in ('t', 'section', 'energy', 'bass', 'hit_low', 'pulse', 'beat')})\n"
            "s.store('sweep', d)\n"
        ) % (SCENE, tk, name, name)
        run(cap, delayFrames=1 + k * gap + wait)
    return len(takes)
