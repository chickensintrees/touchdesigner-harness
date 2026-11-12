# Builds /project1/sw_hub: the one audio source every scene reads.
# Run inside TouchDesigner:  exec(open(<this file>).read())
# Rebuilding destroys and recreates the COMP, so this file is the source of truth.
import json

import td

HUB = "/project1/sw_hub"
_REPO = td.project.folder.replace(chr(92), "/")
_HUB_MODULE_EXPR = "project.folder.replace(chr(92), '/') + '/experiments/sw_hub/hub_module.py'"

# Track lookup lives in hub_module.py, which is also installed inside the hub as a module DAT.
_hub = {"project": td.project, "app": td.app}
exec(open(_REPO + "/experiments/sw_hub/hub_module.py", encoding="utf-8").read(), _hub)
tracks, default_track, SAMPLE = _hub["tracks"], _hub["default_track"], _hub["SAMPLE"]


DRIVER = '''def onFrameStart(frame):
    op('feed').cook(force=True)
    op('spectex').cook(force=True)
    return
'''

# Derived channels, computed each frame from the looked-up feed row.
DERIVED = {
    "beat": "op('row')['beat_pos'] % 1",
    "bar": "op('row')['bar_pos'] % 1",
    "beat_i": "math.floor(op('row')['beat_pos'])",
    "bar_i": "math.floor(op('row')['bar_pos'])",
    "pulse": "math.exp(-4.0 * (op('row')['beat_pos'] % 1))",
    "bar_pulse": "math.exp(-6.0 * (op('row')['bar_pos'] % 1))",
    "track_pos": "op('tsec')['t'] / max(parent().par.Duration.eval(), 0.01)",
}


def build():
    root = op("/project1")
    old = op(HUB)
    if old:
        old.destroy()
    hub = root.create(td.baseCOMP, "sw_hub")
    hub.nodeX, hub.nodeY = -600, 400

    page = hub.appendCustomPage("Hub")
    page.appendStr("Track", label="Track")[0].val = SAMPLE
    page.appendFloat("Duration", label="Duration (s)")[0].val = 1
    page.appendFloat("Volume", label="Speaker Volume")[0].val = 0
    page.appendStr("Scene", label="Active Scene")
    page.appendToggle("Solo", label="Cook All Scenes")

    # The module DAT that finds each track's files, so no folder is stored in the hub.
    local = hub.create(td.baseCOMP, "local")
    modules = local.create(td.baseCOMP, "modules")
    module = modules.create(td.textDAT, "hub")
    module.par.file.expr = _HUB_MODULE_EXPR
    module.par.syncfile = True
    module.par.loadonstartpulse.pulse()

    audio = hub.create(td.audiofileinCHOP, "audio")
    audio.par.file.expr = "mod.hub.audio(parent().par.Track.eval())"
    audio.par.repeat = "on"

    # Volume is on the speaker output only, so analysis and recordings are unaffected.
    out = hub.create(td.audiodeviceoutCHOP, "audioout")
    out.par.volume.expr = "parent().par.Volume"
    audio.outputConnectors[0].connect(out)

    info = hub.create(td.infoCHOP, "ainfo")
    info.par.op = "audio"

    tsec = hub.create(td.constantCHOP, "tsec")
    tsec.par.name0 = "t"
    tsec.par.value0.expr = "op('ainfo')['true_sample'] / max(op('ainfo')['sample_rate'], 1)"

    feedin = hub.create(td.fileinCHOP, "feedin")
    feedin.par.file.expr = "mod.hub.feed(parent().par.Track.eval()) + '/feed.chan'"
    feedin.par.rateoption = "override"  # "resample" would stretch the 100 Hz rows to 60
    feedin.par.rate = 100
    feedin.par.renamefrom = "*"

    row = hub.create(td.lookupCHOP, "row")
    row.par.index1 = 0
    row.par.index2.expr = "parent().par.Duration"
    tsec.outputConnectors[0].connect(row.inputConnectors[0])
    feedin.outputConnectors[0].connect(row.inputConnectors[1])

    derived = hub.create(td.constantCHOP, "derived")
    for i, (name, expr) in enumerate(DERIVED.items()):
        getattr(derived.par, "name%d" % i).val = name
        getattr(derived.par, "value%d" % i).expr = expr

    # Live analysis straight from the samples (works for tracks with no feed).
    mono = hub.create(td.mathCHOP, "mono")
    mono.par.chanop = "avg"
    audio.outputConnectors[0].connect(mono)
    rms = hub.create(td.analyzeCHOP, "rms")
    rms.par.function = "rmspower"
    mono.outputConnectors[0].connect(rms)
    # The first cook of rms can be NaN, and a Lag or Speed CHOP then holds NaN forever.
    clean = hub.create(td.constantCHOP, "rms_clean")
    clean.par.name0 = "level"
    clean.par.value0.expr = "(lambda v: v if v == v else 0.0)(float(op('rms')[0]))"
    lag = hub.create(td.lagCHOP, "lag")
    lag.par.lag1, lag.par.lag2 = 0.02, 0.3
    clean.outputConnectors[0].connect(lag)
    level = hub.create(td.renameCHOP, "level")
    level.par.renamefrom, level.par.renameto = "*", "level"
    lag.outputConnectors[0].connect(level)

    speed = hub.create(td.speedCHOP, "speed")
    level.outputConnectors[0].connect(speed)
    evolve = hub.create(td.renameCHOP, "evolve")
    evolve.par.renamefrom, evolve.par.renameto = "*", "evolve"
    speed.outputConnectors[0].connect(evolve)

    spectrum = hub.create(td.audiospectrumCHOP, "spectrum")
    mono.outputConnectors[0].connect(spectrum)
    spec = hub.create(td.nullCHOP, "spec")
    spectrum.outputConnectors[0].connect(spec)
    specraw = hub.create(td.choptoTOP, "specraw")
    specraw.par.chop = "spec"
    # The spectrum is 24000 bins wide; keep 0-4.8 kHz, where the music is, at 512 px.
    speccrop = hub.create(td.cropTOP, "speccrop")
    speccrop.par.cropright = 0.2
    specraw.outputConnectors[0].connect(speccrop)
    spectex = hub.create(td.resolutionTOP, "spectex")
    spectex.par.outputresolution = "custom"
    spectex.par.resolutionw, spectex.par.resolutionh = 512, 1
    speccrop.outputConnectors[0].connect(spectex)

    merge = hub.create(td.mergeCHOP, "merge")
    for src in (row, derived, level, evolve):
        src.outputConnectors[0].connect(merge)
    feed = hub.create(td.nullCHOP, "feed")
    merge.outputConnectors[0].connect(feed)

    out1 = hub.create(td.outTOP, "out1")
    spectex.outputConnectors[0].connect(out1)

    driver = hub.create(td.executeDAT, "cook_driver")
    driver.text = DRIVER
    driver.par.framestart = True
    driver.par.active = True

    for i, o in enumerate(hub.children):
        o.nodeX, o.nodeY = (i % 6) * 160, -(i // 6) * 130
    set_track(default_track())
    return hub.path


def set_track(slug):
    """Point the hub at a track and its baked feed, and restart it."""
    hub = op(HUB)
    _, folder = tracks()[slug]
    meta = json.loads(open(folder + "/feed.json", encoding="utf-8").read())
    hub.par.Track = slug
    hub.par.Duration = (meta["samples"] - 1) / meta["rate"]
    hub.op("feedin").par.renameto = " ".join(meta["channels"])
    hub.op("feedin").par.refreshpulse.pulse()
    hub.op("audio").par.cuepulse.pulse()
    return slug
