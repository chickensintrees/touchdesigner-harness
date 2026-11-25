# Which tracks the hub can play, and where their audio and feeds are.
#
# Installed in the hub as the module DAT local/modules/hub, so the Audio File In
# and the feed File In can find their files with an expression
# (mod.hub.audio(...), mod.hub.feed(...)) and no folder is stored in the .tox.
# Also loaded by sw_hub/build.py.
#
# Your own tracks go in <assets>/music/<slug>.wav (or .mp3 ...) with their feed in
# <assets>/feeds/<slug>/ (tools/audiofeed/bake_feed.py writes it). The sample
# track is TouchDesigner's own bundled one, and its feed ships in sample_feed/.
import os

SAMPLE = "sample"
AUDIO_TYPES = (".wav", ".mp3", ".aif", ".aiff", ".flac", ".m4a")


def _slashes(path):
    return str(path).replace(chr(92), "/")


def _repo():
    return _slashes(project.folder)  # noqa: F821  TouchDesigner global


def _local_pack():
    try:
        with open(_repo() + "/assets.local.txt", encoding="utf-8") as fh:
            line = fh.readline().strip()
    except OSError:
        return ""
    return _slashes(line) if line and os.path.isdir(line) else ""


def _packs():
    """Folders that may hold tracks: your own pack first (TDH_ASSETS, then
    assets.local.txt), then the pack that ships with the repository."""
    found = []
    for folder in (os.environ.get("TDH_ASSETS"), _local_pack(), _repo() + "/assets"):
        if folder and _slashes(folder) not in found:
            found.append(_slashes(folder))
    return found


def tracks():
    """{slug: (audio file, feed folder)} for every track that has both. The sample is always there."""
    found = {SAMPLE: (_slashes(app.samplesFolder) + "/Audio/JeremyCaulfield_www.dumb-unit.com.mp3",  # noqa: F821
                      _repo() + "/experiments/sw_hub/sample_feed")}
    for pack in reversed(_packs()):  # your own pack wins when two packs hold the same track name
        music, feeds = pack + "/music", pack + "/feeds"
        if os.path.isdir(music):
            for name in sorted(os.listdir(music)):
                slug, ext = os.path.splitext(name)
                if ext.lower() in AUDIO_TYPES and os.path.exists(feeds + "/" + slug + "/feed.json"):
                    found[slug] = (music + "/" + name, feeds + "/" + slug)
    return found


def default_track():
    """The track a new hub starts on: the one named in the first pack's
    default_track.txt, else that pack's first track, else the sample."""
    found = tracks()
    for pack in _packs():
        try:
            with open(pack + "/default_track.txt", encoding="utf-8") as fh:
                name = fh.readline().strip()
        except OSError:
            name = ""
        if name in found:
            return name
        own = sorted(t for t, (audio, _) in found.items() if audio.startswith(pack + "/"))
        if own:
            return own[0]
    return SAMPLE


def _entry(slug):
    found = tracks()
    return found.get(str(slug)) or found[SAMPLE]


def audio(slug):
    """The audio file for a track; the sample's if that track is not there."""
    return _entry(slug)[0]


def feed(slug):
    """The feed folder for a track; the sample's if that track is not there."""
    return _entry(slug)[1]


_META = {}  # feed folder -> (mtime of feed.json, its contents)


def _meta(slug):
    import json

    path = feed(slug) + "/feed.json"
    stamp = os.path.getmtime(path)
    cached = _META.get(path)
    if not cached or cached[0] != stamp:
        with open(path, encoding="utf-8") as fh:
            cached = _META[path] = (stamp, json.load(fh))
    return cached[1]


def duration(slug):
    """Length in seconds of a track's feed. The hub's Duration parameter reads this, so
    it is right however the Track parameter was set."""
    meta = _meta(slug)
    return (meta["samples"] - 1) / meta["rate"]


def channels(slug):
    """The feed's channel names, space separated (what the feed's File In CHOP renames to)."""
    return " ".join(_meta(slug)["channels"])
