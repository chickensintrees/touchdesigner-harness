# Dev helper, run inside TouchDesigner: rebuild the scene from build.py.
#   g = {'op': op, 'td': td}; exec(open('<this file>').read(), g); r = g['r']
import traceback
_g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(td.project.folder + '/experiments/sc_rd_stamp/build.py', encoding='utf-8').read(), _g)
try:
    r = str(_g['build']())
except Exception:
    r = traceback.format_exc()
