# Dev helper, run inside TouchDesigner: optionally rebuild, then start a trap (see trap.py).
#   g = {'op': op, 'td': td, 'absTime': absTime, 'REBUILD': True, 'SHOTS': [('05', 0, 0.3)], 'AGES': [...]}
#   exec(open(project.folder + '/experiments/sc_fluid_ink/go.py').read(), g); r = g['r']
import tdh
_here = td.project.folder + '/experiments/sc_fluid_ink/'
r = {}
if globals().get('REBUILD'):
    _g = {'op': op, 'td': td, 'absTime': absTime}
    exec(open(_here + 'rebuild.py', encoding='utf-8').read(), _g)
    r['build'] = _g['r']
_g2 = {'op': op, 'td': td, 'absTime': absTime, 'SHOTS': SHOTS, 'AGES': AGES}
exec(open(_here + 'trap.py', encoding='utf-8').read(), _g2)
r['err'] = str(tdh.errors('/project1/sc_fluid_ink'))
