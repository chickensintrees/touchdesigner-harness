# Copies each take's Describe words from build.py's TAKES into preset.json ("words"), so the two cannot drift.
# Plain Python, outside TouchDesigner:  python sync_preset.py          (rewrites preset.json)
#                                       python sync_preset.py --check  (exit 1 if preset.json is out of date)
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('td', types.ModuleType('td'))      # build.py imports td; only its tables are read here
g = {'__name__': 'build'}
exec(open(os.path.join(HERE, 'build.py'), encoding='utf-8').read(), g)

path = os.path.join(HERE, 'preset.json')
preset = json.load(open(path, encoding='utf-8'))
assert len(preset['takes']) == len(g['TAKES']), 'preset.json and build.py disagree on the number of takes'
want = json.loads(json.dumps(preset))
for take, row in zip(want['takes'], g['TAKES']):
    words = [w.replace('|', ' ') for w in row.get('describe', [])]
    for w in words:
        assert all(ord(ch) < 128 for ch in w), 'non-ASCII in Describe words: ' + w
    take['words'] = words
want['accepts_input'] = True
want['as_processor'] = g['AS_PROCESSOR']

if '--check' in sys.argv:
    if want != preset:
        print('preset.json is out of date: run python sync_preset.py')
        sys.exit(1)
    print('preset.json matches build.py')
else:
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(want, f, indent=2)
        f.write('\n')
    print('wrote', path)
