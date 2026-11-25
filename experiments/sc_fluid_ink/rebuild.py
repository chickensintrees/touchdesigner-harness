# Dev helper, run inside TouchDesigner: rebuild the scene from build.py.
#   g = {'op': op, 'td': td, 'absTime': absTime}
#   exec(open(project.folder + '/experiments/sc_fluid_ink/rebuild.py').read(), g); r = g['r']
import traceback
_g = {'op': op, 'td': td, 'absTime': absTime, '__name__': 'build'}
exec(open(td.project.folder + '/experiments/sc_fluid_ink/build.py', encoding='utf-8').read(), _g)
try:
    r = str(_g['build']())
    _s = op('/project1/sc_fluid_ink')
    _s.par.Shotstart = absTime.seconds
except Exception:
    r = traceback.format_exc()
