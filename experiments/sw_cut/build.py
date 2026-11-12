# Builds /project1/sw_cut: cuts between scene networks in time with the music.
# Run inside TouchDesigner:  exec(open(<this file>).read()); build()
# Rebuilding destroys and recreates the COMP, so this file is the source of truth.
# The decisions live in cutlogic.py (tested by tests/test_cutlogic.py); this file
# wires them to the hub, two Switch TOPs and the picture layer (shaders/mix.frag).
import td

REPO = td.project.folder.replace(chr(92), "/")  # the repo is where the project file is saved
HERE = REPO + "/experiments/sw_cut"
CUT = "/project1/sw_cut"

# Index order matters: mix.frag switches on these positions. Index 0 is none / cut.
TREATMENTS = ["", "mirror", "kaleido", "rgb", "poster", "punch", "tiles", "negative", "slices", "triptych", "lines"]
TRANSITIONS = ["cut", "flash", "whip", "blocks", "strobe", "luma", "fall", "bands", "negsnap"]
LAYER_MODES = ["", "matte", "difference", "split", "inset", "screen", "interleave"]
TRANSITION_SECONDS = 0.32

# Runs once a frame: asks cutlogic what is on screen, tells the hub (so only that
# scene cooks), gives the next scene its take and cooks it off screen before the
# cut, and drives the picture layer.
DRIVER = '''def onFrameStart(frame):
    comp = parent()
    hub = op('/project1/sw_hub')
    feed = hub.op('feed') if hub else None
    if feed is None or feed.numChans == 0:
        return
    logic = mod('cutlogic')
    rows = comp.op('scenes').rows()[1:]
    scenes = [(r[0].val, float(r[1].val), float(r[2].val)) for r in rows if op('/project1/' + r[0].val)]
    names = [s[0] for s in scenes]
    if not names:
        return
    par = comp.par
    state = comp.fetch('state', None) or logic.new_state()
    treatments = comp.fetch('treatments')
    transitions = comp.fetch('transitions')
    layer_modes = comp.fetch('layer_modes')
    now = absTime.seconds
    cut = False
    before = state['scene']

    if par.Auto.eval():
        values = {
            'energy': float(feed['energy'][0]),
            'section': float(feed['section'][0]),
            'section_pos': float(feed['section_pos'][0]),
            'bar_i': int(feed['bar_i'][0]),
            'bar': float(feed['bar'][0]),
            'beat_i': int(feed['beat_i'][0]),
        }
        looks = par.Looks.eval()
        cfg = {
            'loud': par.Loud.eval(), 'bars_loud': par.Barsloud.eval(), 'min_bars': par.Minbars.eval(),
            'treatments': treatments[1:], 'treat_chance': par.Treatchance.eval() * looks,
            'transitions': transitions[1:], 'trans_chance': par.Transchance.eval() * looks,
            'layer_modes': layer_modes[1:], 'layer_chance': par.Layerchance.eval() * looks,
        }
        had_next = state['next']
        cut = logic.step(state, values, scenes, cfg)
        if state['next'] and state['next'] != had_next:
            _dress(op('/project1/' + state['next']), state['next_plan'])
    else:
        want = names[int(par.Manual.eval()) % len(names)]
        plan = dict(state['shot'], treat=treatments[int(par.Mantreat.eval()) % len(treatments)],
                    trans='cut', layer='', layer_mode='', take=int(par.Mantake.eval()), seed=par.Manseed.eval())
        if want != state['scene'] or plan != state['shot']:
            cut = want != state['scene']
            state['scene'], state['next'], state['next_plan'] = want, '', None
            state['shot'] = plan
            _dress(op('/project1/' + want), plan)

    shot = state['shot']
    scene = state['scene']
    if cut:
        comp.store('cuts', comp.fetch('cuts', 0) + 1)
        comp.store('cut_time', now)
        comp.store('prev', before)
        target = op('/project1/' + scene)
        if target is not None and hasattr(target.par, 'Shotstart'):
            _dress(target, shot)
            target.par.Shotstart = now
        log = comp.fetch('log', [])
        log.append((round(float(feed['t'][0]), 2), scene, shot['take'], shot['treat'], shot['trans'], shot['layer'], shot['layer_mode']))
        comp.store('log', log[-400:])
    comp.store('state', state)

    age = now - comp.fetch('cut_time', now)
    progress = 1.0 if shot['trans'] == 'cut' else min(1.0, age / comp.fetch('transition_seconds', 0.32))
    in_transition = progress < 1.0
    layer = shot.get('layer') or ''
    if layer and layer not in names:
        layer = ''

    if scene in names:
        if hub.par.Scene.eval() != scene:
            hub.par.Scene = scene
        comp.op('switch_a').par.index = names.index(scene)
    # B is the outgoing scene (its last frame stays in its out1) during a transition,
    # then the layered scene.
    prev = comp.fetch('prev', '')
    b_scene = prev if (in_transition and prev in names) else (layer or prev or scene)
    if b_scene in names:
        comp.op('switch_b').par.index = names.index(b_scene)

    live = []
    if layer and not in_transition:
        lay = op('/project1/' + layer)
        if hasattr(lay.par, 'Shotstart') and lay.par.Shotstart.eval() < comp.fetch('cut_time', now):
            lay.par.Take = int(shot['seed'] * 997) % 6
            lay.par.Seed = (shot['seed'] * 7.31) % 1.0
            lay.par.Shotstart = comp.fetch('cut_time', now)
        live.append(layer)
    warm = state.get('next')
    if warm and warm != scene and warm in names:
        live.append(warm)
    for name in live:
        if name != scene:
            op('/project1/' + name + '/hub').cook(force=True)
            op('/project1/' + name + '/out1').cook(force=True)

    mix = comp.op('mix')
    mix.par.vec0valuex = treatments.index(shot['treat']) if shot['treat'] in treatments else 0
    mix.par.vec0valuey = transitions.index(shot['trans']) if shot['trans'] in transitions else 0
    mix.par.vec0valuez = (layer_modes.index(shot['layer_mode']) if shot['layer_mode'] in layer_modes else 0) if layer else 0
    mix.par.vec0valuew = shot['seed']
    mix.par.vec1valuex = progress
    mix.par.vec1valuey = age
    comp.op('out1').cook(force=True)
    if comp.op('rec').par.record.eval():
        comp.op('rec').cook(force=True)
    return


def _dress(target, plan):
    """Give a scene its take and seed for the coming shot (before it is seen)."""
    if target is None or plan is None or not hasattr(target.par, 'Take'):
        return
    target.par.Take = int(plan['take'])
    target.par.Seed = float(plan['seed'])
'''


def record(file, seconds, from_start=True):
    """Record the cut with the track's audio. Returns at once; the Movie File Out
    stops itself after `seconds`. Read tdh.errors right after: a codec that needs
    a licence fails silently otherwise."""
    cut = op(CUT)
    rec = cut.op("rec")
    rec.par.record = False
    rec.par.file = file
    rec.par.length = seconds
    if from_start:
        op("/project1/sw_hub/audio").par.cuepulse.pulse()
        cut.store("state", None)
        cut.store("log", [])
        cut.store("cuts", 0)
    rec.par.record = True
    return file


def build(scenes=None, loud=0.58):
    """scenes: {name: (energy_min, energy_max)}; default every /project1/sc_* at any energy."""
    root = op("/project1")
    old = op(CUT)
    if old:
        old.destroy()
    cut = root.create(td.baseCOMP, "sw_cut")
    cut.nodeX, cut.nodeY = -600, 100
    if scenes is None:
        # scenes.json: each scene's energy band (from its art director's notes) and take count.
        import json

        listed = json.loads(open(HERE + "/scenes.json", encoding="utf-8").read())
        scenes = {n: (v["energy_min"], v["energy_max"]) for n, v in listed.items() if root.op(n) and root.op(n).op("out1")}

    page = cut.appendCustomPage("Cut")
    page.appendToggle("Auto", label="Cut With The Music")[0].val = True
    page.appendFloat("Loud", label="Loud Above (energy)")[0].val = loud
    page.appendInt("Barsloud", label="Bars Per Cut When Loud")[0].val = 2
    page.appendFloat("Minbars", label="Shortest Shot (bars)")[0].val = 1
    page.appendFloat("Looks", label="Looks Amount (0 = clean cuts only)")[0].val = 1
    page.appendFloat("Treatchance", label="Share Of Shots Treated")[0].val = 0.4
    page.appendFloat("Transchance", label="Share Of Cuts With A Transition")[0].val = 0.5
    page.appendFloat("Layerchance", label="Share Of Shots With Two Scenes")[0].val = 0.14
    manual = cut.appendCustomPage("Manual")
    manual.appendInt("Manual", label="Scene")[0].val = 0
    manual.appendInt("Mantake", label="Take")[0].val = 0
    manual.appendFloat("Manseed", label="Seed")[0].val = 0
    manual.appendInt("Mantreat", label="Treatment")[0].val = 0

    table = cut.create(td.tableDAT, "scenes")
    table.clear()
    table.appendRow(["scene", "energy_min", "energy_max"])
    for name, (lo, hi) in scenes.items():
        table.appendRow([name, lo, hi])

    logic = cut.create(td.textDAT, "cutlogic")
    logic.par.file.expr = "project.folder.replace(chr(92), '/') + '/experiments/sw_cut/cutlogic.py'"
    logic.par.syncfile = True
    logic.par.loadonstartpulse.pulse()

    switch_a = cut.create(td.switchTOP, "switch_a")
    switch_b = cut.create(td.switchTOP, "switch_b")
    for i, name in enumerate(scenes):
        sel = cut.create(td.selectTOP, "in_" + name)
        sel.par.top = "/project1/" + name + "/out1"
        sel.nodeX, sel.nodeY = 0, -i * 110
        sel.outputConnectors[0].connect(switch_a)
        sel.outputConnectors[0].connect(switch_b)
    switch_a.nodeX, switch_a.nodeY = 250, 0
    switch_b.nodeX, switch_b.nodeY = 250, -200

    fits = []
    for i, sw in enumerate((switch_a, switch_b)):
        fit = cut.create(td.fitTOP, "fit_" + "ab"[i])
        fit.par.outputresolution = "custom"
        fit.par.resolutionw, fit.par.resolutionh = 1280, 720
        sw.outputConnectors[0].connect(fit)
        fit.nodeX, fit.nodeY = 450, -200 * i
        fits.append(fit)

    frag = cut.create(td.textDAT, "mix_frag")
    frag.par.file.expr = "project.folder.replace(chr(92), '/') + '/experiments/sw_cut/shaders/mix.frag'"
    frag.par.syncfile = True
    frag.par.loadonstartpulse.pulse()
    mix = cut.create(td.glslTOP, "mix")
    for docked in list(mix.docked):
        if docked.name in ("mix_pixel", "mix_compute"):
            docked.destroy()
    mix.par.pixeldat = "mix_frag"
    mix.par.outputresolution = "custom"
    mix.par.resolutionw, mix.par.resolutionh = 1280, 720
    mix.par.format = "rgba16float"
    fits[0].outputConnectors[0].connect(mix.inputConnectors[0])
    fits[1].outputConnectors[0].connect(mix.inputConnectors[1])
    mix.seq.vec.numBlocks = 3
    mix.par.vec0name, mix.par.vec1name, mix.par.vec2name = "uShot", "uTime", "uAudio"
    feed = "op('/project1/sw_hub/feed')"
    mix.par.vec1valuex = 1
    mix.par.vec1valuez.expr = feed + "['beat_pos']"
    mix.par.vec1valuew.expr = feed + "['bar_pos']"
    mix.par.vec2valuex.expr = feed + "['pulse']"
    mix.par.vec2valuey.expr = feed + "['hit_low']"
    mix.par.vec2valuez.expr = feed + "['hit_mid']"
    mix.par.vec2valuew.expr = feed + "['energy']"
    mix.nodeX, mix.nodeY = 650, 0

    out1 = cut.create(td.outTOP, "out1")
    mix.outputConnectors[0].connect(out1)
    out1.nodeX = 850

    rec = cut.create(td.moviefileoutTOP, "rec")
    # h264/h265 need a Commercial licence ("GPU Accelerated H.264/H.265 Encoding
    # requires a Commercial license"); Motion JPEG records, then ffmpeg converts.
    rec.par.videocodec = "mjpa"
    rec.par.audiochop = "/project1/sw_hub/audio"
    rec.par.audiocodec = "aac"
    rec.par.limitlength = True
    rec.par.lengthunit = "seconds"
    mix.outputConnectors[0].connect(rec)
    rec.nodeX, rec.nodeY = 850, -150

    driver = cut.create(td.executeDAT, "cook_driver")
    driver.text = DRIVER
    driver.par.framestart = True
    driver.par.active = True
    driver.nodeX, driver.nodeY = 250, 200
    cut.store("state", None)
    cut.store("cuts", 0)
    cut.store("log", [])
    cut.store("prev", "")
    cut.store("cut_time", 0.0)
    cut.store("treatments", TREATMENTS)
    cut.store("transitions", TRANSITIONS)
    cut.store("layer_modes", LAYER_MODES)
    cut.store("transition_seconds", TRANSITION_SECONDS)
    return cut.path
