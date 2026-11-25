# Dev helper: rebuild the scene, set a take / seed, report errors. Run inside TouchDesigner:
#   g = {'op': op, 'td': td, 'absTime': absTime, 'TAKE': 0, 'SEED': 0.1}
#   exec(open(project.folder + '/experiments/sc_kinetic_type/rebuild.py', encoding='utf-8').read(), g); r = g['r']
import time
import tdh

_t0 = time.perf_counter()
_g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(td.project.folder + '/experiments/sc_kinetic_type/build.py', encoding='utf-8').read(), _g)
_s = op(_g['build']())
_s.par.Take = globals().get('TAKE', 0)
_s.par.Seed = globals().get('SEED', 0.1)
_s.par.Shotstart = absTime.seconds
r = {'build_s': round(time.perf_counter() - _t0, 2), 'errors': str(tdh.errors(_s.path)),
     'counts': str(_s.fetch('glyph_counts', None))}
