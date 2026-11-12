# Where things are. No file in this project names a folder on anyone's machine.
#
# This file is loaded two ways:
#   - as a module DAT at <component>/local/modules/paths, so any parameter inside
#     that component can say   mod.paths.here('shaders/a.frag')   or
#     mod.paths.font('chicago')   as an expression. Because it is an expression,
#     the saved .tox and the text snapshot hold the expression, not a folder.
#   - by scene_lib.py, for builder scripts.
#
# The repository is wherever the open project file (lab.toe) is saved; the README
# puts it at the repo root. Assets are optional and live in one folder:
#
#   <repo>/assets/                 or the folder named by the TDH_ASSETS variable
#       models/<slug>/model.obj, basecolor.png      3D models (tools/models/convert_models.py)
#       fonts/<file>.ttf                            typefaces
#       art/<file>.png                              lettering and marks
#       music/<track>.wav|mp3                       tracks
#       feeds/<track>/feed.chan, feed.json          their analysis (tools/audiofeed/bake_feed.py)
#       scenes/<slug>/words.json                    optional: that scene's words (see words())
#       scenes/<slug>/<file>                        optional: replaces a file of that scene (see scene_file())
#
# Everything must work with that folder missing: a missing model is TouchDesigner's
# own teapot, a missing font is its default face, a missing picture is an empty path.
import os

FONT_FILES = {
    "chicago": "fonts/ChicagoFLF.ttf",
    "archivo": "fonts/ArchivoBlack-Regular.ttf",
    "barlow": "fonts/BarlowCondensed-Bold.ttf",
}


def _slashes(path):
    return str(path).replace(chr(92), "/")


def repo():
    """The repository folder: where the open project file is saved."""
    return _slashes(project.folder)  # noqa: F821  `project` is a TouchDesigner global


def _component():
    """The component this module DAT is installed in, or None outside TouchDesigner's DAT."""
    try:
        return me.parent(3)  # noqa: F821  `me` is this DAT inside TouchDesigner
    except Exception:  # noqa: BLE001  not a DAT (builder scripts, tests)
        return None


def assets():
    """The assets folder (it may not exist).

    In order: the component's own `Assets` parameter if it has one and it is set
    (used to try a scene with no assets without touching anything else), then the
    TDH_ASSETS environment variable, then the folder named on the first line of
    <repo>/assets.local.txt (not in git: for a pack you keep to yourself), then
    <repo>/assets (the pack that ships with the repository).
    """
    comp = _component()
    override = getattr(getattr(comp, "par", None), "Assets", None)
    if override is not None:
        value = str(override.eval()).strip()
        if value:
            return _slashes(value)
    return _slashes(os.environ.get("TDH_ASSETS") or _local_pack() or repo() + "/assets")


def _local_pack():
    """The folder named in <repo>/assets.local.txt, when that file and folder exist."""
    try:
        with open(repo() + "/assets.local.txt", encoding="utf-8") as fh:
            line = fh.readline().strip()
    except OSError:
        return ""
    return _slashes(line) if line and os.path.isdir(line) else ""


_ALIASES = {}  # assets folder -> (mtime of aliases.json, {requested prefix: stand-in prefix})


def _aliases(folder):
    """A pack may hold aliases.json: {"models/crt": "models/monitor", "fonts/A.ttf": "fonts/B.ttf"}.
    A scene asks for a file by one name; the pack answers with the file it has."""
    path = folder + "/aliases.json"
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return {}
    cached = _ALIASES.get(folder)
    if cached and cached[0] == stamp:
        return cached[1]
    import json

    try:
        with open(path, encoding="utf-8") as fh:
            table = {str(k).strip("/"): str(v).strip("/") for k, v in json.load(fh).items()}
    except (OSError, ValueError):
        table = {}
    _ALIASES[folder] = (stamp, table)
    return table


def asset(rel, fallback=""):
    """Path of a file under the assets folder, or `fallback` when it is not there.

    If the file is missing and the pack's aliases.json names a stand-in for it
    (or for a folder it is in), the stand-in is returned instead.
    """
    folder = assets()
    path = folder + "/" + rel
    if os.path.exists(path):
        return path
    table = _aliases(folder)
    for key in sorted(table, key=len, reverse=True):
        if rel == key or rel.startswith(key + "/"):
            other = folder + "/" + table[key] + rel[len(key):]
            if os.path.exists(other):
                return other
    return fallback


def have(rel):
    """True when the assets folder holds this file (or a stand-in for it)."""
    return bool(asset(rel))


def font(name):
    """Font file for 'chicago', 'archivo' or 'barlow', or '' (TouchDesigner's default face) when missing."""
    return asset(FONT_FILES[name])


def samples():
    """TouchDesigner's own bundled samples folder."""
    return _slashes(app.samplesFolder)  # noqa: F821  `app` is a TouchDesigner global


def model_file(slug):
    """A library model's OBJ, or TouchDesigner's bundled teapot when the library is not there."""
    return asset("models/%s/model.obj" % slug, samples() + "/Geo/UtahTeapot.obj")


def model_texture(slug):
    """A library model's base colour image, or '' when the library is not there."""
    return asset("models/%s/basecolor.png" % slug)


def experiment(slug, rel=""):
    """A file in an experiment's folder in the repo."""
    return repo() + "/experiments/" + slug + ("/" + rel if rel else "")


def scene_file(rel, slug=None):
    """A file a scene keeps in its own folder, unless the pack has its own copy.

    A pack may hold scenes/<slug>/<rel> (for example baked data made from that
    pack's models). When it does, that file is used instead of the scene's.
    """
    slug = slug or me.parent(3).name  # noqa: F821
    return asset("scenes/%s/%s" % (slug, rel)) or experiment(slug, rel)


def words(defaults, slug=None):
    """A scene's words: `defaults` (a dict of name -> text, list or dict), with any
    name replaced by the pack's scenes/<slug>/words.json when the pack has one.

    Only names the scene already has are taken, and a replacement must be the same
    kind of thing (text for text, list for list), so a pack cannot break a scene.
    """
    slug = slug or me.parent(3).name  # noqa: F821
    out = dict(defaults)
    path = asset("scenes/%s/words.json" % slug)
    if not path:
        return out
    import json

    with open(path, encoding="utf-8") as fh:
        theirs = json.load(fh)
    for key, value in theirs.items():
        if key not in defaults:
            continue
        if type(value) is not type(defaults[key]):
            raise ValueError("%s: %r must be a %s, as in the scene" % (path, key, type(defaults[key]).__name__))
        out[key] = value
    return out


def here(rel=""):
    """A file in the folder of the experiment this module DAT sits in
    (<component>/local/modules/paths, so the component is three levels up)."""
    return experiment(me.parent(3).name, rel)  # noqa: F821  `me` is this DAT inside TouchDesigner
