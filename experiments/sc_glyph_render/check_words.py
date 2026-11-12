# Asserts that preset.json mirrors the Describe words in build.py, take by take (with the
# default font name filled in), and that every character of them and of the default
# phrases and poster words exists in the glyph atlases (ASCII 32..95).
# Run in a shell (not in TouchDesigner):
#   python check_words.py            check
#   python check_words.py --write    rewrite "words" in preset.json from build.py, then check
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('td', types.ModuleType('td'))      # build.py imports td; nothing here calls it
g = {'__name__': 'build_for_check'}
exec(open(os.path.join(HERE, 'build.py'), encoding='utf-8').read(), g)


def expected(t):
    """The words a take shows in Describe mode, in the order used: poster words, then the running text."""
    return [w.replace('|', ' ') for w in t['dwords']] + [g['_say'](t['describe'])]


if __name__ == '__main__':
    path = os.path.join(HERE, 'preset.json')
    preset = json.load(open(path, encoding='utf-8'))
    takes = g['TAKES']
    if '--write' in sys.argv:
        for p, t in zip(preset['takes'], takes):
            p['words'] = expected(t)
        preset['words_with_input'] = [g['_say'](g['DESCRIBE_INPUT'])]
        head = {k: v for k, v in preset.items() if k != 'takes'}
        lines = [' ' + json.dumps(k) + ': ' + json.dumps(v) + ',' for k, v in head.items()]
        lines.append(' "takes": [')
        lines += ['  ' + json.dumps(p) + (',' if i < len(preset['takes']) - 1 else '')
                  for i, p in enumerate(preset['takes'])]
        open(path, 'w', encoding='utf-8', newline='\n').write('{\n' + '\n'.join(lines) + '\n ]\n}\n')
        preset = json.load(open(path, encoding='utf-8'))
    bad = []
    if [p['name'].lower() for p in preset['takes']] != [t['name'] for t in takes]:
        bad.append('take names or order differ from build.py TAKES')
    for i, (p, t) in enumerate(zip(preset['takes'], takes)):
        if p.get('words') != expected(t):
            bad.append('take %d words differ from build.py' % i)
    if preset.get('words_with_input') != [g['_say'](g['DESCRIBE_INPUT'])]:
        bad.append('words_with_input differs from build.py DESCRIBE_INPUT')
    try:
        g['_describe_strips']()
    except RuntimeError as e:
        bad.append(str(e))
    try:
        g['_strip'](g['DEFAULTS']['PHRASES'])
    except RuntimeError as e:
        bad.append(str(e))
    for t in takes + [{'dwords': g['DEFAULTS']['POSTERS']}]:
        for w in t['dwords']:
            if any(not 32 <= ord(ch) <= 95 for ch in w.replace('|', ' ')):
                bad.append('poster word outside ASCII 32..95: %r' % w)
    if preset.get('accepts_input') is not True or not preset.get('as_processor'):
        bad.append('accepts_input / as_processor missing')
    if bad:
        print('FAIL:', bad)
        sys.exit(1)
    print('PASS: %d takes, words mirror build.py' % len(takes))
