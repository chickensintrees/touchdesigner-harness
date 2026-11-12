# Builds /project1/sw_panel: one page of controls for the whole engine, so nobody
# has to read the network. Run inside TouchDesigner:
#     exec(open(<this file>).read()); build(); show()
# Rebuilding destroys and recreates the COMP; this file is the source of truth.
#
# The panel owns no picture logic. Its parameters are written through to the
# cutter (/project1/sw_cut), the hub (/project1/sw_hub) and the scenes by the
# Parameter Execute DAT below, and its read-outs are refreshed from the cutter.
import json

import td

REPO = td.project.folder.replace(chr(92), "/")  # the repo is where the project file is saved
PANEL = "/project1/sw_panel"


def _tracks():
    """Track slugs the hub can play: your own (assets/music with a feed) and the bundled sample."""
    g = {"op": op, "td": td, "__name__": "sw_hub_build"}
    exec(open(REPO + "/experiments/sw_hub/build.py", encoding="utf-8").read(), g)
    return list(g["tracks"]())


PAREXEC = '''import json

CUT = '/project1/sw_cut'
HUB = '/project1/sw_hub'
REPO = project.folder.replace(chr(92), '/')


def _scenes():
    return [r[0].val for r in op(CUT).op('scenes').rows()[1:]]


def _push_manual(panel):
    cut = op(CUT)
    names = _scenes()
    scene = panel.par.Scene.eval()
    if scene in names:
        cut.par.Manual = names.index(scene)
    cut.par.Mantake = int(panel.par.Take.eval())
    cut.par.Manseed = float(panel.par.Seed.eval())
    cut.par.Mantreat = panel.par.Treatment.menuIndex


def _step_scene(panel, by):
    names = panel.par.Scene.menuNames
    i = (names.index(panel.par.Scene.eval()) + by) % len(names)
    panel.par.Auto = False
    panel.par.Scene = names[i]
    panel.par.Take = 0


def onValueChange(par, prev):
    panel = par.owner
    cut, hub = op(CUT), op(HUB)
    name = par.name
    if name == 'Auto':
        cut.par.Auto = bool(par.eval())
        if not par.eval():
            _push_manual(panel)
    elif name in ('Scene', 'Take', 'Seed', 'Treatment'):
        if name == 'Scene':
            takes = panel.fetch('cards', {}).get(par.eval(), {}).get('takes', [])
            panel.par.Take.normMax = max(1, len(takes) - 1)
        if not panel.par.Auto.eval():
            _push_manual(panel)
    elif name == 'Describe':
        for scene in _scenes():
            target = op('/project1/' + scene)
            if target is not None and hasattr(target.par, 'Describe'):
                target.par.Describe = bool(par.eval())
    elif name == 'Looks':
        cut.par.Looks = float(par.eval())
    elif name == 'Shotbars':
        cut.par.Minbars = float(par.eval())
    elif name == 'Volume':
        hub.par.Volume = float(par.eval())
    elif name == 'Track':
        g = {'op': op, 'td': td, '__name__': 'sw_hub_build'}
        exec(open(REPO + '/experiments/sw_hub/build.py', encoding='utf-8').read(), g)
        g['set_track'](par.eval())
        cut.store('state', None)
    return


def onPulse(par):
    panel = par.owner
    name = par.name
    if name == 'Nextscene':
        _step_scene(panel, 1)
    elif name == 'Prevscene':
        _step_scene(panel, -1)
    elif name == 'Nexttake':
        panel.par.Auto = False
        takes = panel.fetch('cards', {}).get(panel.par.Scene.eval(), {}).get('takes', [])
        panel.par.Take = (int(panel.par.Take.eval()) + 1) % max(1, len(takes))
    elif name == 'Newseed':
        import random
        panel.par.Seed = round(random.random(), 3)
    elif name == 'Restart':
        op(HUB).op('audio').par.cuepulse.pulse()
        op(CUT).store('state', None)
    elif name == 'Showoutput':
        op(CUT).op('out1').openViewer(unique=False, borders=True)
    elif name == 'Showpanel':
        panel.openParameters()
    return
'''

# Keeps the read-outs honest while the cutter runs itself.
READOUT = '''def onFrameStart(frame):
    if absTime.frame % 6:
        return
    panel = parent()
    cut = op('/project1/sw_cut')
    state = cut.fetch('state', None) if cut else None
    if not state:
        return
    scene, shot = state.get('scene', ''), state.get('shot', {})
    card = panel.fetch('cards', {}).get(scene, {})
    takes = card.get('takes', [])
    take = int(shot.get('take', 0)) % max(1, len(takes)) if takes else 0
    panel.par.Nowscene = card.get('title', scene)
    panel.par.Nowtake = '%d  %s' % (take, takes[take]['name'] if takes else '')
    panel.par.Nowlook = ' / '.join(x for x in (shot.get('treat', ''), shot.get('trans', ''), shot.get('layer', '')) if x and x != 'cut') or 'clean'
    words = takes[take].get('words', []) if takes else []
    panel.par.Nowwords = ' | '.join(words)[:200]
    return
'''


def build():
    root = op("/project1")
    old = op(PANEL)
    if old:
        old.destroy()
    panel = root.create(td.baseCOMP, "sw_panel")
    panel.nodeX, panel.nodeY = -350, -500
    panel.color = (0.9, 0.35, 0.2)

    listed = json.loads(open(REPO + "/experiments/sw_cut/scenes.json", encoding="utf-8").read())
    cards = {}
    for slug in listed:
        cards[slug] = json.loads(open(REPO + "/experiments/" + slug + "/preset.json", encoding="utf-8").read())
    panel.store("cards", cards)
    cut = op("/project1/sw_cut")
    scenes = [r[0].val for r in cut.op("scenes").rows()[1:]]
    treatments = cut.fetch("treatments")

    page = panel.appendCustomPage("Engine")
    page.appendToggle("Auto", label="Cut With The Music")[0].val = bool(cut.par.Auto.eval())
    p = page.appendMenu("Scene", label="Scene")[0]
    p.menuNames = scenes
    p.menuLabels = [cards[s]["title"] for s in scenes]
    p = page.appendInt("Take", label="Take")[0]
    p.normMin, p.normMax, p.min, p.clampMin = 0, 13, 0, True
    p = page.appendFloat("Seed", label="Seed (variation inside the take)")[0]
    p.normMin, p.normMax = 0, 1
    p = page.appendMenu("Treatment", label="Treatment")[0]
    p.menuNames = [t or "none" for t in treatments]
    p.menuLabels = [(t or "none").capitalize() for t in treatments]
    page.appendPulse("Prevscene", label="Previous Scene")
    page.appendPulse("Nextscene", label="Next Scene")
    page.appendPulse("Nexttake", label="Next Take")
    page.appendPulse("Newseed", label="New Seed")
    page.appendToggle("Describe", label="Words Describe The Technique")[0].val = False

    p = page.appendFloat("Looks", label="Looks Amount (auto: treatments, transitions, layers)")[0]
    p.normMin, p.normMax = 0, 2
    p.val = float(cut.par.Looks.eval())
    p = page.appendFloat("Shotbars", label="Shortest Shot (bars, auto)")[0]
    p.normMin, p.normMax = 0.5, 8
    p.val = float(cut.par.Minbars.eval())

    p = page.appendMenu("Track", label="Track")[0]
    names = _tracks()
    p.menuNames = names
    p.menuLabels = [n.replace("_", " ").title() for n in names]
    current = op("/project1/sw_hub").par.Track.eval()
    p.val = current if current in names else names[0]
    p = page.appendFloat("Volume", label="Speaker Volume")[0]
    p.normMin, p.normMax = 0, 1
    p.val = float(op("/project1/sw_hub").par.Volume.eval())
    page.appendPulse("Restart", label="Restart Track")
    page.appendPulse("Showoutput", label="Open Output Window")

    now = panel.appendCustomPage("Now Showing")
    for name, label in (("Nowscene", "Scene"), ("Nowtake", "Take"), ("Nowlook", "Look"), ("Nowwords", "Words On Screen")):
        q = now.appendStr(name, label=label)[0]
        q.readOnly = True
    now.appendPulse("Showpanel", label="Open This Panel As A Window")

    pe = panel.create(td.parameterexecuteDAT, "panel_exec")
    pe.text = PAREXEC
    pe.par.op = PANEL
    pe.par.pars = "*"
    pe.par.valuechange = True
    pe.par.onpulse = True
    pe.par.active = True
    ro = panel.create(td.executeDAT, "readout")
    ro.text = READOUT
    ro.par.framestart = True
    ro.par.active = True
    ro.nodeX = 200
    return panel.path


def show():
    """Float the panel and the picture as two windows."""
    op(PANEL).openParameters()
    op("/project1/sw_cut").op("out1").openViewer(unique=False, borders=True)
    return PANEL
