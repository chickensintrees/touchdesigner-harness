# Mirrors the Describe words from build.py into preset.json, and checks they have not drifted.
# Run in the shell (not TouchDesigner):
#   python sync_preset.py            write "words" on every take, "accepts_input", "as_processor"
#   python sync_preset.py --check    exit 1 if preset.json differs from what build.py says
# build.py imports td at the top, so a stub module stands in for it here; nothing is built.
import io
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('td', types.ModuleType('td'))
g = {'__name__': 'sync_preset'}
exec(io.open(os.path.join(HERE, 'build.py'), encoding='utf-8').read(), g)

AS_PROCESSOR = ("Prints the picture on every one of 6144 instanced paper sheets (and as a two-colour print on their "
                "reverses), then flies, drops or rings them to the music; on the board take the wall of 96 x 64 "
                "sheets becomes a flip-dot display of the picture.")
# takes where a given picture is used, best first; 2 (murmuration: ink silhouettes) and 3 (ritual: no paper) ignore it
INPUT_TAKES = [1, 6, 0, 7, 4, 5]

path = os.path.join(HERE, 'preset.json')
preset = json.load(io.open(path, encoding='utf-8'))
want = json.loads(json.dumps(preset))
assert len(want['takes']) == len(g['TAKES']), 'preset.json and TAKES have different lengths'
for i, take in enumerate(want['takes']):
    assert take['name'].lower().replace(' ', '_') == g['TAKES'][i]['name'], (take['name'], g['TAKES'][i]['name'])
    take['words'] = g['describe_words'](i)
    for w in take['words']:
        assert all(ord(c) < 127 for c in w), 'plain ASCII only: %r' % w
want['accepts_input'] = True
want['as_processor'] = AS_PROCESSOR
want['input_takes'] = INPUT_TAKES

if '--check' in sys.argv:
    if want != preset:
        print('preset.json is out of date: run python sync_preset.py')
        sys.exit(1)
    print('preset.json matches build.py (%d takes, %d words)' % (len(want['takes']), sum(len(t['words']) for t in want['takes'])))
else:
    io.open(path, 'w', encoding='utf-8', newline='\n').write(json.dumps(want, indent=2) + '\n')
    print('wrote', path)
