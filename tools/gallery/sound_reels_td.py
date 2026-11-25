# Records reels that can be given their music afterwards. Runs inside TouchDesigner,
# never blocks.
#
#     g = {'op': op, 'td': td, 'absTime': absTime, 'project': project}
#     exec(open(REPO + '/tools/gallery/sound_reels_td.py', encoding='utf-8').read(), g)
#     g['start'](jobs)
#     g['status']()
#
# job: {'movie': file, 'top': TOP to record, 'track': hub track, 'start': track time (s),
#       'parts': [{'frames': n, 'sets': [(comp path, parameter, value), ...], 'shot': [comp path, ...]}]}
# Each part sets its parameters, restarts the shot of every scene named in 'shot'
# (their Shotstart), and records n frames. After the job, every parameter it set
# is put back.
#
# Unlike reels_td.py this is frame-accurate: the hub's track time is stepped one
# frame per recorded frame and the project is off the clock (as sw_cut's record()
# does), so the movie lines up with the track however slowly the machine renders.
# The movie is silent. Add the sound from the track itself:
#     ffmpeg -i reel.mov -ss <start> -t <seconds> -i <track> -map 0:v -map 1:a out.mp4
import td

COMP = "/project1/sw_soundreels"
WARM_FRAMES = 45  # for the hub to load a track and the scene to start cooking
GAP_FRAMES = 40  # between movies, for the file to close

STEPPER = '''def _apply(comp, part, undo):
    for path, name, value in part.get('sets', []):
        par = getattr(op(path).par, name)
        undo.setdefault((path, name), par.eval())
        par.val = value
    for path in part.get('shot', []):
        op(path).par.Shotstart = absTime.seconds


def onFrameStart(frame):
    comp = parent()
    jobs = comp.fetch('jobs', [])
    i = comp.fetch('i', 0)
    hub = op('/project1/sw_hub')
    rec = comp.op('rec')
    if i >= len(jobs):
        if comp.fetch('running', False):
            comp.store('running', False)
            rec.par.record = False
            hub.par.Clock = -1
            project.realTime = comp.fetch('realtime', True)
            cut = op('/project1/sw_cut')
            if cut is not None:
                cut.op('cook_driver').par.framestart = True
        return
    job = jobs[i]
    f = comp.fetch('f', 0)
    warm = comp.fetch('warm', 45)
    total = sum(p['frames'] for p in job['parts'])
    fps = rec.par.fps.eval()
    if f == 0:
        rec.par.record = False
        rec.par.file = job['movie']
        comp.op('src').par.top = job['top']
        if hub.par.Track.eval() != job['track']:
            hub.par.Track = job['track']
        hub.par.Clock = float(job['start'])
        comp.store('undo', {})
    if f < warm:
        if f == warm - 20:
            undo = comp.fetch('undo', {})
            _apply(comp, job['parts'][0], undo)
            comp.store('undo', undo)
        comp.op('src').cook(force=True)
    elif f == warm:
        rec.par.record = True
    elif f <= warm + total:
        k = f - warm - 1  # the frame being written
        at = 0
        for n, part in enumerate(job['parts']):
            if k == at and n > 0:
                undo = comp.fetch('undo', {})
                _apply(comp, part, undo)
                comp.store('undo', undo)
            at += part['frames']
        rec.cook(force=True)
        hub.par.Clock = float(job['start']) + (k + 1) / fps
        if k == total - 1:
            rec.par.record = False
    elif f == warm + total + 1:
        for (path, name), value in comp.fetch('undo', {}).items():
            getattr(op(path).par, name).val = value
    elif f >= warm + total + comp.fetch('gap', 40):
        comp.store('i', i + 1)
        comp.store('f', 0)
        return
    comp.store('f', f + 1)
    return
'''


def start(jobs):
    root = op("/project1")
    old = op(COMP)
    if old:
        old.destroy()
    cut = op("/project1/sw_cut")
    if cut is not None:
        cut.op("cook_driver").par.framestart = False
    op("/project1/sw_hub").par.Scene = ""
    try:  # a recording steps the timeline for minutes: nothing may play out loud meanwhile
        import tdh

        tdh.mute(everything=True)
    except ImportError:
        pass
    comp = root.create(td.baseCOMP, "sw_soundreels")
    comp.nodeX, comp.nodeY = -350, -1300
    src = comp.create(td.selectTOP, "src")
    rec = comp.create(td.moviefileoutTOP, "rec")
    rec.par.videocodec = "mjpa"  # h264 needs a Commercial licence; ffmpeg converts afterwards
    rec.par.limitlength = False
    src.outputConnectors[0].connect(rec)
    comp.store("jobs", jobs)
    comp.store("i", 0)
    comp.store("f", 0)
    comp.store("warm", WARM_FRAMES)
    comp.store("gap", GAP_FRAMES)
    comp.store("realtime", bool(td.project.realTime))
    comp.store("running", True)
    td.project.realTime = False
    stepper = comp.create(td.executeDAT, "stepper")
    stepper.text = STEPPER
    stepper.par.framestart = True
    stepper.par.active = True
    return len(jobs)


def status():
    comp = op(COMP)
    if comp is None:
        return "not started"
    return "%d/%d f=%d %s" % (comp.fetch("i", 0), len(comp.fetch("jobs", [])), comp.fetch("f", 0), "running" if comp.fetch("running", False) else "done")
