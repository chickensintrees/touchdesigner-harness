# The title card's layout inside TouchDesigner: the callbacks of the Script DAT `runs`,
# and the lookups its Text TOPs use. The typesetting itself is typeset.py (pure Python).
import os

REPO_FONTS = "/assets/"


def _ts():
    return mod('typeset')  # noqa: F821  `mod` is a TouchDesigner global


def font_path(key):
    """The font file for 'bold', 'medium' or 'system': from the asset pack in use,
    else from the pack that ships with the repository, else '' (TouchDesigner's own face)."""
    rel = _ts().FONT_FILES.get(str(key), "")
    if not rel:
        return ""
    paths = parent().op('local/modules/paths').module  # noqa: F821
    found = paths.asset(rel)
    if found:
        return found
    shipped = paths.repo() + REPO_FONTS + rel
    return shipped if os.path.exists(shipped) else ""


def _measure(key, text):
    """Width of a text in em as TouchDesigner will draw it (kerning included)."""
    top = parent().op('m_' + key)  # noqa: F821
    if top is None:
        return 0.0
    return top.evalTextSize(text)[0] / 100.0


def onCook(scriptOp):
    c = parent()  # noqa: F821
    ts = _ts()
    fonts = {key: ts.font(font_path(key)) for key in ts.FONT_FILES}
    take = int(c.par.Take.eval())
    runs = ts.layout(ts.pick(c.par.Title.eval(), take), ts.labels(c.par.Line.eval()), take, fonts,
                     measure=_measure, margin=c.par.Margin.eval(), label_track=c.par.Tracking.eval())
    scriptOp.clear()
    for row in ts.table(runs):
        scriptOp.appendRow(row)
    return
