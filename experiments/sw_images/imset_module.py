# Installed in every image template as the module DAT local/modules/imset, so any
# parameter inside can ask the prepared set (tools/imageprep/prepare.py) for a file:
#
#     mod.imset.path(op('state')['i0'], 'file')     the picture at that place in colour order
#     mod.imset.path(3, 'depth')                    its depth map;  'cutout' its cut-out
#     mod.imset.cell(3, 'aspect')                   any column of table.tsv
#     mod.imset.root('atlas.png')                   a file of the set itself
#
# The set is the folder named by the template COMP's Folder control. A relative
# folder is read against the repository (the folder the project file is saved in).


def _comp():
    return me.parent(3)  # noqa: F821  `me` is this DAT inside TouchDesigner


def root(rel=""):
    folder = str(_comp().par.Folder.eval()).replace(chr(92), "/").rstrip("/")
    if not folder:
        return ""
    if not (folder.startswith("/") or folder[1:2] == ":"):
        folder = project.folder.replace(chr(92), "/") + "/" + folder  # noqa: F821
    return folder + ("/" + rel if rel else "")


def count():
    table = _comp().op("table")
    return max(0, table.numRows - 1) if table is not None else 0


def cell(i, col, fallback=""):
    n = count()
    if n == 0:
        return fallback
    hit = _comp().op("table")[1 + int(i) % n, col]
    return hit.val if hit is not None else fallback


def number(i, col, fallback=1.0):
    try:
        return float(cell(i, col, fallback))
    except ValueError:
        return fallback


def path(i, col="file"):
    rel = cell(i, col)
    return root(rel) if rel else ""
