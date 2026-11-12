# Keeps preset.json's "words" and "words_with_input" in step with build.py (runs outside TouchDesigner):
#     python sync_preset.py          rewrite them from build.py's DESCRIBE, CAPTIONS, CAPTIONS_IN and NOUNS
#     python sync_preset.py --check  exit 1 if preset.json says something else
# The words are the scene's own defaults (DEFAULTS in build.py), not a pack's.
import json
import sys
import types
from pathlib import Path

here = Path(__file__).resolve().parent
sys.modules.setdefault("td", types.ModuleType("td"))
b = {"__name__": "build"}
exec(compile((here / "build.py").read_text(encoding="utf-8"), "build.py", "exec"), b)
describe, captions, captions_in = b["described"](b["DEFAULTS"]["NOUNS"])

path = here / "preset.json"
card = json.loads(path.read_text(encoding="utf-8"))
assert len(card["takes"]) == len(b["TAKES"]) == len(captions)
want = json.loads(json.dumps(card))
for i, take in enumerate(want["takes"]):
    take["words"] = [c.replace("\n", " ") for c in describe.get(i, [])] + captions[i].split("\n")
    take.pop("words_with_input", None)
    if i in captions_in:
        take["words_with_input"] = captions_in[i].split("\n")
    take.pop("uses_input", None)                     # re-added so that it stays the last key
    take["uses_input"] = i in captions_in
if "--check" in sys.argv:
    if want != card:
        sys.exit("preset.json is out of step with build.py: run python sync_preset.py")
    print("in step")
else:
    path.write_text(json.dumps(want, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("written")
