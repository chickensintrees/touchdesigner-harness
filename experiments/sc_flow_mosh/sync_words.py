# Mirrors the Describe-mode words from build.py (DESCRIBE, the source of truth) into
# preset.json as "words" on each take, and checks they still match. Plain Python, outside
# TouchDesigner:
#   python sync_words.py           rewrite preset.json's "words" (and "words_with_input")
#   python sync_words.py --check   exit 1 if preset.json has drifted from build.py, or a default
#                                  phrase is too long for its atlas row
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def literal(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == name:
            return ast.literal_eval(node.value)
    raise KeyError(name)


def words_from_build():
    tree = ast.parse(io.open(os.path.join(HERE, "build.py"), encoding="utf-8").read())
    describe, takes = literal(tree, "DESCRIBE"), literal(tree, "TAKES")
    flat = lambda s: " ".join(s.split())
    out = []
    for row in takes:
        d = describe.get(row[0], {})
        if row[0] == "macro":            # zooms into the poster, so its big word shows in pieces
            d = dict(describe["poster"], **d)
            d.pop("label_input", None)
            d["label_input"] = describe["macro"].get("label_input")
        words = [flat(s) for s in d.get("label", ())[:2]]
        words += [flat(d[k]) for k in ("stack", "mark") if k in d]
        words += [flat(s) for s in d.get("cards", [])]
        words += [flat(s) for s in d.get("phrases", [])]
        with_input = [flat(s) for s in (d.get("label_input") or ())[:2]]
        out.append((words, with_input))
    return out


PHRASE_MAX = 38     # a 1260 px atlas row at 32 px a character (the shipped pack's phrase face at 40 px)


def too_long():
    """The default phrases that would be cut off at the end of their atlas row."""
    tree = ast.parse(io.open(os.path.join(HERE, "build.py"), encoding="utf-8").read())
    return [s for s in literal(tree, "DEFAULTS")["PHRASES"] if len(s) > PHRASE_MAX]


def main():
    path = os.path.join(HERE, "preset.json")
    preset = json.load(io.open(path, encoding="utf-8"))
    want = words_from_build()
    assert len(want) == len(preset["takes"]), "take count differs between build.py and preset.json"
    if "--check" in sys.argv:
        long = too_long()
        if long:
            print("PHRASES over %d characters: %s" % (PHRASE_MAX, long))
            return 1
        bad = [t["name"] for t, (w, wi) in zip(preset["takes"], want)
               if t.get("words") != w or t.get("words_with_input") != wi]
        print("preset.json words match build.py" if not bad else "DRIFT in takes: %s" % bad)
        return 1 if bad else 0
    for t, (w, wi) in zip(preset["takes"], want):
        t["words"] = w
        t["words_with_input"] = wi
    lines = ["{"]
    keys = [k for k in preset if k != "takes"]
    for k in keys:
        lines.append(" %s: %s," % (json.dumps(k), json.dumps(preset[k], ensure_ascii=False)))
    lines.append(' "takes": [')
    lines.append(",\n".join("  " + json.dumps(t, ensure_ascii=False) for t in preset["takes"]))
    lines.append(" ]")
    lines.append("}")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
