# Mirrors the Describe words and the Input facts from build.py into preset.json (runs outside TouchDesigner):
#   python words.py          rewrite preset.json
#   python words.py --check  exit 1 if preset.json is out of step with build.py
# build.py is the source: its TAKES rows hold 'describe' and 'inp'.
import io
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('td', types.ModuleType('td'))     # build.py imports td; nothing here calls it
g = {'__name__': 'words'}
exec(io.open(os.path.join(HERE, 'build.py'), encoding='utf-8').read(), g)

AS_PROCESSOR = ("Prints the picture as a two-colour line screen in the take's flat colours, inside the moving type "
                "and more faintly behind it, so big letters and numerals become windows onto it; the mosaic take "
                "turns it into a halftone made of letters, and rings and ticker wall also size every letter by "
                "the brightness of the picture under it.")
SCREEN = {1: "line screen of the picture inside the ink", 2: "line screen of the picture inside the big numerals",
          5: "line screen of the picture inside the front word", 6: "", 0: ""}
GLYPH = {0: "", 1: "every letter sized and coloured by the picture under it",
         2: "halftone of letters: every cell sized by the picture under it, the numeral only tinting bright cells"}


def input_note(inp):
    """One plain line saying what a take does with the Input picture, from its INPUT_USE row."""
    screen, _period, glyph, ground = inp
    parts = [SCREEN[screen]] if SCREEN[screen] else []
    if ground > 0:
        parts.append("%s %s behind the type" % ("the same screen" if parts else "line screen of the picture",
                                                 "clearly" if ground >= 0.4 else "faintly"))
    if GLYPH[glyph]:
        parts.append(GLYPH[glyph])
    return "; ".join(parts)

path = os.path.join(HERE, 'preset.json')
preset = json.load(io.open(path, encoding='utf-8'))
takes = g['TAKES']
assert [t['name'].lower() for t in preset['takes']] == [t['name'] for t in takes], 'take names or order differ'
for pt, t in zip(preset['takes'], takes):
    pt['words'] = g['describe_words'](t)
    pt['input'] = input_note(t['inp'])
preset['accepts_input'] = True
preset['as_processor'] = AS_PROCESSOR

# one take per line, like the file as first written
head = [(k, v) for k, v in preset.items() if k != 'takes']
lines = ['{']
for k, v in head:
    lines.append(' %s: %s,' % (json.dumps(k), json.dumps(v)))
lines.append(' "takes": [')
lines.append(',\n'.join('  ' + json.dumps(t) for t in preset['takes']))
lines.append(' ]')
lines.append('}')
text = '\n'.join(lines) + '\n'
json.loads(text)
if '--check' in sys.argv:
    same = io.open(path, encoding='utf-8').read() == text
    print('preset.json', 'matches build.py' if same else 'IS OUT OF STEP with build.py')
    sys.exit(0 if same else 1)
io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
print('wrote', path, len(preset['takes']), 'takes')
