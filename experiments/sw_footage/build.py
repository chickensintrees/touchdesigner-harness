# Builds /project1/sw_footage: plays a folder of video clips as found footage, one
# clip per channel, and changes channel by hand or in time with the music. The
# change itself is one of the cutter's transitions (experiments/sw_cut/shaders/mix.frag);
# the default is "tune": the picture rolls, tears, drops to snow and locks onto
# the next channel. Its out1 is an ordinary 1280x720 picture, so it can be the
# Input of the finish, of the screen in a room, or of any scene.
#
# Run inside TouchDesigner:
#     g = {'op': op, 'td': td, '__name__': 'build'}
#     exec(open(project.folder + '/experiments/sw_footage/build.py', encoding='utf-8').read(), g)
#     g['build']()
import td

SLUG = "sw_footage"
DEFAULT_FOLDER = "assets/footage"  # read against the repository unless it is a full path
# The same order as experiments/sw_cut/build.py: mix.frag switches on these positions.
TRANSITIONS = ["cut", "flash", "whip", "blocks", "strobe", "luma", "fall", "bands", "negsnap", "tune"]
LABELS = ["Hard Cut", "Flash", "Whip", "Blocks", "Strobe", "Dark Parts First", "Fall Through", "Bands", "Negative Snap", "Change Channel (tune)"]

# Two players take turns: one shows the channel that is on, the other keeps the
# channel that was on (for the transition) and then loads the one that comes next.
DRIVER = '''def onFrameStart(frame):
    comp = parent()
    par = comp.par
    logic = op('channels').module
    files = op('files')
    count = max(1, files.numRows - 1)
    feed = op('hub')
    music = par.Follow.eval() and feed.numChans > 0
    n = logic.channel_at(feed['bar_pos'].eval(), par.Bars.eval()) if music else 0
    first, step = int(par.Clip.eval()), int(par.Step.eval())
    want = logic.clip_for(n, first, step, count)
    state = op('state')
    slot = int(state['slot'].eval())
    now = absTime.seconds
    restart = par.Shotstart.eval()
    if int(state['clip%d' % slot].eval()) != want or restart != comp.fetch('restart', restart, search=False):
        comp.store('restart', restart)
        other = 1 - slot
        state.par['const%dvalue' % (1 + other)] = want
        state.par['const%dvalue' % (3 + other)] = now
        state.par.const0value = other
        state.par.const5value = now
        comp.store('changes', comp.fetch('changes', 0, search=False) + 1)
        comp.store('ahead', False)
    elif not comp.fetch('ahead', False, search=False) and now - state['cut'].eval() > par.Transtime.eval() + 0.1:
        # the transition is over: the idle player opens the next channel's clip now, so the change does not wait for the file
        other = 1 - slot
        state.par['const%dvalue' % (1 + other)] = logic.clip_for(n + 1, first, step, count)
        state.par['const%dvalue' % (3 + other)] = 0
        comp.store('ahead', True)
    if par.Preview.eval():
        op('out1').cook(force=True)
    return
'''


def _slider(page, name, label, value, top, low=0.0):
    p = page.appendFloat(name, label=label)[0]
    p.normMin, p.normMax = low, top
    p.default = value
    p.val = value
    return p


def build(folder=""):
    repo = td.project.folder.replace(chr(92), "/")
    SCENE = {"op": op}  # noqa: F821
    exec(open(repo + "/experiments/sw_hub/scene_lib.py", encoding="utf-8").read(), SCENE)
    root = op("/project1")  # noqa: F821
    old = root.op(SLUG)
    if old:
        if not folder and hasattr(old.par, "Folder"):
            folder = old.par.Folder.eval()
        old.destroy()
    c = root.create(td.baseCOMP, SLUG)
    c.nodeX, c.nodeY = 1050, -1700
    SCENE["add_paths"](c)

    page = c.appendCustomPage("Controls")
    page.appendStr("Folder", label="Folder Of Clips")[0].val = folder or DEFAULT_FOLDER
    page.appendInt("Clip", label="First Clip (which clip channel 0 shows)")[0].val = 0
    page.appendToggle("Follow", label="Change Channel With The Music")[0].val = True
    _slider(page, "Bars", "Bars Per Channel", 2.0, 8.0, 0.5)
    page.appendInt("Step", label="Clips To Skip Between Channels")[0].val = 7
    m = page.appendMenu("Transition", label="How The Channel Changes")[0]
    m.menuNames = TRANSITIONS
    m.menuLabels = LABELS
    m.val = "tune"
    _slider(page, "Transtime", "Seconds A Change Takes", 0.45, 1.5, 0.1)
    _slider(page, "Speed", "Playback Speed", 1.0, 2.0, 0.25)
    page.appendFloat("Shotstart", label="Shot Start (set it to restart the clip)")[0].val = 0
    page.appendToggle("Preview", label="Preview (cook when not on screen)")[0].val = True

    hub = c.create(td.selectCHOP, "hub")
    hub.par.chop = "/project1/sw_hub/feed"
    files = c.create(td.folderDAT, "files")
    files.par.rootfolder.expr = (
        "(lambda f: f if (f.startswith('/') or f[1:2] == ':') else project.folder.replace(chr(92), '/') + '/' + f)"
        "(str(parent().par.Folder.eval()).replace(chr(92), '/').rstrip('/'))"
    )
    files.par.allextensions = False
    files.par.movieextensions = True
    logic = c.create(td.textDAT, "channels")
    logic.par.file.expr = "mod.paths.experiment('%s', 'channels.py')" % SLUG
    logic.par.syncfile = True
    logic.par.loadonstartpulse.pulse()

    state = c.create(td.constantCHOP, "state")
    state.seq.const.numBlocks = 6
    for i, (name, value) in enumerate([("slot", 0), ("clip0", 0), ("clip1", 1), ("start0", 0), ("start1", 0), ("cut", -10)]):
        setattr(state.par, "const%dname" % i, name)
        setattr(state.par, "const%dvalue" % i, value)

    players = []
    for i in range(2):
        mv = c.create(td.moviefileinTOP, "play%d" % i)
        mv.par.file.expr = (
            "(lambda t, r: t[1 + r %% max(1, t.numRows - 1), 'path'].val if t.numRows > 1 else '')(op('files'), int(op('state')['clip%d']))" % i
        )
        mv.par.playmode = "specify"
        mv.par.indexunit = "seconds"
        mv.par.textendright = "cycle"
        # the frame comes from the clock, not from the player, so a recording made off the clock gets every frame in order
        # (in seconds and cycled by the player itself: asking the player for its own length here is a cook loop)
        mv.par.index.expr = "max(0, absTime.seconds - op('state')['start%d']) * parent().par.Speed" % i
        mv.par.outputresolution = "custom"
        mv.par.resolutionw, mv.par.resolutionh = 1280, 720
        players.append(mv)

    on = c.create(td.switchTOP, "on")
    was = c.create(td.switchTOP, "was")
    for mv in players:
        mv.outputConnectors[0].connect(on)
        mv.outputConnectors[0].connect(was)
    on.par.index.expr = "op('state')['slot']"
    was.par.index.expr = "1 - op('state')['slot']"

    frag = c.create(td.textDAT, "mix_frag")
    frag.par.file.expr = "mod.paths.experiment('sw_cut', 'shaders/mix.frag')"
    frag.par.syncfile = True
    frag.par.loadonstartpulse.pulse()
    mix = c.create(td.glslTOP, "mix")
    for d in list(mix.docked):
        d.destroy()
    mix.par.pixeldat = frag.name
    mix.par.outputresolution = "custom"
    mix.par.resolutionw, mix.par.resolutionh = 1280, 720
    mix.par.format = "rgba8fixed"
    on.outputConnectors[0].connect(mix.inputConnectors[0])
    was.outputConnectors[0].connect(mix.inputConnectors[1])
    AGE = "(absTime.seconds - op('state')['cut'])"
    rows = [
        ("uShot", [0, "parent().par.Transition.menuIndex", 0, "(op('state')['cut'] * 0.37) % 1"]),
        ("uTime", ["min(1, max(0, %s) / max(0.05, parent().par.Transtime))" % AGE, "max(0, %s)" % AGE,
                   "op('hub')['beat_pos'] if op('hub').numChans else 0", "op('hub')['bar_pos'] if op('hub').numChans else 0"]),
        ("uAudio", [0, 0, 0, 0]),
    ]
    mix.seq.vec.numBlocks = len(rows)
    for i, (name, exprs) in enumerate(rows):
        setattr(mix.par, "vec%dname" % i, name)
        for axis, expr in zip("xyzw", exprs):
            getattr(mix.par, "vec%dvalue%s" % (i, axis)).expr = str(expr)

    out1 = c.create(td.outTOP, "out1")
    mix.outputConnectors[0].connect(out1)
    drv = c.create(td.executeDAT, "driver")
    drv.text = DRIVER
    drv.par.framestart = True
    drv.par.active = True

    hub.nodeX, hub.nodeY = -400, 60
    files.nodeX, files.nodeY = -400, 300
    logic.nodeX, logic.nodeY = -400, -160
    state.nodeX, state.nodeY = -250, 180
    drv.nodeX, drv.nodeY = -400, -60
    for i, mv in enumerate(players):
        mv.nodeX, mv.nodeY = 0, 100 - 200 * i
    on.nodeX, on.nodeY = 250, 100
    was.nodeX, was.nodeY = 250, -100
    frag.nodeX, frag.nodeY = 450, -250
    mix.nodeX, mix.nodeY = 450, 0
    out1.nodeX, out1.nodeY = 700, 0
    return c.path
