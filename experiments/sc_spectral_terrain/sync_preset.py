# Mirror the Describe words from build.py into preset.json (run outside TouchDesigner).
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent.as_posix()
sys.modules['td'] = types.ModuleType('td')
g = {'__name__': 'build'}
exec(open(HERE + '/build.py', encoding='utf-8').read(), g)
TAKES, WORDS, DWORDS = g['TAKES'], g['CONTENT']['WORDS'], g['DWORDS']
allw = WORDS + DWORDS

p = HERE + '/preset.json'
preset = json.load(open(p, encoding='utf-8'))
assert [t['name'].lower() for t in preset['takes']] == [t['name'] for t in TAKES]
for pt, t in zip(preset['takes'], TAKES):
    words = [allw[i][1] for i in (t.get('dhero') or ())]
    words += list(t.get('dlabels') or ())
    pt['words'] = words
preset['accepts_input'] = True
preset['as_processor'] = ("Lays the picture on the landscape as relief: bright areas rise and colour the ridge "
                          "lines, contours or rock, while the sound spectrum still ripples through it.")
if len(sys.argv) > 1 and sys.argv[1] == 'check':
    old = json.load(open(p, encoding='utf-8'))
    print('in sync' if old == preset else 'OUT OF SYNC')
    sys.exit(0 if old == preset else 1)
json.dump(preset, open(p, 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=True)
open(p, 'a', encoding='utf-8', newline='\n').write('\n')
for pt in preset['takes']:
    print(pt['name'], pt['words'])
