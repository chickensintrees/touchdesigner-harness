# Text for the attractant map. The phrases themselves are build.py's DEFAULTS (or the pack's
# scenes/sc_physarum/words.json); build.py writes them to the DAT 'words_json' and every function here
# is handed that DAT's text. text(js, layout, i): layout 0 one phrase, 1 a wall of phrases, 2 a short fragment.
import json

_CACHE = {}
_WORDS = {}


def _words(js):
    if js not in _WORDS:
        _WORDS.clear()
        _WORDS[js] = json.loads(js)
    return _WORDS[js]


def text(js, layout, i):
    w = _words(js)
    phrases, fragments = w["PHRASES"], w["FRAGMENTS"]
    i = int(i)
    if layout == 1:
        n = len(phrases)
        return "  ".join(phrases[(i + k * 5) % n].replace("\n", " ") for k in range(9))
    if layout == 2:
        return fragments[i % len(fragments)]
    return phrases[i % len(phrases)]


# ---- Describe mode (2026-11-11): the words come from build.py's TAKES rows, written to the DAT 'describe_json' ----

def _rows(js):
    if js not in _CACHE:
        _CACHE.clear()
        _CACHE[js] = json.loads(js)
    return _CACHE[js]


def words(js, take, i):
    """The Describe words of a take: one entry of its list, picked like text() picks a phrase."""
    rows = _rows(js)
    w = rows[int(take) % len(rows)]["describe"]
    return w[int(i) % len(w)] if w else ""


def label(js, take):
    """The small caption a take carries in Describe mode ('' = none)."""
    rows = _rows(js)
    return rows[int(take) % len(rows)]["label"]


def inp(comp):
    """Path of the TOP named by the scene's Input parameter, or '' when blank, missing, not a TOP, or inside this scene."""
    p = comp.par.Input.eval().strip()
    if not p:
        return ""
    o = comp.op(p)
    if o is None or not o.isTOP or o.path.startswith(comp.path + "/"):
        return ""
    return o.path


# ---- stand-in sheets (2026-11-11): typed out by the Text TOP 'ssheet' when the pack has no sheet pictures ----
def sheet(js, i):
    """The text of a stand-in sheet."""
    sheets = _words(js)["STANDIN_SHEETS"]
    return sheets[int(i) % len(sheets)]
