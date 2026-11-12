# Builds the whole scene engine in the open project: the hub, every scene listed in
# experiments/sw_cut/scenes.json, the cutter and the control panel. Run inside
# TouchDesigner, in a project saved at the repository root (lab.toe):
#
#     g = {'op': op, 'td': td, 'absTime': absTime, 'project': project}
#     exec(open(project.folder + '/experiments/sw_hub/build_all.py', encoding='utf-8').read(), g)
#     g['start']()
#     g['status']()        # {'done': 5, 'of': 21, 'running': True, 'log': {}}
#
# It never blocks for long: one builder runs per step, a few frames apart. Builders
# that raise are recorded in the log and the rest still run. When it finishes, the
# control panel opens beside the output. The timeline must be playing: the steps run
# on frame starts, so a paused timeline builds nothing.
import td

COMP = "/project1/sw_buildall"
GAP_FRAMES = 20  # frames between builders, so the interface stays responsive

STEPPER = '''import traceback


def onFrameStart(frame):
    comp = parent()
    jobs = comp.fetch('jobs', [])
    i = comp.fetch('i', 0)
    if i >= len(jobs):
        if comp.fetch('running', False):
            comp.store('running', False)
            me.par.active = False
        return
    wait = comp.fetch('wait', 0)
    if wait > 0:
        comp.store('wait', wait - 1)
        return
    name, calls = jobs[i]
    try:
        g = {'op': op, 'td': td, 'absTime': absTime, 'project': project, '__name__': 'build'}
        path = project.folder.replace(chr(92), '/') + '/experiments/' + name + '/build.py'
        exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), g)
        for call in calls:
            g[call]()
        scene = op('/project1/' + name)
        if scene is not None and hasattr(scene.par, 'Preview'):
            scene.par.Preview = False
    except Exception:
        log = comp.fetch('log', {})
        log[name] = traceback.format_exc()[-800:]
        comp.store('log', log)
    comp.store('i', i + 1)
    comp.store('wait', comp.fetch('gap', 20))
    return
'''


def start(scenes=None, panel=True):
    """Build the hub, the scenes (default: all in sw_cut/scenes.json), the cutter and the panel."""
    import json

    repo = td.project.folder.replace(chr(92), "/")
    if scenes is None:
        with open(repo + "/experiments/sw_cut/scenes.json", encoding="utf-8") as fh:
            scenes = sorted(json.load(fh))
    jobs = [("sw_hub", ["build"])] + [(s, ["build"]) for s in scenes] + [("sw_cut", ["build"])]
    if panel:
        jobs.append(("sw_panel", ["build", "show"]))
    root = op("/project1")
    old = op(COMP)
    if old:
        old.destroy()
    comp = root.create(td.baseCOMP, "sw_buildall")
    comp.nodeX, comp.nodeY = -350, -1700
    comp.store("jobs", jobs)
    comp.store("i", 0)
    comp.store("wait", 0)
    comp.store("gap", GAP_FRAMES)
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
