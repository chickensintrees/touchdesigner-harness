# Run in a shell (not TouchDesigner): mirror the Describe words of build.py into preset.json.
#   python preset_words.py           rewrite "words" on every take, plus the Input fields
#   python preset_words.py --check   exit 1 if preset.json differs from build.py (changes nothing)
# The words are listed per take in the order a viewer meets them: what is stamped, then the
# printed sheet under the stamps (if the take has a page), then the caption along the bottom.
import json
import os
import sys
import types

here = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault("td", types.ModuleType("td"))   # build.py imports td; only its tables are read here
g = {"__name__": "build"}
exec(open(os.path.join(here, "build.py"), encoding="utf-8").read(), g)

AS_PROCESSOR = g["AS_PROCESSOR"]


def flat(s):
    return " ".join(s.replace("-\n", "-").split())   # a word broken at its hyphen is one word


def words(row):
    out = [flat(w) for w in row["describe"]]
    if not row["relic"] and row["paper"] in (0, 1):
        _, _, head, _, body = g["SHEETS"][row["form"]]
        out.append(head)
        out += [flat(line) for line in body.split("\n") if line.strip()]
    out += [flat(line) for line in row["caption"].split("\n") if line.strip()]
    return out


path = os.path.join(here, "preset.json")
preset = json.load(open(path, encoding="utf-8"))
names = [t["name"].lower().replace(" ", "") for t in preset["takes"]]
rows = g["take_rows"](g["DEFAULTS"])   # the scene's own words and shapes, not a pack's
assert names == [r["name"] for r in rows], (names, [r["name"] for r in rows])
want = json.loads(json.dumps(preset))
for t, row in zip(want["takes"], rows):
    t["words"] = words(row)
want["accepts_input"] = True
want["as_processor"] = AS_PROCESSOR
want["words_with_input"] = [g["INPUT_CAPTION"]]   # replaces each caption's second line when Input is set
for t in want["takes"]:
    for w in t["words"]:
        assert all(ord(c) < 128 for c in w), w   # straight quotes and plain hyphens only

if "--check" in sys.argv:
    if want != preset:
        print("preset.json is out of date: run python preset_words.py")
        sys.exit(1)
    print("preset.json matches build.py:", sum(len(t["words"]) for t in want["takes"]), "lines of words")
else:
    lines = ["{"]
    keys = [k for k in want if k != "takes"]
    for k in keys:
        lines.append(" %s: %s," % (json.dumps(k), json.dumps(want[k])))
    lines.append(' "takes": [')
    lines.append(",\n".join("  " + json.dumps(t) for t in want["takes"]))
    lines.append(" ]")
    lines.append("}")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("wrote", path)
