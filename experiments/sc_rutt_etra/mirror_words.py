# Mirror the Describe words from build.py's TAKES into preset.json ("words" on each take) and
# check the two files agree. Plain Python, no TouchDesigner needed:
#   python experiments/sc_rutt_etra/mirror_words.py          write preset.json
#   python experiments/sc_rutt_etra/mirror_words.py --check  exit 1 if preset.json is out of date
# On screen the caption's {n} is the live line count (the take's count +-15% by seed), {sym} the
# feedback symmetry (3 to 8 by seed) and {tiles} 4, 9 or 16; here they are written as the take's
# nominal values. {src}/{page}/{osc} are written as they read with Input blank.
import io
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('td', types.ModuleType('td'))
g = {'__name__': 'mirror'}
exec(io.open(os.path.join(HERE, 'build.py'), encoding='utf-8').read(), g)

NOMINAL = dict(sym='N', tiles='4, 9 or 16', src='a 3D model', page='a page of words')


def words(take):
    row = dict(g['DEFAULT'])
    row.update(take)
    cap = take.get('label', '').format(n=int(row['lines']), **NOMINAL)
    out = [line for line in cap.split('\n') if line]
    out += [w.replace('\n', ' ') for w in take.get('words', [])]
    return out


def main():
    path = os.path.join(HERE, 'preset.json')
    preset = json.load(io.open(path, encoding='utf-8'))
    assert len(preset['takes']) == len(g['TAKES']), 'take count differs'
    want = [words(t) for t in g['TAKES']]
    if '--check' in sys.argv:
        have = [t.get('words') for t in preset['takes']]
        if have != want:
            print('preset.json words are out of date with build.py')
            return 1
        print('preset.json words match build.py')
        return 0
    for t, w in zip(preset['takes'], want):
        t['words'] = w
    lines = ['{']
    keys = [k for k in preset if k != 'takes']
    for k in keys:
        lines.append(' %s: %s,' % (json.dumps(k), json.dumps(preset[k], ensure_ascii=False)))
    lines.append(' "takes": [')
    lines.append(',\n'.join('  ' + json.dumps(t, ensure_ascii=False) for t in preset['takes']))
    lines.append(' ]')
    lines.append('}')
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('wrote', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
