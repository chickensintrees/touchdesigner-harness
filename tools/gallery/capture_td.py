# Captures every preset of the scene engine for the gallery. Runs inside TouchDesigner.
#
#     g = {'op': op, 'td': td, 'absTime': absTime}
#     exec(open(REPO + '/tools/gallery/capture_td.py', encoding='utf-8').read(), g)
#     g['start'](out_dir, {'sc_rd_stamp': 6, ...})      # scene -> number of takes
#
# It never blocks: an Execute DAT steps through the jobs a frame at a time, driving
# the cutter's Manual page (scene, take, seed), waiting for the picture to settle,
# then saving a short run of frames. Read progress with g['status']().
import td

COMP = "/project1/sw_gallery"
CUT = "/project1/sw_cut"
SETTLE_FRAMES = 200  # simulations and feedback loops need a few seconds to become themselves
BURST = 12  # frames saved per take, for the moving preview
BURST_EVERY = 5  # one saved frame every this many frames (12 fps at 60)

STEPPER = '''def onFrameStart(frame):
    comp = parent()
    jobs = comp.fetch('jobs', [])
    i = comp.fetch('i', 0)
    if i >= len(jobs):
        if comp.fetch('running', False):
            comp.store('running', False)
            cut = op('/project1/sw_cut')
            cut.par.Auto = True
        return
    job = jobs[i]
    f = comp.fetch('f', 0)
    cut = op('/project1/sw_cut')
    if f == 0:
        names = [r[0].val for r in cut.op('scenes').rows()[1:]]
        cut.par.Auto = False
        cut.par.Manual = names.index(job['scene'])
        cut.par.Mantake = job['take']
        cut.par.Manseed = job['seed']
        cut.par.Mantreat = job.get('treat', 0)
        target = op('/project1/' + job['scene'])
        if hasattr(target.par, 'Shotstart'):
            target.par.Shotstart = absTime.seconds
    settle = comp.fetch('settle', 200)
    every = comp.fetch('every', 5)
    burst = job.get('burst', 1)
    k = f - settle
    if k >= 0 and k % every == 0 and k // every < burst:
        small = comp.op('small')
        small.cook(force=True)
        small.save('%s_%02d.jpg' % (job['file'], k // every), asynchronous=True)
    if k >= every * burst:
        comp.store('i', i + 1)
        comp.store('f', 0)
        return
    comp.store('f', f + 1)
    return
'''


def start(out_dir, takes, seeds=(0.37,), treat_scene=None, treatments=0):
    """takes: {scene: number of takes}. Saves <out_dir>/<scene>/take_<n>_<frame>.jpg.

    With treat_scene and treatments=N, also saves that scene under treatments 0..N
    to <out_dir>/_treatments/treat_<n>_00.jpg.
    """
    import os

    root = op("/project1")
    old = op(COMP)
    if old:
        old.destroy()
    comp = root.create(td.baseCOMP, "sw_gallery")
    comp.nodeX, comp.nodeY = -350, -1100
    sel = comp.create(td.selectTOP, "src")
    sel.par.top = CUT + "/out1"
    small = comp.create(td.resolutionTOP, "small")
    small.par.outputresolution = "custom"
    small.par.resolutionw, small.par.resolutionh = 640, 360
    sel.outputConnectors[0].connect(small)

    jobs = []
    for scene, n in takes.items():
        os.makedirs(out_dir + "/" + scene, exist_ok=True)
        for take in range(n):
            jobs.append({
                "scene": scene, "take": take, "seed": (seeds[take % len(seeds)] + take * 0.137) % 1.0,
                "burst": BURST, "file": "%s/%s/take_%02d" % (out_dir, scene, take),
            })
    if treat_scene:
        os.makedirs(out_dir + "/_treatments", exist_ok=True)
        for t in range(treatments + 1):
            jobs.append({
                "scene": treat_scene, "take": 0, "seed": (0.11 + t * 0.37) % 1.0, "treat": t,
                "burst": 1, "file": "%s/_treatments/treat_%02d" % (out_dir, t),
            })
    comp.store("jobs", jobs)
    comp.store("i", 0)
    comp.store("f", 0)
    comp.store("settle", SETTLE_FRAMES)
    comp.store("every", BURST_EVERY)
    comp.store("running", True)
    stepper = comp.create(td.executeDAT, "stepper")
    stepper.text = STEPPER
    stepper.par.framestart = True
    stepper.par.active = True
    return len(jobs)


def status():
    comp = op(COMP)
    if comp is None:
        return "not started"
    jobs = comp.fetch("jobs", [])
    i = comp.fetch("i", 0)
    return "%d/%d %s" % (i, len(jobs), "running" if comp.fetch("running", False) else "done")
