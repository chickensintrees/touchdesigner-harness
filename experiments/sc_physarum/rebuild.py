# Dev helper, run inside TouchDesigner: rebuild the scene from build.py.
import td
import tdh
g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(td.project.folder + '/experiments/sc_physarum/build.py', encoding='utf-8').read(), g)
g['build']()
r = str(tdh.errors('/project1/sc_physarum'))
