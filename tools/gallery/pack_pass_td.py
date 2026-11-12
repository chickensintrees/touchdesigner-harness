# Rebuilds every scene on a chosen asset pack and captures a few takes of each.
# Runs inside TouchDesigner and never blocks for long: one scene is rebuilt per
# step, then the stepper waits and saves stills.
#
#     g = {'op': op, 'td': td, 'absTime': absTime, 'project': project}
#     exec(open(project.folder + '/tools/gallery/pack_pass_td.py', encoding='utf-8').read(), g)
#     g['start'](out_dir, pack_dir, ['sc_rd_stamp', ...], takes=(0, 2, 4))
#     g['status']()
#
# pack_dir '' means the default pack. Each scene's Assets parameter is set to
# pack_dir before its rebuild (the scaffold keeps it across the rebuild) and is
# left that way; call start(..., pack_dir='') again to put scenes back.
# save=True also saves each scene's .tox and text snapshot after its stills (only
# when its build raised nothing).
import td

COMP = "/project1/sw_packpass"

STEPPER = '''import traceback


def onFrameStart(frame):
    comp = parent()
    jobs = comp.fetch('jobs', [])
    i = comp.fetch('i', 0)
    if i >= len(jobs):
        comp.store('running', False)
        return
    job = jobs[i]
    f = comp.fetch('f', 0)
    scene = op('/project1/' + job['scene'])
    if f == 0 and job['rebuild']:
        try:
            if scene is not None and hasattr(scene.par, 'Assets'):
                scene.par.Assets = job['pack']
            g = {'op': op, 'td': td, 'absTime': absTime, 'project': project, '__name__': 'build'}
            path = project.folder.replace(chr(92), '/') + '/experiments/' + job['scene'] + '/build.py'
            exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), g)
            g['build']()
            scene = op('/project1/' + job['scene'])
            scene.par.Assets = job['pack']
        except Exception:
            log = comp.fetch('log', {})
            log[job['scene']] = traceback.format_exc()[-600:]
            comp.store('log', log)
    if f == 1 and scene is not None:
        scene.par.Preview = True
        scene.par.Take = job['take']
        scene.par.Seed = job['seed']
        scene.par.Shotstart = absTime.seconds
        comp.op('src').par.top = scene.path + '/out1'
    if f == job['settle']:
        comp.op('small').cook(force=True)
        comp.op('small').save(job['file'], asynchronous=True)
    if f > job['settle'] + 2:
        if job['last'] and scene is not None:
            scene.par.Preview = False
            if job.get('save') and job['scene'] not in comp.fetch('log', {}):
                # Saved with Assets blank, so the files hold no folder of this machine. The
                # words and tables built from the pack stay as built.
                import tdh
                scene.par.Assets = ''
                folder = 'experiments/' + job['scene'] + '/'
                tdh.save_tox(scene.path, folder + job['scene'] + '.tox')
                tdh.snapshot(scene.path, folder + 'snapshot/network.json')
                scene.par.Assets = job['pack']
            errs = scene.errors(recurse=True)
            if errs:
                log = comp.fetch('log', {})
                log[job['scene']] = (log.get(job['scene'], '') + ' ERRORS: ' + errs)[-600:]
                comp.store('log', log)
        comp.store('i', i + 1)
        comp.store('f', 0)
        return
    comp.store('f', f + 1)
    return
'''


def start(out_dir, pack_dir, scenes, takes=(0, 2, 4), settle=210, save=False):
    import os

    root = op("/project1")
    old = op(COMP)
    if old:
        old.destroy()
    comp = root.create(td.baseCOMP, "sw_packpass")
    comp.nodeX, comp.nodeY = -350, -1500
    src = comp.create(td.selectTOP, "src")
    small = comp.create(td.resolutionTOP, "small")
    small.par.outputresolution = "custom"
    small.par.resolutionw, small.par.resolutionh = 640, 360
    src.outputConnectors[0].connect(small)
    os.makedirs(out_dir, exist_ok=True)
    jobs = []
    for scene in scenes:
        for k, take in enumerate(takes):
            jobs.append({
                "scene": scene, "pack": pack_dir, "take": take, "seed": (0.37 + take * 0.137) % 1.0,
                "rebuild": k == 0, "last": k == len(takes) - 1, "save": save, "settle": settle if k == 0 else 170,
                "file": "%s/%s_take%02d.jpg" % (out_dir, scene, take),
            })
    comp.store("jobs", jobs)
    comp.store("i", 0)
    comp.store("f", 0)
    comp.store("log", {})
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
    return {"done": comp.fetch("i", 0), "of": len(comp.fetch("jobs", [])), "running": comp.fetch("running", False), "log": comp.fetch("log", {})}
