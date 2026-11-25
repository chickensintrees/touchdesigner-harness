# Dev helper, run inside TouchDesigner after a rebuild: mirrors each take's Describe words
# (build.py TAKES 'describe', read from the live COMP's storage) into preset.json as "words",
# in the order they are used: big-word options, caption, rows of sentences, slug.
#   g = {'op': op}; exec(open('<this file>', encoding='utf-8').read(), g); r = g['r']
import json

import td

_p = td.project.folder + '/experiments/sc_riso_press/preset.json'
_takes = op('/project1/sc_riso_press').fetch('TAKES')
_d = json.load(open(_p, encoding='utf-8'))
assert len(_d['takes']) == len(_takes), 'preset.json and build.py disagree on the number of takes'
for _t, _tk in zip(_d['takes'], _takes):
    _D = _tk.get('describe') or {}
    _w = list(_D.get('big') or [])
    if _D.get('label'):
        _w.append(_D['label']['text'].replace('|', ' '))
    _w += list(_D.get('rows') or [])
    if _D.get('slug'):
        _w.append(_D['slug'].replace('%04d', '').strip())
    _t['words'] = _w
_d['accepts_input'] = True
_d['as_processor'] = ("Prints the picture as a colour separation: its red, green and blue channels become three ink plates "
                      "(dark areas take the most ink), each screened into dots, lines, rings or hatching and overprinted "
                      "out of register on paper, with each plate re-exposed on its own drum hit.")
_lines = ['{']
for _k in [k for k in _d if k != 'takes']:
    _lines.append(' %s: %s,' % (json.dumps(_k), json.dumps(_d[_k])))
_lines.append(' "takes": [')
_lines.append(',\n'.join('  ' + json.dumps(_t) for _t in _d['takes']))
_lines.append(' ]')
_lines.append('}')
open(_p, 'w', encoding='utf-8', newline='\n').write('\n'.join(_lines) + '\n')
r = [(t['name'], len(t['words'])) for t in _d['takes']]
