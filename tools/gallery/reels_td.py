# Records the website's samples. Runs inside TouchDesigner, never blocks.
#
#     g = {'op': op, 'td': td, 'absTime': absTime}
#     exec(open(REPO + '/tools/gallery/reels_td.py', encoding='utf-8').read(), g)
#     g['start_reels'](out_dir, {'sc_rd_stamp': 7, ...}, describe=True)   # scene -> takes
#     g['start_combos'](out_dir, [{'id':..., 'source':..., 'source_take':..., 'processor':..., 'take':..., 'seed':...}], seconds=6)
#     g['status']()
#
# Reels: for each scene, one movie <out_dir>/<scene>/take_all.mov holding a few
# seconds of every take from the moment the take starts (so arrivals are in it),
# plus a still <out_dir>/<scene>/take_NN_00.jpg from late in each take.
# Combos: one movie and one still per combination, the processor scene's output
# while its Input is the source scene's out1. With seconds=0 only the still is
# saved (for exploring many pairs quickly).
#
# The cutter is parked while this runs and restarted after; scenes are driven
# directly through their Preview, Take, Seed, Describe and Input parameters.
import td

COMP = "/project1/sw_reels"
TAKE_FRAMES = 180  # 3 s of each take in a reel
STILL_AT = 150
GAP_FRAMES = 40  # between movies, for the file to close
SETTLE_FRAMES = 150  # before a combination is recorded

STEPPER = '''def _prep(scene, take, seed, describe, inp):
    c = op('/project1/' + scene)
    c.par.Preview = True
    c.par.Describe = describe
    c.par.Input = inp
    c.par.Take = take
    c.par.Seed = seed
    c.par.Shotstart = absTime.seconds
    return c


def _release(scene):
    c = op('/project1/' + scene)
    if c is not None:
        c.par.Preview = False
        c.par.Describe = False
        c.par.Input = ''


def onFrameStart(frame):
    comp = parent()
    jobs = comp.fetch('jobs', [])
    i = comp.fetch('i', 0)
    if i >= len(jobs):
        if comp.fetch('running', False):
            comp.store('running', False)
            comp.op('rec').par.record = False
            cut = op('/project1/sw_cut')
            if cut is not None:
                cut.op('cook_driver').par.framestart = True
        return
    job = jobs[i]
    f = comp.fetch('f', 0)
    rec = comp.op('rec')
    show = job.get('processor') or job['scene']
    if f == 0:
        comp.op('src').par.top = '/project1/' + show + '/out1'
        if job['kind'] == 'reel':
            _prep(job['scene'], job['take'], job['seed'], job['describe'], '')
            if job['first']:
                rec.par.record = False
                rec.par.file = job['movie']
        else:
            _prep(job['scene'], job['source_take'], job['seed'], job['describe'], '')
            _prep(job['processor'], job['take'], job['seed'], job['describe'], '/project1/' + job['scene'] + '/out1')
            rec.par.record = False
            if job['frames']:
                rec.par.file = job['movie']
    comp.op('small').cook(force=True)

    if job['kind'] == 'reel':
        if f == 1 and job['first']:
            rec.par.record = True
        if rec.par.record.eval():
            rec.cook(force=True)
        if f == comp.fetch('still_at', 150):
            comp.op('small').save(job['still'], asynchronous=True)
        if f >= comp.fetch('take_frames', 180):
            if job['last']:
                rec.par.record = False
                if f < comp.fetch('take_frames', 180) + comp.fetch('gap', 40):
                    comp.store('f', f + 1)
                    return
                _release(job['scene'])
            comp.store('i', i + 1)
            comp.store('f', 0)
            return
    else:
        settle = comp.fetch('settle', 150)
        if f == settle:
            comp.op('small').save(job['still'], asynchronous=True)
            if job['frames']:
                rec.par.record = True
        if rec.par.record.eval():
            rec.cook(force=True)
        if f >= settle + job['frames']:
            rec.par.record = False
            if job['frames'] and f < settle + job['frames'] + comp.fetch('gap', 40):
                comp.store('f', f + 1)
                return
            _release(job['processor'])
            _release(job['scene'])
            comp.store('i', i + 1)
            comp.store('f', 0)
            return
    comp.store('f', f + 1)
    return
'''


def _make(jobs):
    root = op("/project1")
    old = op(COMP)
    if old:
        old.destroy()
    cut = op("/project1/sw_cut")
    if cut is not None:
        cut.op("cook_driver").par.framestart = False
    op("/project1/sw_hub").par.Scene = ""
    comp = root.create(td.baseCOMP, "sw_reels")
    comp.nodeX, comp.nodeY = -350, -1300
    src = comp.create(td.selectTOP, "src")
    small = comp.create(td.resolutionTOP, "small")
    small.par.outputresolution = "custom"
    small.par.resolutionw, small.par.resolutionh = 854, 480
    src.outputConnectors[0].connect(small)
    rec = comp.create(td.moviefileoutTOP, "rec")
    rec.par.videocodec = "mjpa"  # h264 needs a Commercial licence; ffmpeg converts afterwards
    small.outputConnectors[0].connect(rec)
    comp.store("jobs", jobs)
    comp.store("i", 0)
    comp.store("f", 0)
    comp.store("take_frames", TAKE_FRAMES)
    comp.store("still_at", STILL_AT)
    comp.store("gap", GAP_FRAMES)
    comp.store("settle", SETTLE_FRAMES)
    comp.store("running", True)
    stepper = comp.create(td.executeDAT, "stepper")
    stepper.text = STEPPER
    stepper.par.framestart = True
    stepper.par.active = True
    return len(jobs)


def start_reels(out_dir, takes, describe=True):
    import os

    jobs = []
    for scene, n in takes.items():
        os.makedirs(out_dir + "/" + scene, exist_ok=True)
        for take in range(n):
            jobs.append({
                "kind": "reel", "scene": scene, "take": take, "seed": (0.37 + take * 0.137) % 1.0,
                "describe": bool(describe), "first": take == 0, "last": take == n - 1,
                "movie": "%s/%s/take_all.mov" % (out_dir, scene),
                "still": "%s/%s/take_%02d_00.jpg" % (out_dir, scene, take),
            })
    return _make(jobs)


def start_combos(out_dir, combos, seconds=6.0, describe=False):
    import os

    os.makedirs(out_dir + "/_combos", exist_ok=True)
    jobs = []
    for c in combos:
        jobs.append({
            "kind": "combo", "scene": c["source"], "source_take": int(c.get("source_take", 0)),
            "processor": c["processor"], "take": int(c.get("take", 0)), "seed": float(c.get("seed", 0.37)),
            "describe": bool(c.get("describe", describe)), "frames": int(seconds * 60),
            "movie": "%s/_combos/%s.mov" % (out_dir, c["id"]),
            "still": "%s/_combos/%s.jpg" % (out_dir, c["id"]),
        })
    return _make(jobs)


def status():
    comp = op(COMP)
    if comp is None:
        return "not started"
    return "%d/%d %s" % (comp.fetch("i", 0), len(comp.fetch("jobs", [])), "running" if comp.fetch("running", False) else "done")
